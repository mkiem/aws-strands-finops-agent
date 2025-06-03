# FinOps Agent

A Lambda-based agent built with Strands SDK to assist with FinOps tasks.

## Project Structure

```
finopsAgent/
├── my_agent/
│   ├── __init__.py
│   ├── lambda_handler.py
│   ├── requirements.txt
│   ├── build_lambda_package.sh
│   └── finops_agent_cf.yaml
├── finops-ui/
│   ├── src/
│   │   ├── App.js
│   │   └── ...
│   └── ...
└── README.md
```

## Setup and Deployment

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate permissions
- Access to Amazon Bedrock and Cost Explorer services

### Building the Lambda Package

1. Set up a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the required dependencies:

```bash
cd my_agent
pip install -r requirements.txt
```

3. Run the build script to create the Lambda deployment package:

```bash
chmod +x build_lambda_package.sh
./build_lambda_package.sh
```

This will create a `finops_agent_lambda.zip` file in the `my_agent` directory.

### Deploying to AWS

1. Upload the Lambda package to the designated S3 bucket:

```bash
aws s3 cp my_agent/finops_agent_lambda.zip s3://finops-deployment-packages-062025/finops_agent_lambda.zip
```

2. Deploy using CloudFormation:

```bash
aws cloudformation deploy \
  --template-file my_agent/finops_agent_cf.yaml \
  --stack-name finops-agent \
  --parameter-overrides \
    LambdaS3Key=finops_agent_lambda.zip \
    LambdaTimeout=30 \
    LambdaMemorySize=256 \
  --capabilities CAPABILITY_IAM
```

## API Gateway Integration

The FinOps Agent is accessible through an API Gateway endpoint, which allows the web UI to communicate with the Lambda function.

### Setting Up API Gateway

1. Create a REST API:

```bash
aws apigateway create-rest-api \
  --name finops-api \
  --region us-east-1
```

2. Create a resource and method:

```bash
# Get the root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id YOUR_API_ID --query 'items[?path==`/`].id' --output text)

# Create a resource
aws apigateway create-resource \
  --rest-api-id YOUR_API_ID \
  --parent-id $ROOT_ID \
  --path-part query

# Create a POST method
aws apigateway put-method \
  --rest-api-id YOUR_API_ID \
  --resource-id YOUR_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE
```

3. Set up Lambda proxy integration:

```bash
aws apigateway put-integration \
  --rest-api-id YOUR_API_ID \
  --resource-id YOUR_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:REGION:ACCOUNT_ID:function:finops-agent/invocations
```

4. Add Lambda permission:

```bash
aws lambda add-permission \
  --function-name finops-agent \
  --statement-id apigateway-test \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT_ID:YOUR_API_ID/*/POST/query"
```

5. Deploy the API:

```bash
aws apigateway create-deployment \
  --rest-api-id YOUR_API_ID \
  --stage-name prod
```

### Lambda Response Format for API Gateway

For the Lambda function to work correctly with API Gateway, it must return responses in the following format:

```python
{
    'statusCode': 200,
    'headers': {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    },
    'body': json.dumps({
        'query': query,
        'response': response_text
    })
}
```

## Usage

Once deployed, you can invoke the Lambda function directly or through the API Gateway endpoint:

### Direct Lambda Invocation

```bash
aws lambda invoke \
  --function-name finops-agent \
  --payload '{"query": "What is the current AWS spend?"}' \
  response.json
```

### API Gateway

```bash
curl -X POST \
  https://YOUR_API_ID.execute-api.REGION.amazonaws.com/prod/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is the current AWS spend?"}'
```

### Web UI

The web UI is deployed using AWS Amplify and can be accessed at the provided Amplify URL. The UI communicates with the Lambda function through the API Gateway endpoint.

## Key Learnings and Best Practices

1. **Lambda Proxy Integration**: When using Lambda proxy integration with API Gateway, the Lambda function must return responses in a specific format that includes `statusCode`, `headers`, and a string `body`.

2. **CORS Headers**: Include CORS headers in the Lambda response to allow browser-based applications to access the API.

3. **Error Handling**: Implement proper error handling in the Lambda function to provide meaningful error messages to clients.

4. **Event Structure**: API Gateway sends events to Lambda with a specific structure, where the request body is in the `body` field. The Lambda function must parse this correctly.

5. **JSON Serialization**: The `body` field in the Lambda response must be a string, so use `json.dumps()` to serialize the response.

6. **Testing**: Test the API Gateway endpoint directly before integrating with the UI to ensure it works correctly.

## Customization

To extend the agent's capabilities:
1. Add new tools to the agent initialization in `my_agent/lambda_handler.py`
2. Update the IAM permissions in `my_agent/finops_agent_cf.yaml` as needed
3. Rebuild and redeploy the Lambda package
