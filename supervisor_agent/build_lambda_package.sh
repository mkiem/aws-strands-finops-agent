#!/bin/bash

# FinOps Supervisor Agent - Container Build Script
# This script builds and pushes the container image for the Supervisor Agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_IMAGE_NAME="finops-supervisor-agent"
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
    echo -e "${BLUE}[BUILD]${NC} $1"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build and push FinOps Supervisor Agent container image

OPTIONS:
    -n, --name NAME         Container image name (default: $DEFAULT_IMAGE_NAME)
    -r, --region REGION     AWS region (default: $DEFAULT_REGION)
    -t, --tag TAG           Image tag (default: latest)
    --build-only           Only build image, don't push to ECR
    --push-only            Only push to ECR (skip building)
    --platform PLATFORM    Target platform (default: linux/amd64)
    -h, --help             Show this help message

EXAMPLES:
    $0                                    # Build and push with defaults
    $0 --name my-supervisor --tag v1.0   # Custom name and tag
    $0 --build-only                      # Build only, don't push
    $0 --region us-west-2                # Use different region

PREREQUISITES:
    - Docker installed and running
    - AWS CLI configured with ECR permissions
    - Dockerfile present in current directory
EOF
}

# Parse command line arguments
parse_arguments() {
    IMAGE_NAME="$DEFAULT_IMAGE_NAME"
    AWS_REGION="$DEFAULT_REGION"
    IMAGE_TAG="latest"
    BUILD_ONLY=false
    PUSH_ONLY=false
    PLATFORM="linux/amd64"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --push-only)
                PUSH_ONLY=true
                shift
                ;;
            --platform)
                PLATFORM="$2"
                shift 2
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
    
    # Validate image name
    if [[ ! "$IMAGE_NAME" =~ ^[a-z0-9]+(?:[._-][a-z0-9]+)*$ ]]; then
        print_error "Invalid image name. Must match ECR repository naming rules."
        exit 1
    fi
    
    # Validate tag
    if [[ ! "$IMAGE_TAG" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        print_error "Invalid image tag. Must contain only alphanumeric characters, periods, underscores, and hyphens."
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
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
    
    # Check Dockerfile
    if [ ! -f "$SCRIPT_DIR/Dockerfile" ]; then
        print_error "Dockerfile not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Check required Python files
    local required_files=("lambda_handler.py" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$file" ]; then
            print_error "Required file not found: $file"
            exit 1
        fi
    done
    
    print_status "Prerequisites check passed"
}

# Get AWS account ID
get_aws_account_id() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "Failed to get AWS account ID"
        exit 1
    fi
    print_status "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Build Docker image
build_image() {
    if [ "$PUSH_ONLY" = true ]; then
        print_status "Skipping build (push-only mode)"
        return
    fi
    
    print_header "Building container image..."
    
    local full_image_name="${IMAGE_NAME}:${IMAGE_TAG}"
    
    print_status "Building image: $full_image_name"
    print_status "Platform: $PLATFORM"
    print_status "Context: $SCRIPT_DIR"
    
    # Build the Docker image
    cd "$SCRIPT_DIR"
    docker buildx build \
        --platform "$PLATFORM" \
        --provenance=false \
        --load \
        -t "$full_image_name" \
        .
    
    print_status "Image built successfully: $full_image_name"
    
    # Show image size
    local image_size=$(docker images --format "table {{.Size}}" "$full_image_name" | tail -n 1)
    print_status "Image size: $image_size"
}

# Create ECR repository
create_ecr_repository() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_status "Creating/updating ECR repository..."
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region "$AWS_REGION" &> /dev/null; then
        print_status "ECR repository '$IMAGE_NAME' already exists"
    else
        print_status "Creating ECR repository: $IMAGE_NAME"
        aws ecr create-repository \
            --repository-name "$IMAGE_NAME" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true \
            --image-tag-mutability MUTABLE \
            --tags Key=Project,Value=FinOpsAgent Key=Component,Value=SupervisorAgent
    fi
}

# Authenticate with ECR
authenticate_ecr() {
    if [ "$BUILD_ONLY" = true ]; then
        return
    fi
    
    print_status "Authenticating with Amazon ECR..."
    
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    print_status "ECR authentication successful"
}

# Push image to ECR
push_image() {
    if [ "$BUILD_ONLY" = true ]; then
        print_status "Skipping push (build-only mode)"
        return
    fi
    
    print_header "Pushing image to ECR..."
    
    local local_image="${IMAGE_NAME}:${IMAGE_TAG}"
    local ecr_image="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Tag image for ECR
    print_status "Tagging image for ECR..."
    docker tag "$local_image" "$ecr_image"
    
    # Push image
    print_status "Pushing image to ECR..."
    docker push "$ecr_image"
    
    print_status "Image pushed successfully: $ecr_image"
    
    # Get image digest
    local image_digest=$(aws ecr describe-images \
        --repository-name "$IMAGE_NAME" \
        --image-ids imageTag="$IMAGE_TAG" \
        --region "$AWS_REGION" \
        --query 'imageDetails[0].imageDigest' \
        --output text 2>/dev/null || echo "unknown")
    
    if [ "$image_digest" != "unknown" ]; then
        print_status "Image digest: $image_digest"
    fi
}

# Generate deployment instructions
generate_deployment_instructions() {
    print_header "Generating deployment instructions..."
    
    local ecr_image="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
    
    cat > "$SCRIPT_DIR/DEPLOYMENT.md" << EOF
# FinOps Supervisor Agent Deployment

## Container Image Information
- **ECR Repository**: $IMAGE_NAME
- **Image Tag**: $IMAGE_TAG
- **Full Image URI**: $ecr_image
- **Region**: $AWS_REGION

## Deployment Steps

### 1. Deploy CloudFormation Stack
\`\`\`bash
aws cloudformation deploy \\
  --template-file cloudformation.yaml \\
  --stack-name finops-supervisor-agent-prod \\
  --parameter-overrides \\
    ECRRepository=$IMAGE_NAME \\
    ImageTag=$IMAGE_TAG \\
    Environment=prod \\
  --capabilities CAPABILITY_NAMED_IAM \\
  --region $AWS_REGION
\`\`\`

### 2. Test Deployment
\`\`\`bash
# Get Function URL from stack outputs
FUNCTION_URL=\$(aws cloudformation describe-stacks \\
  --stack-name finops-supervisor-agent-prod \\
  --region $AWS_REGION \\
  --query 'Stacks[0].Outputs[?OutputKey==\`SupervisorAgentFunctionUrl\`].OutputValue' \\
  --output text)

# Test the function
curl -X POST "\$FUNCTION_URL" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "What is my current AWS spend?"}'
\`\`\`

### 3. Monitor Deployment
\`\`\`bash
# View logs
aws logs tail /aws/lambda/finops-supervisor-agent-prod --follow --region $AWS_REGION

# Check CloudWatch alarms
aws cloudwatch describe-alarms \\
  --alarm-names finops-supervisor-agent-errors-prod \\
  --region $AWS_REGION
\`\`\`

## Configuration Options

### CloudFormation Parameters
- **ECRRepository**: ECR repository name (default: finops-supervisor-agent)
- **ImageTag**: Container image tag (default: latest)
- **Environment**: Deployment environment (dev/staging/prod)
- **LambdaTimeout**: Function timeout in seconds (30-900)
- **LambdaMemorySize**: Memory allocation in MB (128-10240)
- **ProvisionedConcurrency**: Number of provisioned executions (0 to disable)
- **CorsOrigins**: Comma-delimited list of allowed CORS origins

### Environment Variables
- **POWERTOOLS_SERVICE_NAME**: Service name for observability
- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **ENVIRONMENT**: Deployment environment

## Updating the Image

### 1. Build and Push New Image
\`\`\`bash
./build_lambda_package.sh --tag v2.0
\`\`\`

### 2. Update Lambda Function
\`\`\`bash
aws lambda update-function-code \\
  --function-name finops-supervisor-agent-prod \\
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:v2.0 \\
  --region $AWS_REGION
\`\`\`

## Troubleshooting

### Common Issues
1. **ECR Authentication**: Ensure AWS CLI has ECR permissions
2. **Image Size**: Lambda container images must be < 10GB
3. **Platform**: Ensure image is built for linux/amd64
4. **Permissions**: Lambda role needs permissions to invoke other agents

### Debug Commands
\`\`\`bash
# Check ECR repository
aws ecr describe-repositories --repository-names $IMAGE_NAME --region $AWS_REGION

# List images
aws ecr list-images --repository-name $IMAGE_NAME --region $AWS_REGION

# Test locally
docker run --rm -p 9000:8080 $IMAGE_NAME:$IMAGE_TAG
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \\
  -d '{"query": "test"}'
\`\`\`
EOF

    print_status "Deployment instructions created: $SCRIPT_DIR/DEPLOYMENT.md"
}

# Main build function
main() {
    echo
    print_header "FinOps Supervisor Agent Container Build"
    echo
    
    parse_arguments "$@"
    check_prerequisites
    get_aws_account_id
    build_image
    create_ecr_repository
    authenticate_ecr
    push_image
    generate_deployment_instructions
    
    echo
    print_status "Build completed successfully! 🎉"
    echo
    
    if [ "$BUILD_ONLY" = false ]; then
        local ecr_image="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
        print_status "Container image: $ecr_image"
        echo
        print_status "Next steps:"
        echo "  1. Deploy using CloudFormation template"
        echo "  2. Test the deployment"
        echo "  3. See DEPLOYMENT.md for detailed instructions"
    else
        print_status "Image built locally: ${IMAGE_NAME}:${IMAGE_TAG}"
        echo
        print_status "To push to ECR, run:"
        echo "  $0 --push-only --name $IMAGE_NAME --tag $IMAGE_TAG --region $AWS_REGION"
    fi
    echo
}

# Run main function with all arguments
main "$@"
