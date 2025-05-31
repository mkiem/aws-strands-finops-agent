#!/bin/bash

# Deploy AppSync API using AWS CDK

# Set environment variables
export CDK_DEFAULT_REGION=${AWS_REGION:-us-east-1}

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Navigate to infrastructure directory
cd "$(dirname "$0")"

# Bootstrap CDK (if not already done)
echo "Bootstrapping CDK..."
cdk bootstrap

# Deploy the stack
echo "Deploying AppSync stack..."
cdk deploy FinOpsAppSyncStack --require-approval never

# Get outputs
echo "Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks --stack-name FinOpsAppSyncStack --query "Stacks[0].Outputs[?OutputKey=='GraphQLAPIURL'].OutputValue" --output text)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name FinOpsAppSyncStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name FinOpsAppSyncStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text)

# Create .env file for frontend
echo "Creating .env file for frontend..."
cat > ../frontend/.env << EOL
REACT_APP_APPSYNC_URL=${API_URL}
REACT_APP_USER_POOL_ID=${USER_POOL_ID}
REACT_APP_USER_POOL_CLIENT_ID=${CLIENT_ID}
REACT_APP_AWS_REGION=${CDK_DEFAULT_REGION}
EOL

# Update Lambda environment variables
echo "Updating Lambda environment variables..."
aws lambda update-function-configuration \
  --function-name finops-supervisor-agent \
  --environment "Variables={APPSYNC_API_ID=$(echo $API_URL | cut -d'/' -f5)}"

aws lambda update-function-configuration \
  --function-name finops-cost-analysis-agent \
  --environment "Variables={APPSYNC_API_ID=$(echo $API_URL | cut -d'/' -f5)}"

aws lambda update-function-configuration \
  --function-name finops-optimization-agent \
  --environment "Variables={APPSYNC_API_ID=$(echo $API_URL | cut -d'/' -f5)}"

echo "Deployment complete!"
echo "AppSync API URL: ${API_URL}"
echo "User Pool ID: ${USER_POOL_ID}"
echo "User Pool Client ID: ${CLIENT_ID}"
