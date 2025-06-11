#!/bin/bash

# Build script for Trusted Advisor Agent Lambda package
# This script creates a deployment package for the Trusted Advisor Strands agent

set -e

echo "Building Trusted Advisor Agent Lambda package..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up any existing build artifacts
echo "Cleaning up existing build artifacts..."
rm -rf build/
rm -f trusted_advisor_agent_lambda.zip

# Create build directory
mkdir -p build

# Copy source files
echo "Copying source files..."
cp lambda_handler.py build/
cp trusted_advisor_tools.py build/
cp __init__.py build/

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t build/

# Create the deployment package
echo "Creating deployment package..."
cd build
zip -r ../trusted_advisor_agent_lambda.zip .
cd ..

# Clean up build directory
rm -rf build/

echo "✅ Lambda package created: trusted_advisor_agent_lambda.zip"
echo "📦 Package size: $(du -h trusted_advisor_agent_lambda.zip | cut -f1)"
echo ""
echo "Next steps:"
echo "1. Upload to S3: aws s3 cp trusted_advisor_agent_lambda.zip s3://finops-deployment-packages-062025/"
echo "2. Deploy with CloudFormation using the trusted_advisor_cf.yaml template"
