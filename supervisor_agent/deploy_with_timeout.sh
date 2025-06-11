#!/bin/bash

# Deploy AWS FinOps Supervisor Agent with updated timeout
set -e

echo "Building and deploying AWS FinOps Supervisor Agent with 5-minute timeout..."

# Build the container image
echo "Building container image..."
./build_lambda_package.sh

# Deploy using CloudFormation with updated timeout
echo "Deploying CloudFormation stack with 5-minute timeout..."
aws cloudformation deploy \
  --template-file aws_finops_agent_cf.yaml \
  --stack-name aws-finops-supervisor-agent \
  --parameter-overrides \
    LambdaTimeout=300 \
    LambdaMemorySize=256 \
  --capabilities CAPABILITY_NAMED_IAM

echo "Deployment completed successfully!"

# Get the API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name aws-finops-supervisor-agent \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_ENDPOINT"

# Test the deployment
echo "Testing deployment with a simple query..."
curl -X POST \
  "$API_ENDPOINT" \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are my current AWS costs?"}' \
  | jq '.'

echo "Deployment and testing completed!"
