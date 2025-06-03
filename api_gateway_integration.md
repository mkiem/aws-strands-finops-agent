# API Gateway Integration with Lambda

This document outlines the key learnings and best practices for integrating API Gateway with Lambda functions, specifically for the FinOps Agent project.

## Lambda Proxy Integration

When using Lambda proxy integration with API Gateway, the Lambda function receives the full HTTP request as an event and must return a response in a specific format.

### Event Format

The Lambda function receives an event with the following structure:

```json
{
  "resource": "/query",
  "path": "/query",
  "httpMethod": "POST",
  "headers": {
    "Content-Type": "application/json",
    ...
  },
  "queryStringParameters": null,
  "pathParameters": null,
  "stageVariables": null,
  "body": "{\"query\": \"What is my S3 spend?\"}",
  "isBase64Encoded": false
}
```

### Response Format

The Lambda function must return a response in the following format:

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

## CORS Support

To enable CORS for browser-based applications, you need to:

1. Add CORS headers to the Lambda response
2. Create an OPTIONS method in API Gateway
3. Configure the OPTIONS method to return CORS headers

### CORS Headers

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
```

## Error Handling

Implement proper error handling in the Lambda function:

```python
try:
    # Process the request
    ...
except Exception as e:
    return {
        'statusCode': 500,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            ...
        },
        'body': json.dumps({'error': str(e)})
    }
```

## Testing

Test the API Gateway endpoint directly before integrating with the UI:

```bash
curl -X POST \
  https://YOUR_API_ID.execute-api.REGION.amazonaws.com/prod/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is my S3 spend?"}'
```

## Common Issues and Solutions

1. **502 Bad Gateway**: This often indicates that the Lambda function is not returning the expected response format. Make sure the response includes `statusCode`, `headers`, and a string `body`.

2. **CORS Errors**: If the browser shows CORS errors, make sure the Lambda function includes the proper CORS headers in the response.

3. **JSON Parsing Errors**: Make sure the `body` field in the Lambda response is a string, not an object. Use `json.dumps()` to serialize the response.

4. **Lambda Permission**: Make sure the Lambda function has permission to be invoked by API Gateway.

## Best Practices

1. **Use Lambda Proxy Integration**: This simplifies the integration and allows the Lambda function to handle the full HTTP request.

2. **Include CORS Headers**: Always include CORS headers in the Lambda response to allow browser-based applications to access the API.

3. **Implement Error Handling**: Provide meaningful error messages to clients.

4. **Test Thoroughly**: Test the API Gateway endpoint directly before integrating with the UI.

5. **Use JSON Serialization**: Make sure to serialize the response body using `json.dumps()`.

6. **Log Requests and Responses**: Add logging to help with debugging.

7. **Use Environment Variables**: Use environment variables for configuration to avoid hardcoding values.

8. **Separate Concerns**: Keep the API Gateway configuration separate from the Lambda function code.

9. **Use CloudFormation**: Use CloudFormation to manage the API Gateway and Lambda resources.

10. **Monitor Performance**: Monitor the performance of the API Gateway and Lambda function to identify bottlenecks.
