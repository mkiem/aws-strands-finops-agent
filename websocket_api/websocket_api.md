
## WebSocket API Specific Rules (Added 2025-06-11)
- WebSocket APIs require different authentication patterns than REST APIs - use post-connection authentication
- Always redeploy WebSocket API stage after Lambda function updates using: aws apigatewayv2 create-deployment
- WebSocket response prop names must match exactly between parent and child React components
- Limit WebSocket reconnection attempts to prevent infinite loops (recommended: 3 max attempts)
- Use correct CloudFormation property names: VisibilityTimeout (not VisibilityTimeoutSeconds) for SQS
- WebSocket Lambda functions should return proper status codes: 200 for success, 400/500 for errors
- Always test WebSocket connections with wscat before frontend integration
- Document all WebSocket troubleshooting steps in troubleshooting_notes.md for future reference
- WebSocket APIs support up to 15-minute Lambda execution times for background processing
- Use DynamoDB TTL for automatic cleanup of connection and job records