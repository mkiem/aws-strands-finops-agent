# API Gateway Setup for FinOps Agent

This document outlines the steps taken to create and configure the API Gateway for the FinOps Agent.

## 1. Create a Test Lambda Function

First, we created a simple test Lambda function to verify the API Gateway integration:

```python
def handler(event, context):
    print("Event received:", event)
    
    # Return a properly formatted response for Lambda proxy integration
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': '{"message": "Hello from Lambda!", "input": ' + str(event) + '}'
    }
```

This function:
- Logs the received event
- Returns a properly formatted response with CORS headers
- Includes the input event in the response for debugging

## 2. Create a REST API in API Gateway

```bash
aws apigateway create-rest-api \
  --name finops-test-api \
  --region us-east-1
```

## 3. Create a Resource

```bash
aws apigateway create-resource \
  --rest-api-id 71mmhvzkuh \
  --parent-id yig341573d \
  --path-part query
```

## 4. Create a POST Method

```bash
aws apigateway put-method \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method POST \
  --authorization-type NONE
```

## 5. Create a Lambda Proxy Integration

```bash
aws apigateway put-integration \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:837882009522:function:finops-test-api/invocations
```

## 6. Set Up CORS

### 6.1 Create OPTIONS Method

```bash
aws apigateway put-method \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method OPTIONS \
  --authorization-type NONE
```

### 6.2 Create Mock Integration for OPTIONS

```bash
aws apigateway put-integration \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json":"{\"statusCode\": 200}"}'
```

### 6.3 Set Up Method Response for OPTIONS

```bash
aws apigateway put-method-response \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters "method.response.header.Access-Control-Allow-Headers=true,method.response.header.Access-Control-Allow-Methods=true,method.response.header.Access-Control-Allow-Origin=true"
```

### 6.4 Set Up Integration Response for OPTIONS

```bash
aws apigateway put-integration-response \
  --rest-api-id 71mmhvzkuh \
  --resource-id vsr6wb \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'POST,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}'
```

## 7. Add Lambda Permission

```bash
aws lambda add-permission \
  --function-name finops-test-api \
  --statement-id apigateway-test \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:837882009522:71mmhvzkuh/*/POST/query"
```

## 8. Deploy the API

```bash
aws apigateway create-deployment \
  --rest-api-id 71mmhvzkuh \
  --stage-name prod
```

## 9. Test the API

```bash
curl -X POST https://71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my S3 spend?"}'
```

## 10. Update the UI to Use the API

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setDebug('');
  
  try {
    // Make a direct fetch call to the API Gateway endpoint
    const apiUrl = 'https://71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod/query';
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    };
    
    const fetchResponse = await fetch(apiUrl, requestOptions);
    const apiResponse = await fetchResponse.json();
    
    // Debug information
    setDebug(JSON.stringify({
      status: fetchResponse.status,
      statusText: fetchResponse.statusText,
      headers: Object.fromEntries([...fetchResponse.headers.entries()]),
      response: apiResponse
    }, null, 2));
    
    // Extract the response from the API response
    let responseText = '';
    
    if (apiResponse) {
      if (apiResponse.message) {
        responseText = apiResponse.message + "\n\nInput: " + JSON.stringify(JSON.parse(apiResponse.input.body));
      } else {
        responseText = JSON.stringify(apiResponse);
      }
    } else {
      responseText = "No response received from the API.";
    }
    
    setResponse(responseText);
    
    // Add to history
    setHistory([
      { query, response: responseText, timestamp: new Date().toISOString() },
      ...history
    ]);
    
    // Clear the input
    setQuery('');
  } catch (error) {
    console.error('Error querying FinOps agent:', error);
    setResponse(`Error: Failed to get a response from the FinOps agent.\n\nDetails: ${error.message}`);
    setDebug(JSON.stringify(error, null, 2));
  } finally {
    setLoading(false);
  }
};
```

## 11. Deploy the Updated UI

```bash
cd /home/ec2-user/projects/finopsAgent/finops-ui && npm run build
cd /home/ec2-user/projects/finopsAgent/finops-ui/build && zip -r ../finops-ui-build-direct-api.zip .
aws s3 cp /home/ec2-user/projects/finopsAgent/finops-ui/finops-ui-build-direct-api.zip s3://finops-deployment-packages-062025/finops-ui-build-direct-api.zip
APP_ID=$(aws amplify list-apps --query "apps[?name=='FinOpsAgentUI'].appId" --output text) && aws amplify start-deployment --app-id $APP_ID --branch-name main --source-url s3://finops-deployment-packages-062025/finops-ui-build-direct-api.zip
```

## 12. Access the Deployed UI

The UI is now available at: https://d1qhkm9u84uoie.amplifyapp.com

## Key Learnings

1. **Lambda Proxy Integration**: The Lambda function must return a response in the format expected by API Gateway:
   ```json
   {
     "statusCode": 200,
     "headers": { ... },
     "body": "..."
   }
   ```

2. **CORS Configuration**: Proper CORS headers are essential for browser-based applications to access the API.

3. **Lambda Permissions**: The Lambda function needs explicit permission to be invoked by API Gateway.

4. **Direct API Integration**: Using the Fetch API directly in the React application provides more control over the request and response handling.

5. **Debug Information**: Including debug information in the UI helps troubleshoot API integration issues.

## Next Steps

1. Replace the test Lambda function with the actual FinOps Agent Lambda function.
2. Enhance the UI to better display the FinOps Agent responses.
3. Add authentication to the API Gateway.
4. Implement error handling for different types of API responses.
