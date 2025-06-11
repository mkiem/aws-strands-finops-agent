#!/bin/bash

# Exit on error
set -e

echo "Building AWS FinOps Supervisor Agent container image..."

# Configuration
IMAGE_NAME="aws-finops-agent"
ECR_REPO="finops-deployment-packages-062025"
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Build the Docker image
echo "Building Docker image..."
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  -t ${IMAGE_NAME}:latest .

# Get ECR login token
echo "Authenticating with Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Create ECR repository if it doesn't exist
echo "Creating/updating ECR repository..."
aws ecr create-repository \
  --repository-name ${IMAGE_NAME} \
  --region ${AWS_REGION} \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability MUTABLE \
  2>/dev/null || true

# Tag and push image
echo "Tagging and pushing image to ECR..."
docker tag ${IMAGE_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest

echo "✅ Container image built and pushed to ECR:"
echo "   ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest"
echo ""
echo "Next steps:"
echo "1. Deploy using CloudFormation:"
echo "   aws cloudformation deploy \\"
echo "     --template-file aws_finops_agent_cf.yaml \\"
echo "     --stack-name aws-finops-supervisor-agent \\"
echo "     --capabilities CAPABILITY_NAMED_IAM"
