#!/bin/bash

# Exit on error
set -e

echo "Building Lambda deployment package..."

# Create a temporary directory for the package
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Install dependencies to the temporary directory
echo "Installing dependencies..."
pip install -r requirements.txt --target $TEMP_DIR

# Copy the Lambda handler to the package
echo "Copying Lambda handler..."
cp lambda_handler.py $TEMP_DIR/

# Create the deployment package
echo "Creating deployment package..."
cd $TEMP_DIR
zip -r9 ../finops_agent_lambda.zip .
cd -

# Clean up
echo "Cleaning up..."
rm -rf $TEMP_DIR

echo "Deployment package created: finops_agent_lambda.zip"
