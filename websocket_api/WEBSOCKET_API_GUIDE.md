# WebSocket API for FinOps Agent - Complete Guide

## Overview

The WebSocket API provides real-time, bidirectional communication for the FinOps Agent, overcoming the 30-second timeout limitation of API Gateway REST APIs. This enables long-running FinOps analysis with real-time progress updates.

## Architecture

```
Frontend → WebSocket Connection → Message Handler → SQS Queue → Background Processor
    ↓                                                                    ↓
Progress Updates ← WebSocket API ← Real-time Updates ← Supervisor Agent Orchestration
```

## Deployed Resources

### Core Infrastructure
- **WebSocket API ID**: `rtswivmeqj`
- **Endpoint**: `wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod`
- **CloudFormation Stack**: `finops-websocket-api`
- **Status**: ✅ **PRODUCTION READY**

### Lambda Functions
1. **Connection Manager**: `finops-websocket-connection-manager`
   - Handles `$connect`, `$disconnect`, and authentication
   - Runtime: Python 3.11, Memory: 256MB, Timeout: 30s

2. **Message Handler**: `finops-websocket-message-handler`
   - Processes WebSocket messages and queues jobs
   - Runtime: Python 3.11, Memory: 256MB, Timeout: 30s

3. **Background Processor**: `finops-websocket-background-processor`
   - Executes long-running FinOps analysis
   - Runtime: Python 3.11, Memory: 512MB, Timeout: 900s (15 minutes)

### Supporting Services
- **DynamoDB Tables**:
  - `finops-websocket-connections` (connection tracking)
  - `finops-websocket-jobs` (job status tracking)
- **SQS Queue**: `finops-websocket-processing-queue` (with DLQ)
- **IAM Role**: `finops-websocket-lambda-role` (comprehensive permissions)

## Authentication Flow

### 1. Connection Establishment
```javascript
// Frontend connects without authentication
const ws = new WebSocket('wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod');
```

### 2. Post-Connection Authentication
```javascript
// Send authentication message after connection
ws.send(JSON.stringify({
  action: 'authenticate',
  userId: 'user-id-from-cognito',
  username: 'username-from-cognito'
}));
```

### 3. Authentication Response
```javascript
// Server confirms authentication
{
  type: 'authenticated',
  message: 'Welcome username! WebSocket connection established.',
  userId: 'user-id',
  connectionId: 'connection-id'
}
```

## Message Protocol

### Client → Server Messages

#### Authentication
```javascript
{
  action: 'authenticate',
  userId: 'string',
  username: 'string'
}
```

#### FinOps Query
```javascript
{
  action: 'finops_query',
  query: 'What was my S3 spend in May?',
  userId: 'string',
  username: 'string',
  timestamp: 1749612773
}
```

### Server → Client Messages

#### Job Queued
```javascript
{
  type: 'job_queued',
  jobId: 'uuid',
  message: 'Your FinOps query has been queued for processing...',
  query: 'string',
  progress: 5
}
```

#### Progress Updates
```javascript
{
  type: 'progress_update',
  jobId: 'uuid',
  status: 'processing',
  message: 'Analyzing cost data...',
  progress: 30,
  timestamp: 1749612773
}
```

#### Job Completed
```javascript
{
  type: 'job_completed',
  jobId: 'uuid',
  result: {
    agent: 'AWS-FinOps-WebSocket-Supervisor',
    query: 'string',
    response: 'markdown-formatted-analysis',
    cost_analysis: { /* Cost Explorer data */ },
    optimization_recommendations: { /* Trusted Advisor data */ }
  },
  timestamp: 1749612773
}
```

#### Job Failed
```javascript
{
  type: 'job_failed',
  jobId: 'uuid',
  error: 'Error description',
  timestamp: 1749612773
}
```

## Frontend Integration

### WebSocket Client Implementation
```javascript
import WebSocketClient from './utils/websocketClient';

const wsClient = new WebSocketClient(
  'wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod',
  handleMessage,
  handleError,
  handleClose
);

// Connect and authenticate
await wsClient.connect();

// Send FinOps query
wsClient.sendFinOpsQuery('What is my current AWS spend?');
```

### Progress Handling
```javascript
const handleMessage = (message) => {
  switch (message.type) {
    case 'job_queued':
      setProgress(5);
      setProgressMessage(message.message);
      break;
    case 'progress_update':
      setProgress(message.progress);
      setProgressMessage(message.message);
      break;
    case 'job_completed':
      setProgress(100);
      setResponse(message.result);
      break;
    case 'job_failed':
      setError(message.error);
      break;
  }
};
```

## Deployment Guide

### Prerequisites
- AWS CLI configured with appropriate permissions
- S3 bucket for deployment packages: `${DEPLOYMENT_BUCKET}`
- Existing FinOps agents: `aws-cost-forecast-agent`, `trusted-advisor-agent-trusted-advisor-agent`

### Step 1: Build Lambda Packages
```bash
cd websocket_api
./build_packages.sh
```

### Step 2: Upload to S3
```bash
aws s3 cp build/websocket-connection-manager.zip s3://${DEPLOYMENT_BUCKET}/
aws s3 cp build/websocket-message-handler.zip s3://${DEPLOYMENT_BUCKET}/
aws s3 cp build/websocket-background-processor.zip s3://${DEPLOYMENT_BUCKET}/
```

### Step 3: Deploy CloudFormation Stack
```bash
aws cloudformation deploy \
  --template-file cloudformation/finops-websocket-api-fixed.yaml \
  --parameter-overrides ProjectName=finops-websocket LambdaS3Bucket=${DEPLOYMENT_BUCKET} \
  --capabilities CAPABILITY_NAMED_IAM \
  --stack-name finops-websocket-api
```

### Step 4: Update Lambda Functions
```bash
aws lambda update-function-code \
  --function-name finops-websocket-connection-manager \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --s3-key websocket-connection-manager.zip

aws lambda update-function-code \
  --function-name finops-websocket-message-handler \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --s3-key websocket-message-handler.zip

aws lambda update-function-code \
  --function-name finops-websocket-background-processor \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --s3-key websocket-background-processor.zip
```

### Step 5: Deploy WebSocket API
```bash
aws apigatewayv2 create-deployment \
  --api-id rtswivmeqj \
  --stage-name prod \
  --description "Deploy WebSocket API updates"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. WebSocket Connection Code 1006 (Abnormal Closure)
**Symptoms**: Connection immediately closes with code 1006
**Causes**: 
- Lambda function errors
- Missing permissions
- Authentication issues

**Solutions**:
- Check Lambda function logs: `/aws/lambda/finops-websocket-connection-manager`
- Verify IAM permissions for Lambda execution role
- Ensure DynamoDB tables exist and are accessible

#### 2. Frontend Not Displaying Response
**Symptoms**: WebSocket receives data but UI doesn't update
**Cause**: Prop name mismatch in React components

**Solution**:
```javascript
// Ensure correct prop names
<FinOpsResponse responseData={response} />  // ✅ Correct
<FinOpsResponse response={response} />      // ❌ Wrong
```

#### 3. Infinite Reconnection Loops
**Symptoms**: WebSocket continuously attempts to reconnect
**Cause**: Poor error handling in WebSocket client

**Solution**:
- Limit reconnection attempts (max 3)
- Implement exponential backoff
- Distinguish between manual and automatic disconnections

#### 4. Authentication Failures
**Symptoms**: Connection established but authentication fails
**Cause**: Invalid user tokens or missing user information

**Solution**:
- Verify Cognito session is valid
- Check user ID and username extraction
- Ensure authentication message format is correct

### Debugging Tools

#### 1. WebSocket Test Page
Use `websocket_test.html` for direct WebSocket testing:
```html
<!-- Simple WebSocket connection test -->
<script>
const ws = new WebSocket('wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
</script>
```

#### 2. Lambda Function Logs
```bash
# Check connection manager logs
aws logs get-log-events \
  --log-group-name "/aws/lambda/finops-websocket-connection-manager" \
  --log-stream-name "LATEST_STREAM_NAME"

# Check background processor logs
aws logs get-log-events \
  --log-group-name "/aws/lambda/finops-websocket-background-processor" \
  --log-stream-name "LATEST_STREAM_NAME"
```

#### 3. DynamoDB Table Inspection
```bash
# Check active connections
aws dynamodb scan --table-name finops-websocket-connections

# Check job status
aws dynamodb scan --table-name finops-websocket-jobs
```

## Performance Characteristics

### Scalability
- **Concurrent Connections**: Supports thousands of simultaneous WebSocket connections
- **Job Processing**: Background processor handles one job at a time per connection
- **Auto-scaling**: Lambda functions scale automatically based on demand

### Reliability
- **Connection Persistence**: Automatic reconnection with exponential backoff
- **Job Durability**: Jobs stored in DynamoDB with TTL for cleanup
- **Error Handling**: Comprehensive error handling with dead letter queues

### Monitoring
- **CloudWatch Metrics**: Lambda invocations, errors, duration
- **DynamoDB Metrics**: Read/write capacity, throttling
- **API Gateway Metrics**: Connection count, message count, errors

## Security

### Authentication
- **Post-Connection Auth**: Authentication after WebSocket establishment
- **User Context**: All operations tied to authenticated user
- **Session Management**: Connection tracking with user association

### Authorization
- **IAM Roles**: Least privilege access for Lambda functions
- **Resource Isolation**: User-specific data isolation
- **API Gateway**: Built-in DDoS protection and throttling

### Data Protection
- **Encryption in Transit**: WSS (WebSocket Secure) protocol
- **Encryption at Rest**: DynamoDB encryption enabled
- **PII Handling**: No sensitive data stored in logs

## Cost Optimization

### Resource Efficiency
- **Pay-per-Use**: Lambda and DynamoDB on-demand pricing
- **Connection Cleanup**: Automatic cleanup of stale connections
- **TTL Settings**: Automatic data expiration in DynamoDB

### Monitoring Costs
- **Lambda Duration**: Background processor optimized for efficiency
- **DynamoDB Usage**: Minimal read/write operations
- **Data Transfer**: Minimal WebSocket message overhead

## Future Enhancements

### Planned Features
1. **Multi-tenant Support**: Organization-level isolation
2. **Message Queuing**: Offline message delivery
3. **Connection Pooling**: Improved resource utilization
4. **Advanced Analytics**: Real-time usage metrics

### Scalability Improvements
1. **Connection Sharding**: Distribute connections across multiple APIs
2. **Regional Deployment**: Multi-region WebSocket endpoints
3. **Caching Layer**: Redis for session and job state caching

## Conclusion

The WebSocket API successfully overcomes the 30-second timeout limitation while providing:
- ✅ Real-time progress updates
- ✅ 15-minute job processing capability
- ✅ Scalable architecture
- ✅ Comprehensive error handling
- ✅ Production-ready reliability

The implementation demonstrates best practices for serverless WebSocket APIs and provides a solid foundation for real-time FinOps analysis.
