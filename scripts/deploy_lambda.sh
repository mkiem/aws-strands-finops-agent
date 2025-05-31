#!/bin/bash

# Script to deploy the FinOps Agent Lambda functions

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies for Lambda functions
echo "Installing Lambda dependencies..."
pip install -r src/lambda/requirements.txt -t src/lambda/supervisor_agent/
pip install -r src/lambda/requirements.txt -t src/lambda/cost_analysis_agent/
pip install -r src/lambda/requirements.txt -t src/lambda/cost_optimization_agent/

# Install CDK dependencies
echo "Installing CDK dependencies..."
pip install -r cdk/requirements.txt

# Change to the CDK directory
cd cdk

# Deploy the CDK stack
echo "Deploying CDK stack..."
cdk deploy --require-approval never

echo "Deployment completed successfully!"
