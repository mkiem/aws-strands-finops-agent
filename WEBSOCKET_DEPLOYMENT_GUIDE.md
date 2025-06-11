# WebSocket API Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the WebSocket API for the FinOps Agent. The WebSocket API overcomes the 30-second timeout limitation of API Gateway REST APIs and enables real-time progress updates for long-running FinOps analysis.

## Prerequisites

### AWS Resources
- AWS CLI configured with appropriate permissions
- S3 bucket for deployment packages: `finops-deployment-packages-062025`
- Existing FinOps agents deployed:
  - `aws-cost-forecast-agent`
  - `trusted-advisor-agent-trusted-advisor-agent`

### Local Environment
- Python 3.11+
- Node.js 16+ (for frontend)
- Git repository access

### Required Permissions
The deploying user/role needs the following AWS permissions:
- CloudFormation: Full access
- Lambda: Full access
- API Gateway V2: Full access
- DynamoDB: Full access
- SQS: Full access
- IAM: Create/manage roles and policies
- S3: Upload to deployment bucket

## Deployment Steps

### Step 1: Prepare the Environment

```bash
# Clone the repository
git clone <repository-url>
cd finopsAgent

# Activate Python virtual environment
source .venv/bin/activate

# Navigate to WebSocket API directory
cd websocket_api
```

### Step 2: Build Lambda Deployment Packages

```bash
# Make build script executable
chmod +x build_packages.sh

# Build all Lambda packages
./build_packages.sh
```

This creates three deployment packages:
- `build/websocket-connection-manager.zip`
- `build/websocket-message-handler.zip`
- `build/websocket-background-processor.zip`

### Step 3: Upload Packages to S3

```bash
# Upload all packages to S3
cd build
aws s3 cp websocket-connection-manager.zip s3://finops-deployment-packages-062025/
aws s3 cp websocket-message-handler.zip s3://finops-deployment-packages-062025/
aws s3 cp websocket-background-processor.zip s3://finops-deployment-packages-062025/
cd ..
```

### Step 4: Deploy CloudFormation Stack

```bash
# Deploy the WebSocket API infrastructure
aws cloudformation deploy \
  --template-file cloudformation/finops-websocket-api-fixed.yaml \
  --parameter-overrides \
    ProjectName=finops-websocket \
    LambdaS3Bucket=finops-deployment-packages-062025 \
  --capabilities CAPABILITY_NAMED_IAM \
  --stack-name finops-websocket-api \
  --region us-east-1
```

### Step 5: Verify Deployment

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name finops-websocket-api \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'

# Get WebSocket API endpoint
aws cloudformation describe-stacks \
  --stack-name finops-websocket-api \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`WebSocketApiEndpoint`].OutputValue' \
  --output text
```

Expected output: `wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod`

### Step 6: Test WebSocket Connection

```bash
# Install wscat for testing
npm install -g wscat

# Test WebSocket connection
wscat -c wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod
```

In the wscat session:
```json
{"action": "authenticate", "userId": "test-user", "username": "testuser"}
```

Expected response:
```json
{"type": "authenticated", "message": "Welcome testuser! WebSocket connection established.", "userId": "test-user", "connectionId": "..."}
```

### Step 7: Update Frontend Configuration

```bash
# Navigate to frontend directory
cd ../finops-ui

# Update configuration file
cat > src/config.js << 'EOF'
const config = {
    region: 'us-east-1',
    cognito: {
        userPoolId: 'us-east-1_DQpPM15TX',
        userPoolWebClientId: '4evk2m4ru8rrenij1ukg0044k6',
        identityPoolId: 'us-east-1:dd3fed4d-d712-440a-af16-b16bf5b9c2ef',
    },
    api: {
        websocketEndpoint: 'wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod',
        privateEndpoint: 'https://bybfgjmve5b5m4baexntp62d3e0dqjty.lambda-url.us-east-1.on.aws/',
        legacyEndpoint: 'https://mdog752949.execute-api.us-east-1.amazonaws.com/prod/query',
        useWebSocket: true
    }
};
export default config;
EOF
```

### Step 8: Build and Deploy Frontend

```bash
# Build the frontend
npm run build

# Create deployment package
mkdir -p deployment-package
cp -r build/* deployment-package/
cd deployment-package
zip -r ../finops-ui-websocket-deployed.zip .
cd ..

# Upload to S3
aws s3 cp finops-ui-websocket-deployed.zip s3://finops-deployment-packages-062025/

# Deploy to Amplify
aws amplify start-deployment \
  --app-id da7jmqelobr5a \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-websocket-deployed.zip

# Clean up
rm -rf deployment-package finops-ui-websocket-deployed.zip
```

### Step 9: Verify End-to-End Functionality

1. **Access the UI**: https://staging.da7jmqelobr5a.amplifyapp.com
2. **Login**: Use test credentials (testuser / SecurePassword123!)
3. **Test WebSocket**: Submit a FinOps query and verify:
   - WebSocket connection establishes
   - Real-time progress updates appear
   - Final response displays properly

## Post-Deployment Configuration

### Enable CloudWatch Logging (Optional)

```bash
# Create CloudWatch logs role for API Gateway
aws iam create-role \
  --role-name APIGatewayCloudWatchLogsRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "apigateway.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach policy
aws iam attach-role-policy \
  --role-name APIGatewayCloudWatchLogsRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs

# Enable logging on WebSocket API
aws apigatewayv2 update-stage \
  --api-id rtswivmeqj \
  --stage-name prod \
  --default-route-settings DataTraceEnabled=true,DetailedMetricsEnabled=true,LoggingLevel=INFO
```

### Set Up Monitoring Alarms

```bash
# Create CloudWatch alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name "WebSocket-Lambda-Errors" \
  --alarm-description "WebSocket Lambda function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=finops-websocket-connection-manager \
  --evaluation-periods 1
```

## Updating the Deployment

### Lambda Function Updates

```bash
# Rebuild packages
cd websocket_api
./build_packages.sh

# Upload to S3
cd build
aws s3 cp websocket-connection-manager.zip s3://finops-deployment-packages-062025/
aws s3 cp websocket-message-handler.zip s3://finops-deployment-packages-062025/
aws s3 cp websocket-background-processor.zip s3://finops-deployment-packages-062025/
cd ..

# Update Lambda functions
aws lambda update-function-code \
  --function-name finops-websocket-connection-manager \
  --s3-bucket finops-deployment-packages-062025 \
  --s3-key websocket-connection-manager.zip

aws lambda update-function-code \
  --function-name finops-websocket-message-handler \
  --s3-bucket finops-deployment-packages-062025 \
  --s3-key websocket-message-handler.zip

aws lambda update-function-code \
  --function-name finops-websocket-background-processor \
  --s3-bucket finops-deployment-packages-062025 \
  --s3-key websocket-background-processor.zip

# Redeploy WebSocket API
aws apigatewayv2 create-deployment \
  --api-id rtswivmeqj \
  --stage-name prod \
  --description "Deploy Lambda function updates"
```

### Frontend Updates

```bash
# Build and deploy frontend updates
cd finops-ui
npm run build

mkdir -p deployment-package
cp -r build/* deployment-package/
cd deployment-package
zip -r ../finops-ui-updated.zip .
cd ..

aws s3 cp finops-ui-updated.zip s3://finops-deployment-packages-062025/

aws amplify start-deployment \
  --app-id da7jmqelobr5a \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-updated.zip

rm -rf deployment-package finops-ui-updated.zip
```

## Rollback Procedures

### Lambda Function Rollback

```bash
# List function versions
aws lambda list-versions-by-function --function-name finops-websocket-connection-manager

# Update to previous version
aws lambda update-function-configuration \
  --function-name finops-websocket-connection-manager \
  --code-sha-256 PREVIOUS_SHA256_HASH
```

### CloudFormation Stack Rollback

```bash
# Cancel update in progress
aws cloudformation cancel-update-stack --stack-name finops-websocket-api

# Or delete and redeploy with previous template
aws cloudformation delete-stack --stack-name finops-websocket-api
# Wait for deletion to complete, then redeploy with previous template
```

### Frontend Rollback

```bash
# Deploy previous version from S3
aws amplify start-deployment \
  --app-id da7jmqelobr5a \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-previous-version.zip
```

## Troubleshooting

### Common Deployment Issues

1. **CloudFormation Stack Fails**
   - Check CloudFormation events for specific errors
   - Verify S3 bucket access and object existence
   - Ensure proper IAM permissions

2. **Lambda Function Errors**
   - Check CloudWatch logs: `/aws/lambda/FUNCTION_NAME`
   - Verify environment variables are set correctly
   - Test function directly with sample events

3. **WebSocket Connection Fails**
   - Verify API Gateway deployment is current
   - Check Lambda function permissions
   - Test with wscat command-line tool

4. **Frontend Not Connecting**
   - Verify WebSocket endpoint URL in config
   - Check browser console for errors
   - Ensure Cognito authentication is working

### Health Check Commands

```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name finops-websocket-api --query 'Stacks[0].StackStatus'

# Check Lambda function status
aws lambda get-function --function-name finops-websocket-connection-manager --query 'Configuration.State'

# Check DynamoDB tables
aws dynamodb describe-table --table-name finops-websocket-connections --query 'Table.TableStatus'
aws dynamodb describe-table --table-name finops-websocket-jobs --query 'Table.TableStatus'

# Check SQS queue
aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/837882009522/finops-websocket-processing-queue --attribute-names All
```

## Security Considerations

### IAM Permissions
- Use least privilege principle for all IAM roles
- Regularly review and audit permissions
- Enable CloudTrail for API call logging

### Network Security
- WebSocket API uses WSS (secure WebSocket) protocol
- API Gateway provides built-in DDoS protection
- Consider VPC endpoints for internal access

### Data Protection
- Enable encryption at rest for DynamoDB tables
- Use AWS KMS for additional encryption layers
- Implement proper data retention policies

## Cost Optimization

### Resource Monitoring
- Monitor Lambda invocation costs
- Track DynamoDB read/write capacity usage
- Review API Gateway request charges

### Optimization Strategies
- Use DynamoDB on-demand pricing for variable workloads
- Implement connection cleanup to reduce storage costs
- Monitor and optimize Lambda memory allocation

## Maintenance

### Regular Tasks
- Review CloudWatch logs for errors
- Monitor performance metrics
- Update Lambda runtime versions
- Review and rotate IAM credentials

### Backup and Recovery
- CloudFormation templates are version controlled
- Lambda function code is stored in S3
- DynamoDB point-in-time recovery is enabled
- Regular testing of disaster recovery procedures

## Support and Documentation

### Resources
- **Main Documentation**: `WEBSOCKET_API_GUIDE.md`
- **Troubleshooting**: `troubleshooting_notes.md`
- **Architecture**: `agent_to_agent_communication_architecture.md`
- **Project Rules**: `project_rules.md`

### Getting Help
1. Check troubleshooting guide for common issues
2. Review CloudWatch logs for error details
3. Test individual components in isolation
4. Document new issues and solutions for future reference

This deployment guide ensures consistent, repeatable deployments of the WebSocket API infrastructure while maintaining security and operational best practices.
