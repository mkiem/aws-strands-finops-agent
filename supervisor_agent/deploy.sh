#!/bin/bash

# FinOps Supervisor Agent - Deployment Script
# This script automates the complete deployment of the Supervisor Agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME="finops-supervisor-agent"
STACK_NAME="finops-supervisor-agent"
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

Deploy FinOps Supervisor Agent to AWS Lambda

OPTIONS:
    -n, --name NAME         ECR repository name (default: $AGENT_NAME)
    -r, --region REGION     AWS region (default: $DEFAULT_REGION)
    -e, --env ENVIRONMENT   Environment (dev|staging|prod, default: prod)
    -s, --stack STACK       CloudFormation stack name (default: $STACK_NAME)
    -t, --tag TAG           Container image tag (default: latest)
    --cors-origins ORIGINS  Comma-delimited CORS origins (default: localhost)
    --memory SIZE           Lambda memory in MB (default: 1024)
    --timeout SECONDS       Lambda timeout in seconds (default: 300)
    --concurrency COUNT     Provisioned concurrency (default: 2, 0 to disable)
    --build-only           Only build container, don't deploy
    --deploy-only          Only deploy (skip building)
    --no-api-gateway       Disable API Gateway (use Function URL only)
    -h, --help             Show this help message

EXAMPLES:
    $0                                          # Deploy with defaults
    $0 --env staging --region us-west-2        # Deploy to staging
    $0 --build-only                            # Build container only
    $0 --deploy-only --tag v1.0               # Deploy existing image
    $0 --cors-origins "https://myapp.com,https://staging.myapp.com"

PREREQUISITES:
    - AWS CLI configured with appropriate permissions
    - Docker installed and running
    - CloudFormation template present
EOF
}

# Parse command line arguments
parse_arguments() {
    ECR_REPOSITORY="$AGENT_NAME"
    AWS_REGION="$DEFAULT_REGION"
    ENVIRONMENT="prod"
    IMAGE_TAG="latest"
    CORS_ORIGINS="http://localhost:3000,https://localhost:3000"
    LAMBDA_MEMORY="1024"
    LAMBDA_TIMEOUT="300"
    PROVISIONED_CONCURRENCY="2"
    BUILD_ONLY=false
    DEPLOY_ONLY=false
    ENABLE_API_GATEWAY="true"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                ECR_REPOSITORY="$2"
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
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --cors-origins)
                CORS_ORIGINS="$2"
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
            --concurrency)
                PROVISIONED_CONCURRENCY="$2"
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
            --no-api-gateway)
                ENABLE_API_GATEWAY="false"
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
    
    if ! [[ "$PROVISIONED_CONCURRENCY" =~ ^[0-9]+$ ]] || [ "$PROVISIONED_CONCURRENCY" -lt 0 ] || [ "$PROVISIONED_CONCURRENCY" -gt 100 ]; then
        print_error "Provisioned concurrency must be between 0 and 100"
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
    
    # Check Docker (only if building)
    if [ "$DEPLOY_ONLY" = false ]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker is required for building but not installed"
            exit 1
        fi
        
        if ! docker info &> /dev/null; then
            print_error "Docker is not running. Please start Docker and try again."
            exit 1
        fi
    fi
    
    # Check CloudFormation template
    if [ "$BUILD_ONLY" = false ] && [ ! -f "$SCRIPT_DIR/cloudformation.yaml" ]; then
        print_error "CloudFormation template not found: $SCRIPT_DIR/cloudformation.yaml"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Build container image
build_container() {
    if [ "$DEPLOY_ONLY" = true ]; then
        print_status "Skipping build (deploy-only mode)"
        return
    fi
    
    print_header "Building container image..."
    
    if [ ! -f "$SCRIPT_DIR/build_lambda_package.sh" ]; then
        print_error "Build script not found: $SCRIPT_DIR/build_lambda_package.sh"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
    ./build_lambda_package.sh \
        --name "$ECR_REPOSITORY" \
        --region "$AWS_REGION" \
        --tag "$IMAGE_TAG"
    
    print_status "Container image built and pushed successfully"
}

# Deploy CloudFormation stack
deploy_stack() {
    if [ "$BUILD_ONLY" = true ]; then
        print_status "Skipping deployment (build-only mode)"
        return
    fi
    
    print_header "Deploying CloudFormation stack..."
    
    print_status "Stack Name: $STACK_NAME"
    print_status "Region: $AWS_REGION"
    print_status "Environment: $ENVIRONMENT"
    print_status "ECR Repository: $ECR_REPOSITORY"
    print_status "Image Tag: $IMAGE_TAG"
    
    aws cloudformation deploy \
        --template-file "$SCRIPT_DIR/cloudformation.yaml" \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            ECRRepository="$ECR_REPOSITORY" \
            ImageTag="$IMAGE_TAG" \
            Environment="$ENVIRONMENT" \
            LambdaMemorySize="$LAMBDA_MEMORY" \
            LambdaTimeout="$LAMBDA_TIMEOUT" \
            ProvisionedConcurrency="$PROVISIONED_CONCURRENCY" \
            CorsOrigins="$CORS_ORIGINS" \
            EnableApiGateway="$ENABLE_API_GATEWAY" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --tags \
            Project=FinOpsAgent \
            Component=SupervisorAgent \
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
        echo
        
        # Extract Function URL for testing
        FUNCTION_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`SupervisorAgentFunctionUrl`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$FUNCTION_URL" ]; then
            print_status "Function URL: $FUNCTION_URL"
        fi
    else
        print_warning "No stack outputs available"
    fi
}

# Test deployment
test_deployment() {
    if [ "$BUILD_ONLY" = true ] || [ -z "$FUNCTION_URL" ]; then
        return
    fi
    
    print_header "Testing deployment..."
    
    print_status "Testing Supervisor Agent function..."
    
    # Create test payload
    local test_payload='{"query": "What is my current AWS spend?"}'
    
    # Test the function
    print_status "Sending test request to: $FUNCTION_URL"
    
    local response_file=$(mktemp)
    local http_code=$(curl -s -w "%{http_code}" \
        -X POST "$FUNCTION_URL" \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        -o "$response_file")
    
    if [ "$http_code" = "200" ]; then
        print_status "Function test successful (HTTP $http_code)"
        print_status "Response preview: $(head -c 200 "$response_file")..."
    else
        print_warning "Function test returned HTTP $http_code"
        print_warning "Response: $(cat "$response_file")"
    fi
    
    rm -f "$response_file"
}

# Monitor deployment
monitor_deployment() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_header "Monitoring Information"
    
    local function_name="finops-supervisor-agent-$ENVIRONMENT"
    local log_group="/aws/lambda/$function_name"
    
    print_status "CloudWatch Logs: $log_group"
    print_status "Monitor with: aws logs tail $log_group --follow --region $AWS_REGION"
    
    # Check if there are any recent errors
    print_status "Checking for recent errors..."
    local recent_errors=$(aws logs filter-log-events \
        --log-group-name "$log_group" \
        --start-time $(($(date +%s) - 300))000 \
        --filter-pattern "ERROR" \
        --region "$AWS_REGION" \
        --query 'events[].message' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$recent_errors" ] && [ "$recent_errors" != "None" ]; then
        print_warning "Recent errors found in logs:"
        echo "$recent_errors"
    else
        print_status "No recent errors found in logs"
    fi
}

# Main deployment function
main() {
    echo
    print_header "FinOps Supervisor Agent Deployment"
    echo
    
    parse_arguments "$@"
    check_prerequisites
    build_container
    deploy_stack
    get_stack_outputs
    test_deployment
    monitor_deployment
    
    echo
    print_status "Deployment completed successfully! 🎉"
    echo
    print_status "Stack Name: $STACK_NAME"
    print_status "Region: $AWS_REGION"
    print_status "Environment: $ENVIRONMENT"
    
    if [ -n "$FUNCTION_URL" ]; then
        echo
        print_status "Function URL: $FUNCTION_URL"
        echo
        print_status "Test with:"
        echo "  curl -X POST \"$FUNCTION_URL\" \\"
        echo "    -H \"Content-Type: application/json\" \\"
        echo "    -d '{\"query\": \"What is my current AWS spend?\"}'"
    fi
    
    echo
    print_status "Next steps:"
    echo "  - Monitor CloudWatch logs for any issues"
    echo "  - Test with various FinOps queries"
    echo "  - Configure frontend to use the Function URL"
    echo "  - Set up monitoring and alerting"
    echo
}

# Run main function with all arguments
main "$@"
