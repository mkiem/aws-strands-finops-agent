#!/bin/bash

# AWS Trusted Advisor Agent - Lambda Package Builder
# This script builds deployment packages for the Trusted Advisor Agent

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_NAME="trusted-advisor-agent"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    rm -rf "$BUILD_DIR" "$DIST_DIR"
    mkdir -p "$BUILD_DIR" "$DIST_DIR"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command -v zip &> /dev/null; then
        print_error "zip command is required but not installed"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found in $SCRIPT_DIR"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/lambda_handler.py" ]; then
        print_error "lambda_handler.py not found in $SCRIPT_DIR"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/trusted_advisor_tools.py" ]; then
        print_error "trusted_advisor_tools.py not found in $SCRIPT_DIR"
        exit 1
    fi
}

# Build dependencies layer
build_dependencies_layer() {
    print_status "Building dependencies layer..."
    
    local deps_dir="$BUILD_DIR/python"
    mkdir -p "$deps_dir"
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt" --target "$deps_dir" --no-deps --quiet
    
    # Create dependencies ZIP
    print_status "Creating dependencies package..."
    cd "$BUILD_DIR"
    zip -r9 "$DIST_DIR/dependencies.zip" python/ > /dev/null
    cd "$SCRIPT_DIR"
    
    local deps_size=$(du -h "$DIST_DIR/dependencies.zip" | cut -f1)
    print_status "Dependencies package created: $deps_size"
}

# Build application package
build_application_package() {
    print_status "Building application package..."
    
    local app_dir="$BUILD_DIR/app"
    mkdir -p "$app_dir"
    
    # Copy application files
    print_status "Copying application files..."
    cp "$SCRIPT_DIR/lambda_handler.py" "$app_dir/"
    cp "$SCRIPT_DIR/trusted_advisor_tools.py" "$app_dir/"
    
    # Copy __init__.py if it exists
    if [ -f "$SCRIPT_DIR/__init__.py" ]; then
        cp "$SCRIPT_DIR/__init__.py" "$app_dir/"
    fi
    
    # Create application ZIP
    print_status "Creating application package..."
    cd "$app_dir"
    zip -r9 "$DIST_DIR/app.zip" . > /dev/null
    cd "$SCRIPT_DIR"
    
    local app_size=$(du -h "$DIST_DIR/app.zip" | cut -f1)
    print_status "Application package created: $app_size"
}

# Validate packages
validate_packages() {
    print_status "Validating packages..."
    
    if [ ! -f "$DIST_DIR/app.zip" ]; then
        print_error "Application package not found"
        exit 1
    fi
    
    if [ ! -f "$DIST_DIR/dependencies.zip" ]; then
        print_error "Dependencies package not found"
        exit 1
    fi
    
    # Check package sizes (Lambda limits)
    local app_size=$(stat -f%z "$DIST_DIR/app.zip" 2>/dev/null || stat -c%s "$DIST_DIR/app.zip")
    local deps_size=$(stat -f%z "$DIST_DIR/dependencies.zip" 2>/dev/null || stat -c%s "$DIST_DIR/dependencies.zip")
    
    # Lambda limits: 50MB zipped, 250MB unzipped
    local max_size=$((50 * 1024 * 1024))  # 50MB in bytes
    
    if [ "$app_size" -gt "$max_size" ]; then
        print_warning "Application package size ($app_size bytes) exceeds Lambda limit (50MB)"
    fi
    
    if [ "$deps_size" -gt "$max_size" ]; then
        print_warning "Dependencies package size ($deps_size bytes) exceeds Lambda limit (50MB)"
    fi
    
    print_status "Package validation completed"
}

# Generate deployment instructions
generate_deployment_instructions() {
    print_status "Generating deployment instructions..."
    
    cat > "$DIST_DIR/DEPLOYMENT.md" << EOF
# AWS Trusted Advisor Agent Deployment

## Package Information
- **Application Package**: app.zip
- **Dependencies Layer**: dependencies.zip
- **CloudFormation Template**: cloudformation.yaml

## Deployment Steps

### 1. Upload Packages to S3
\`\`\`bash
# Replace YOUR_DEPLOYMENT_BUCKET with your S3 bucket name
aws s3 cp app.zip s3://YOUR_DEPLOYMENT_BUCKET/trusted-advisor-agent/app.zip
aws s3 cp dependencies.zip s3://YOUR_DEPLOYMENT_BUCKET/trusted-advisor-agent/dependencies.zip
\`\`\`

### 2. Deploy CloudFormation Stack
\`\`\`bash
aws cloudformation deploy \\
  --template-file cloudformation.yaml \\
  --stack-name finops-trusted-advisor-agent \\
  --parameter-overrides \\
    DeploymentBucket=YOUR_DEPLOYMENT_BUCKET \\
    Environment=prod \\
  --capabilities CAPABILITY_NAMED_IAM \\
  --region us-east-1
\`\`\`

### 3. Test Deployment
\`\`\`bash
aws lambda invoke \\
  --function-name finops-trusted-advisor-agent-prod \\
  --payload '{"query": "Show me cost optimization recommendations"}' \\
  response.json
\`\`\`

## Environment Variables
- **REGION**: AWS region (automatically set)
- **LOG_LEVEL**: Logging level (INFO, DEBUG, WARNING, ERROR)
- **ENVIRONMENT**: Deployment environment (dev, staging, prod)
- **ENABLE_LEGACY_SUPPORT**: Enable legacy Support API fallback

## Prerequisites
- **AWS Support Plan**: Business or Enterprise support plan required for full functionality
- **Trusted Advisor Access**: Appropriate permissions for Trusted Advisor APIs
- **Bedrock Access**: Access to Amazon Bedrock for AI-powered insights

## Monitoring
- CloudWatch Logs: /aws/lambda/finops-trusted-advisor-agent-{environment}
- CloudWatch Alarms: Error rate and duration monitoring
- Dead Letter Queue: Failed invocations

## Troubleshooting
- Check CloudWatch logs for detailed error information
- Verify AWS Support plan level (Business/Enterprise required for full features)
- Ensure Trusted Advisor API permissions are correctly configured
- Verify Bedrock model access permissions
EOF

    print_status "Deployment instructions created: $DIST_DIR/DEPLOYMENT.md"
}

# Main build function
main() {
    echo
    print_status "Building AWS Trusted Advisor Agent Lambda packages..."
    echo
    
    check_prerequisites
    clean_build
    build_dependencies_layer
    build_application_package
    validate_packages
    generate_deployment_instructions
    
    echo
    print_status "Build completed successfully! 🎉"
    echo
    print_status "Packages created in: $DIST_DIR"
    print_status "- app.zip ($(du -h "$DIST_DIR/app.zip" | cut -f1))"
    print_status "- dependencies.zip ($(du -h "$DIST_DIR/dependencies.zip" | cut -f1))"
    print_status "- DEPLOYMENT.md (deployment instructions)"
    echo
    print_status "Next steps:"
    echo "  1. Upload packages to your S3 deployment bucket"
    echo "  2. Deploy using CloudFormation template"
    echo "  3. See DEPLOYMENT.md for detailed instructions"
    echo
}

# Handle script arguments
case "${1:-}" in
    clean)
        clean_build
        print_status "Build directory cleaned"
        ;;
    deps)
        check_prerequisites
        clean_build
        build_dependencies_layer
        print_status "Dependencies layer built"
        ;;
    app)
        check_prerequisites
        clean_build
        build_application_package
        print_status "Application package built"
        ;;
    *)
        main
        ;;
esac
