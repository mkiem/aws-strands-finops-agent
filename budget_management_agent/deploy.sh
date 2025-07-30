#!/bin/bash

# AWS Budget Management Agent - Deployment Script
# This script automates the deployment of the Budget Management Agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME="budget-management-agent"
STACK_NAME="finops-budget-management-agent"
DEFAULT_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy AWS Budget Management Agent to AWS Lambda

OPTIONS:
    -b, --bucket BUCKET     S3 deployment bucket (required)
    -r, --region REGION     AWS region (default: $DEFAULT_REGION)
    -e, --env ENVIRONMENT   Environment (dev|staging|prod, default: prod)
    -s, --stack STACK       CloudFormation stack name (default: $STACK_NAME)
    --memory SIZE           Lambda memory in MB (default: 1024)
    --timeout SECONDS       Lambda timeout in seconds (default: 300)
    --no-budget-actions     Disable automated budget actions
    --build-only           Only build packages, don't deploy
    --deploy-only          Only deploy (skip building)
    -h, --help             Show this help message

EXAMPLES:
    $0 --bucket my-deployment-bucket
    $0 --bucket my-bucket --region us-west-2 --env staging
    $0 --bucket my-bucket --build-only

PREREQUISITES:
    - AWS CLI configured with appropriate permissions
    - Python 3.11+ installed
    - S3 bucket for deployment artifacts
    - AWS Budgets API access
EOF
}

# Parse command line arguments
parse_arguments() {
    DEPLOYMENT_BUCKET=""
    AWS_REGION="$DEFAULT_REGION"
    ENVIRONMENT="prod"
    LAMBDA_MEMORY="1024"
    LAMBDA_TIMEOUT="300"
    ENABLE_BUDGET_ACTIONS="true"
    BUILD_ONLY=false
    DEPLOY_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--bucket)
                DEPLOYMENT_BUCKET="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--stack)
                STACK_NAME="$2"
                shift 2
                ;;
            --memory)
                LAMBDA_MEMORY="$2"
                shift 2
                ;;
            --timeout)
                LAMBDA_TIMEOUT="$2"
                shift 2
                ;;
            --no-budget-actions)
                ENABLE_BUDGET_ACTIONS="false"
                shift
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --deploy-only)
                DEPLOY_ONLY=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required parameters
    if [ -z "$DEPLOYMENT_BUCKET" ]; then
        print_error "Deployment bucket is required. Use --bucket option."
        show_usage
        exit 1
    fi
    
    # Validate environment
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        print_error "Environment must be one of: dev, staging, prod"
        exit 1
    fi
    
    # Update stack name with environment
    STACK_NAME="$STACK_NAME-$ENVIRONMENT"
    
    # Validate numeric parameters
    if ! [[ "$LAMBDA_MEMORY" =~ ^[0-9]+$ ]] || [ "$LAMBDA_MEMORY" -lt 128 ] || [ "$LAMBDA_MEMORY" -gt 10240 ]; then
        print_error "Lambda memory must be between 128 and 10240 MB"
        exit 1
    fi
    
    if ! [[ "$LAMBDA_TIMEOUT" =~ ^[0-9]+$ ]] || [ "$LAMBDA_TIMEOUT" -lt 30 ] || [ "$LAMBDA_TIMEOUT" -gt 900 ]; then
        print_error "Lambda timeout must be between 30 and 900 seconds"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is required but not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check if bucket exists
    if ! aws s3 ls "s3://$DEPLOYMENT_BUCKET" &> /dev/null; then
        print_error "S3 bucket '$DEPLOYMENT_BUCKET' does not exist or is not accessible"
        exit 1
    fi
    
    # Check AWS Budgets access
    if ! aws budgets describe-budgets --account-id "$(aws sts get-caller-identity --query Account --output text)" --region "$AWS_REGION" > /dev/null 2>&1; then
        print_warning "AWS Budgets API access may be limited. Some features may not work."
    fi
    
    print_status "Prerequisites check passed"
}

# Build packages
build_packages() {
    if [ "$DEPLOY_ONLY" = true ]; then
        print_status "Skipping build (deploy-only mode)"
        return
    fi
    
    print_header "Building Lambda packages..."
    
    if [ ! -f "$SCRIPT_DIR/build_lambda_package.sh" ]; then
        print_error "Build script not found: $SCRIPT_DIR/build_lambda_package.sh"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
    ./build_lambda_package.sh
    
    print_status "Packages built successfully"
}

# Upload packages to S3
upload_packages() {
    if [ "$BUILD_ONLY" = true ]; then
        print_status "Skipping upload (build-only mode)"
        return
    fi
    
    print_header "Uploading packages to S3..."
    
    local s3_prefix="$AGENT_NAME"
    
    # Upload application package
    print_status "Uploading application package..."
    aws s3 cp "$SCRIPT_DIR/dist/app.zip" "s3://$DEPLOYMENT_BUCKET/$s3_prefix/app.zip" \
        --region "$AWS_REGION"
    
    # Upload dependencies layer
    print_status "Uploading dependencies layer..."
    aws s3 cp "$SCRIPT_DIR/dist/dependencies.zip" "s3://$DEPLOYMENT_BUCKET/$s3_prefix/dependencies.zip" \
        --region "$AWS_REGION"
    
    print_status "Packages uploaded successfully"
}

# Deploy CloudFormation stack
deploy_stack() {
    if [ "$BUILD_ONLY" = true ]; then
        print_status "Skipping deployment (build-only mode)"
        return
    fi
    
    print_header "Deploying CloudFormation stack..."
    
    if [ ! -f "$SCRIPT_DIR/cloudformation.yaml" ]; then
        print_error "CloudFormation template not found: $SCRIPT_DIR/cloudformation.yaml"
        exit 1
    fi
    
    local s3_prefix="$AGENT_NAME"
    
    print_status "Deploying stack: $STACK_NAME"
    print_status "Region: $AWS_REGION"
    print_status "Environment: $ENVIRONMENT"
    print_status "Budget Actions: $ENABLE_BUDGET_ACTIONS"
    
    aws cloudformation deploy \
        --template-file "$SCRIPT_DIR/cloudformation.yaml" \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            DeploymentBucket="$DEPLOYMENT_BUCKET" \
            AppS3Key="$s3_prefix/app.zip" \
            DependenciesS3Key="$s3_prefix/dependencies.zip" \
            Environment="$ENVIRONMENT" \
            LambdaMemorySize="$LAMBDA_MEMORY" \
            LambdaTimeout="$LAMBDA_TIMEOUT" \
            EnableBudgetActions="$ENABLE_BUDGET_ACTIONS" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --tags \
            Project=FinOpsAgent \
            Component=BudgetManagementAgent \
            Environment="$ENVIRONMENT"
    
    print_status "Stack deployed successfully"
}

# Get stack outputs
get_stack_outputs() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_header "Deployment Information"
    
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output table 2>/dev/null || echo "[]")
    
    if [ "$outputs" != "[]" ]; then
        echo "$outputs"
    else
        print_warning "No stack outputs available"
    fi
}

# Test deployment
test_deployment() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_header "Testing deployment..."
    
    local function_name="finops-budget-management-agent-$ENVIRONMENT"
    
    print_status "Testing Lambda function: $function_name"
    
    # Create test payload
    local test_payload='{"query": "Show me my budget performance"}'
    
    # Invoke function
    local response_file=$(mktemp)
    if aws lambda invoke \
        --function-name "$function_name" \
        --payload "$test_payload" \
        --region "$AWS_REGION" \
        "$response_file" > /dev/null 2>&1; then
        
        print_status "Function invocation successful"
        print_status "Response: $(cat "$response_file")"
        rm -f "$response_file"
    else
        print_warning "Function test failed. Check CloudWatch logs for details."
        rm -f "$response_file"
    fi
}

# Check budget access and setup
check_budget_access() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_header "Checking budget access and setup..."
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    
    # Test budget access
    print_status "Testing AWS Budgets API access..."
    if aws budgets describe-budgets --account-id "$account_id" --region "$AWS_REGION" > /dev/null 2>&1; then
        print_status "AWS Budgets API access: ✓"
        
        # Count existing budgets
        local budget_count=$(aws budgets describe-budgets \
            --account-id "$account_id" \
            --region "$AWS_REGION" \
            --query 'length(Budgets)' \
            --output text 2>/dev/null || echo "0")
        
        print_status "Existing budgets: $budget_count"
        
        if [ "$budget_count" -eq 0 ]; then
            print_warning "No budgets found. Consider creating budgets for the agent to manage."
        fi
    else
        print_warning "AWS Budgets API access: ✗"
        print_warning "The agent may have limited functionality without budget access."
    fi
    
    # Check DynamoDB table
    local table_name="finops-budget-state-$ENVIRONMENT"
    if aws dynamodb describe-table --table-name "$table_name" --region "$AWS_REGION" > /dev/null 2>&1; then
        print_status "DynamoDB state table: ✓"
    else
        print_warning "DynamoDB state table: ✗"
    fi
}

# Main deployment function
main() {
    echo
    print_header "AWS Budget Management Agent Deployment"
    echo
    
    parse_arguments "$@"
    check_prerequisites
    build_packages
    upload_packages
    deploy_stack
    get_stack_outputs
    test_deployment
    check_budget_access
    
    echo
    print_status "Deployment completed successfully! 🎉"
    echo
    print_status "Stack Name: $STACK_NAME"
    print_status "Region: $AWS_REGION"
    print_status "Environment: $ENVIRONMENT"
    echo
    print_status "Next steps:"
    echo "  - Check CloudWatch logs: /aws/lambda/finops-budget-management-agent-$ENVIRONMENT"
    echo "  - Monitor CloudWatch alarms for errors and performance"
    echo "  - Test the agent with budget management queries"
    echo "  - Create budgets if none exist for the agent to manage"
    echo
}

# Run main function with all arguments
main "$@"
