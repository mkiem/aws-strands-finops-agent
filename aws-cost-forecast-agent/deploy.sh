#!/bin/bash

# AWS Cost Forecast Agent - Deployment Script
# This script automates the deployment of the Cost Forecast Agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME="aws-cost-forecast-agent"
STACK_NAME="finops-cost-forecast-agent"
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

Deploy AWS Cost Forecast Agent to AWS Lambda

OPTIONS:
    -b, --bucket BUCKET     S3 deployment bucket (required)
    -r, --region REGION     AWS region (default: $DEFAULT_REGION)
    -e, --env ENVIRONMENT   Environment (dev|staging|prod, default: prod)
    -s, --stack STACK       CloudFormation stack name (default: $STACK_NAME)
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
EOF
}

# Parse command line arguments
parse_arguments() {
    DEPLOYMENT_BUCKET=""
    AWS_REGION="$DEFAULT_REGION"
    ENVIRONMENT="prod"
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
    
    aws cloudformation deploy \
        --template-file "$SCRIPT_DIR/cloudformation.yaml" \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            DeploymentBucket="$DEPLOYMENT_BUCKET" \
            AppS3Key="$s3_prefix/app.zip" \
            DependenciesS3Key="$s3_prefix/dependencies.zip" \
            Environment="$ENVIRONMENT" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --tags \
            Project=FinOpsAgent \
            Component=CostForecastAgent \
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
    
    local function_name="finops-cost-forecast-agent-$ENVIRONMENT"
    
    print_status "Testing Lambda function: $function_name"
    
    # Create test payload
    local test_payload='{"query": "What is my current AWS spend?"}'
    
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

# Main deployment function
main() {
    echo
    print_header "AWS Cost Forecast Agent Deployment"
    echo
    
    parse_arguments "$@"
    check_prerequisites
    build_packages
    upload_packages
    deploy_stack
    get_stack_outputs
    test_deployment
    
    echo
    print_status "Deployment completed successfully! 🎉"
    echo
    print_status "Stack Name: $STACK_NAME"
    print_status "Region: $AWS_REGION"
    print_status "Environment: $ENVIRONMENT"
    echo
    print_status "Next steps:"
    echo "  - Check CloudWatch logs: /aws/lambda/finops-cost-forecast-agent-$ENVIRONMENT"
    echo "  - Monitor CloudWatch alarms for errors and performance"
    echo "  - Test the agent with various cost analysis queries"
    echo
}

# Run main function with all arguments
main "$@"
