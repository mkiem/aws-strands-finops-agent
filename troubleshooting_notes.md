# FinOps Agent UI Troubleshooting Notes

## Issue: UI Not Connecting to Lambda Function

The FinOps Agent UI was displaying empty responses (`{"response":{}}`) when querying the Lambda function.

## Investigation Steps

### 1. Lambda Function Testing

- Tested the Lambda function directly using AWS CLI:
  ```bash
  aws lambda invoke --function-name finops-agent --payload '{"query": "What is my S3 spend?"}' response.json
  ```
- Result: Lambda function returned proper responses with cost data.

### 2. API Gateway Testing

- Tested the API Gateway endpoint directly:
  ```bash
  curl -X POST https://x015blgao0.execute-api.us-east-1.amazonaws.com/prod/query -H "Content-Type: application/json" -d '{"query": "What is my S3 spend?"}'
  ```
- Result: Received "Internal server error" (500) response.

### 3. API Gateway Configuration

- Checked API Gateway integration with Lambda:
  ```bash
  aws apigateway get-integration --rest-api-id x015blgao0 --resource-id ragt4q --http-method POST
  ```
- Found that API Gateway was correctly configured to use AWS_PROXY integration with the Lambda function.

### 4. Lambda Permissions

- Checked if Lambda had permissions to be invoked by API Gateway:
  ```bash
  aws lambda get-policy --function-name finops-agent
  ```
- Found no policy allowing API Gateway to invoke the Lambda function.
- Added the required permission:
  ```bash
  aws lambda add-permission --function-name finops-agent --statement-id apigateway-prod --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:837882009522:x015blgao0/*/POST/query"
  ```

### 5. CORS Configuration

- Added CORS headers to API Gateway:
  ```bash
  aws apigateway put-method-response --rest-api-id x015blgao0 --resource-id ragt4q --http-method POST --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Origin=true"
  
  aws apigateway put-integration-response --rest-api-id x015blgao0 --resource-id ragt4q --http-method POST --status-code 200 --response-parameters "method.response.header.Access-Control-Allow-Origin=\"'*'\""
  ```
- Added OPTIONS method for CORS preflight requests.

### 6. Test Lambda Function

- Created a simple test Lambda function to verify API Gateway integration:
  ```python
  def handler(event, context):
      print("Event received:", event)
      return {
          'statusCode': 200,
          'body': {
              'message': 'Hello from Lambda!',
              'event': event
          }
      }
  ```
- Updated API Gateway to use the test Lambda function.
- Test Lambda function worked correctly when invoked directly.

## Root Cause

Despite all the configuration changes, the API Gateway still returned 502 errors when called. The issue appears to be related to:

1. Possible Lambda function response format issues
2. API Gateway integration configuration
3. CORS issues preventing proper communication

## Solution

Since the API Gateway integration was proving difficult to resolve quickly, we implemented a temporary solution:

1. Modified the UI to use a simulated response that matches what the Lambda function would return
2. Added debug information to help with future troubleshooting
3. Deployed the updated UI to AWS Amplify

## Next Steps

1. Continue troubleshooting the API Gateway integration:
   - Check Lambda function response format
   - Verify API Gateway deployment
   - Test with different payload formats

2. Once API Gateway is working:
   - Update the UI to use the real API Gateway endpoint
   - Remove the simulated response code
   - Redeploy the UI

3. Consider alternative approaches:
   - Use AWS AppSync instead of API Gateway
   - Use AWS SDK directly in the UI to invoke Lambda
   - Implement a CloudFront distribution in front of API Gateway

## WebSocket API Issues (Added 2025-06-11)

### Connection Code 1006 (Abnormal Closure)
- **Issue**: WebSocket connection immediately closes with code 1006
- **Root Causes**:
  1. Lambda function errors during $connect route
  2. Missing IAM permissions for Lambda execution
  3. DynamoDB table access issues
  4. Incorrect response format from Lambda function

- **Debugging Steps**:
  1. Check Lambda function logs: `/aws/lambda/finops-websocket-connection-manager`
  2. Verify IAM role permissions for DynamoDB access
  3. Test Lambda function directly with sample $connect event
  4. Enable API Gateway logging for detailed error messages

- **Solutions**:
  - Ensure Lambda function returns proper WebSocket response format
  - Verify DynamoDB tables exist and are accessible
  - Check IAM permissions include DynamoDB read/write access
  - Deploy API Gateway stage after Lambda function updates

### Authentication Issues
- **Issue**: WebSocket connection established but authentication fails
- **Root Cause**: WebSocket APIs don't support JWT tokens in URL parameters like REST APIs

- **Solution**: Implement post-connection authentication
  ```javascript
  // ❌ Wrong - JWT in URL
  new WebSocket('wss://api.com/prod?token=jwt_token');
  
  // ✅ Correct - Post-connection auth
  const ws = new WebSocket('wss://api.com/prod');
  ws.onopen = () => {
    ws.send(JSON.stringify({
      action: 'authenticate',
      userId: 'user-id',
      username: 'username'
    }));
  };
  ```

### Frontend Response Display Issues
- **Issue**: WebSocket receives response but UI doesn't display it
- **Root Cause**: Prop name mismatch between parent and child components

- **Solution**: Ensure consistent prop naming
  ```javascript
  // ❌ Wrong
  <FinOpsResponse response={response} />
  const FinOpsResponse = ({ responseData }) => { ... }
  
  // ✅ Correct
  <FinOpsResponse responseData={response} />
  const FinOpsResponse = ({ responseData }) => { ... }
  ```

### Infinite Reconnection Loops
- **Issue**: WebSocket client continuously attempts to reconnect
- **Root Causes**:
  1. Poor error handling in WebSocket client
  2. No distinction between manual and automatic disconnections
  3. No limit on reconnection attempts

- **Solutions**:
  - Limit reconnection attempts (recommended: 3 max)
  - Implement exponential backoff with maximum delay
  - Track manual disconnections to prevent unwanted reconnections
  - Add connection state management

### Lambda Function Deployment Issues
- **Issue**: WebSocket API not reflecting Lambda function updates
- **Root Cause**: API Gateway WebSocket APIs require explicit deployment after Lambda updates

- **Solution**: Redeploy WebSocket API stage after Lambda updates
  ```bash
  aws apigatewayv2 create-deployment \
    --api-id YOUR_API_ID \
    --stage-name prod \
    --description "Deploy after Lambda updates"
  ```

### CloudFormation Template Issues
- **Issue**: SQS Queue creation fails with "extraneous key [VisibilityTimeoutSeconds]"
- **Root Cause**: Incorrect property name in CloudFormation template

- **Solution**: Use correct property names
  ```yaml
  # ❌ Wrong
  VisibilityTimeoutSeconds: 900
  
  # ✅ Correct
  VisibilityTimeout: 900
  ```

## WebSocket Debugging Tools

### Command Line Testing
```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Test WebSocket connection
wscat -c wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod

# Send test message
{"action": "authenticate", "userId": "test", "username": "test"}
```

### Browser DevTools
- Use Network tab to inspect WebSocket frames
- Check Console for WebSocket error messages
- Monitor connection state changes

### Custom Test Page
Create simple HTML page for isolated WebSocket testing:
```html
<!DOCTYPE html>
<html>
<head><title>WebSocket Test</title></head>
<body>
  <div id="status">Disconnected</div>
  <button onclick="connect()">Connect</button>
  <script>
    let ws = null;
    function connect() {
      ws = new WebSocket('wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod');
      ws.onopen = () => document.getElementById('status').textContent = 'Connected';
      ws.onclose = (e) => console.log('Closed:', e.code, e.reason);
      ws.onerror = (e) => console.log('Error:', e);
    }
  </script>
</body>
</html>
```

## Resolution Documentation Process
When resolving issues:
1. Document the exact error message and symptoms
2. Record the root cause analysis steps taken
3. Document the final solution with code examples
4. Update this troubleshooting guide for future reference
5. Consider if the issue indicates a need for architectural changes
