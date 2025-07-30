# FinOps Agent Design Document

## Project Overview

The FinOps Agent is a Lambda-based agent built with Strands SDK to assist with FinOps tasks. It provides cost analysis and optimization recommendations for AWS resources.

## Architecture

### Components

1. **AWS Lambda Function**
   - Name: `finops-agent`
   - Runtime: Python 3.11
   - Handler: `lambda_handler.handler`
   - Memory: 256 MB
   - Timeout: 30 seconds

2. **Lambda Layer**
   - Name: `finops-agent-dependencies`
   - Contains all dependencies including Strands SDK

3. **API Gateway**
   - Name: `FinOpsAgentAPI`
   - Type: REST API
   - Integration: AWS_PROXY to Lambda function
   - Endpoint: `/query` (POST method)

4. **AWS Amplify UI**
   - Name: `FinOpsAgentUI`
   - Framework: React
   - Authentication: Amazon Cognito
   - API Integration: API Gateway

5. **Amazon Cognito**
   - User Pool: For authentication
   - Identity Pool: For AWS resource access

6. **IAM Role**
   - Permissions for:
     - Bedrock model invocation
     - Cost Explorer API access
     - CloudWatch Logs

4. **CloudFormation Stack**
   - Name: `finops-agent`
   - Manages all resources

### Deployment Artifacts

- **Application Code**: `app.zip` (contains `lambda_handler.py`)
- **Dependencies Layer**: `dependencies.zip` (contains all Python dependencies)
- **UI Build**: `finops-ui-build-debug.zip` (contains React application build)
- **S3 Bucket**: `${DEPLOYMENT_BUCKET}`

## Implementation Details

### Lambda Handler

The Lambda handler initializes a Strands Agent with:
- A FinOps-focused system prompt
- Tools for:
  - Basic calculations
  - Current time retrieval
  - AWS cost data analysis

The handler processes incoming queries and returns formatted responses.

### Custom Tools

1. **get_aws_cost_summary**
   - Retrieves cost data from AWS Cost Explorer
   - Supports different time periods (MONTH_TO_DATE, LAST_MONTH)
   - Groups costs by AWS service

### Deployment Process

1. **Package Creation**
   - Application code packaged separately from dependencies
   - Dependencies packaged from virtual environment to ensure compatibility
   - Both packages uploaded to S3

2. **CloudFormation Deployment**
   - Creates Lambda function with appropriate permissions
   - Creates Lambda layer with dependencies
   - Sets up CloudWatch logging

3. **Runtime Configuration**
   - Python 3.11 runtime to match development environment
   - Environment variables for region and logging

## Web UI Implementation

### Frontend Architecture

The FinOps Agent UI is a React application deployed on AWS Amplify with the following features:
- Authentication via Amazon Cognito
- API integration with the Lambda function through API Gateway
- Responsive design for various device sizes
- Query history tracking

### UI Components

1. **Authentication**
   - Login/signup forms provided by Amplify UI components
   - Session management and token handling

2. **Query Interface**
   - Input field for cost-related questions
   - Response display with proper formatting
   - Loading state indication

3. **History Section**
   - List of previous queries and responses
   - Timestamp for each interaction

### Integration with Backend

The UI integrates with the backend Lambda function through:
1. API Gateway REST endpoint
2. AWS Amplify API client libraries
3. AWS Cognito for authentication

## Development Challenges and Solutions

### Challenge: Dependency Compatibility

**Issue**: Initial deployment faced "No module named 'pydantic_core._pydantic_core'" error.

**Solution**: 
1. Verified the code works locally in the virtual environment
2. Created a packaging script to use the exact same libraries from the virtual environment
3. Updated Lambda runtime to match the development environment (Python 3.11)
4. Removed python_repl tool which had file system access issues in Lambda

### Challenge: Lambda Layer Size

**Issue**: Dependencies package is large (~65MB) due to Strands SDK requirements.

**Solution**: 
1. Separated application code from dependencies
2. Used Lambda layers to manage dependencies efficiently

## Troubleshooting and Issue Resolution

### UI Response Handling Issue

**Issue**: The UI displayed empty responses (`{"response":{}}`) when querying the Lambda function.

**Investigation**:
1. **Lambda Function**: Tested directly and confirmed it returns proper responses.
2. **API Gateway**: Found "Internal server error" when testing directly, suggesting integration issues.
3. **UI Code**: Identified incorrect response parsing in the React application.

**Root Cause**: Mismatch between how the Lambda function formatted its response and how the UI parsed it.

**Solution**:
1. Added debug information display to the UI to visualize raw API responses
2. Enhanced response parsing logic to handle different response formats:
   ```javascript
   if (apiResponse && apiResponse.body) {
     if (typeof apiResponse.body === 'string') {
       try {
         const parsedBody = JSON.parse(apiResponse.body);
         responseText = parsedBody.response || JSON.stringify(parsedBody);
       } catch (e) {
         responseText = apiResponse.body;
       }
     } else {
       responseText = apiResponse.body.response || JSON.stringify(apiResponse.body);
     }
   }
   ```
3. Deployed updated UI with improved error handling

**Outcome**: The UI now correctly displays responses from the Lambda function, properly parsing the response format.

## Testing

The agent was tested with simple queries like "What is 2+2?" to verify basic functionality.

## Future Enhancements

1. Add more specialized FinOps tools:
   - Reserved Instance analysis
   - Savings Plan recommendations
   - Resource utilization analysis

2. Improve the system prompt with more specific FinOps guidance

3. Enhance the UI with data visualization capabilities

## Deployed Resources

- **Lambda Function**: `finops-agent`
- **Lambda Layer**: `finops-agent-dependencies`
- **CloudFormation Stack**: `finops-agent`
- **API Gateway**: `FinOpsAgentAPI` (endpoint: `${API_GATEWAY_ENDPOINT}`)
- **Amplify Application**: `FinOpsAgentUI` (URL: `https://d1qhkm9u84uoie.amplifyapp.com`)
- **Cognito User Pool**: `us-east-1_DQpPM15TX`
- **S3 Artifacts**:
  - `s3://${DEPLOYMENT_BUCKET}/app.zip`
  - `s3://${DEPLOYMENT_BUCKET}/dependencies.zip`
  - `s3://${DEPLOYMENT_BUCKET}/finops-ui-build-debug.zip`

## Usage

### Lambda Function

The Lambda function can be invoked with a JSON payload containing a query:

```json
{
  "query": "What is the current AWS spend?"
}
```

The response will include the query and the agent's response:

```json
{
  "statusCode": 200,
  "body": {
    "query": "What is the current AWS spend?",
    "response": "..."
  }
}
```

### Web UI

The web UI can be accessed at `https://d1qhkm9u84uoie.amplifyapp.com`. Users need to:

1. Sign in with Cognito credentials
2. Enter a query in the input field
3. View the response and debug information
4. Review previous queries in the history section
