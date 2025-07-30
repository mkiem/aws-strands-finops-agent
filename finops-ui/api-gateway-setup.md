# API Gateway Setup for FinOps Agent

This document provides instructions for setting up an API Gateway endpoint for your FinOps Agent Lambda function.

## Creating the API Gateway

### Using AWS CLI

```bash
# Create an API Gateway REST API
aws apigateway create-rest-api \
  --name "FinOpsAgentAPI" \
  --description "API for FinOps Agent" \
  --endpoint-configuration "{ \"types\": [\"REGIONAL\"] }"

# Get the API ID
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='FinOpsAgentAPI'].id" --output text)

# Create a resource
RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $(aws apigateway get-resources --rest-api-id $API_ID --query "items[0].id" --output text) \
  --path-part "query" \
  --query "id" --output text)

# Create a POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

# Set up Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:finops-agent:function:finops-agent/invocations

# Deploy the API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### Using AWS Console

1. Go to the [API Gateway console](https://console.aws.amazon.com/apigateway/home)
2. Click "Create API"
3. Select "REST API" and click "Build"
4. Enter "FinOpsAgentAPI" as the API name and click "Create API"
5. Click "Actions" > "Create Resource"
6. Enter "query" as the Resource Path and click "Create Resource"
7. With the new resource selected, click "Actions" > "Create Method"
8. Select "POST" from the dropdown and click the checkmark
9. Configure the method:
   - Integration type: Lambda Function
   - Use Lambda Proxy integration: Yes
   - Lambda Region: (your region)
   - Lambda Function: finops-agent
   - Click "Save"
10. Click "Actions" > "Deploy API"
11. Create a new stage named "prod" and click "Deploy"

## Granting API Gateway Permission to Invoke Lambda

```bash
aws lambda add-permission \
  --function-name finops-agent \
  --statement-id apigateway-prod \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$AWS_REGION:$ACCOUNT_ID:$API_ID/*/POST/query"
```

## Enabling CORS

### Using AWS CLI

```bash
# Enable CORS for the resource
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --response-parameters "{\"method.response.header.Access-Control-Allow-Origin\":true}"

# Add CORS headers to the integration response
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --response-parameters "{\"method.response.header.Access-Control-Allow-Origin\":\"'*'\"}"

# Create OPTIONS method for preflight requests
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE

# Create a mock integration for OPTIONS
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates "{\"application/json\":\"{\\\"statusCode\\\": 200}\"}"

# Configure OPTIONS method response
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters "{\"method.response.header.Access-Control-Allow-Origin\":true,\"method.response.header.Access-Control-Allow-Methods\":true,\"method.response.header.Access-Control-Allow-Headers\":true}"

# Configure OPTIONS integration response
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters "{\"method.response.header.Access-Control-Allow-Origin\":\"'*'\",\"method.response.header.Access-Control-Allow-Methods\":\"'POST,OPTIONS'\",\"method.response.header.Access-Control-Allow-Headers\":\"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\"}"

# Redeploy the API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### Using AWS Console

1. Go to the [API Gateway console](https://console.aws.amazon.com/apigateway/home)
2. Select your API
3. Select the "query" resource
4. Click "Actions" > "Enable CORS"
5. Check all the options and click "Enable CORS and replace existing CORS headers"
6. Click "Actions" > "Deploy API"
7. Select the "prod" stage and click "Deploy"

## Getting the API URL

After deployment, your API URL will be in the following format:

```
https://{API_ID}.execute-api.{AWS_REGION}.amazonaws.com/prod/query
```

You can get this URL from the AWS Console:

1. Go to the [API Gateway console](https://console.aws.amazon.com/apigateway/home)
2. Select your API
3. Click on "Stages" in the left navigation
4. Select the "prod" stage
5. Copy the "Invoke URL" displayed at the top of the page

Update the `aws-exports.js` file in your React application with this URL.
