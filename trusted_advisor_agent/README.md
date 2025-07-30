# AWS Trusted Advisor Agent

The AWS Trusted Advisor Agent is a specialized component of the FinOps Agent system that provides intelligent cost optimization recommendations using AWS Trusted Advisor APIs and AI-powered insights.

## 🎯 **Features**

- **Cost Optimization Recommendations**: Real-time access to AWS Trusted Advisor insights
- **Dual API Support**: New Trusted Advisor API with legacy Support API fallback
- **AI-Powered Analysis**: Enhanced recommendations using Amazon Bedrock
- **Performance Insights**: Service limit monitoring and performance optimization
- **Security Recommendations**: Security-related Trusted Advisor checks
- **Fault Tolerance**: Comprehensive error handling and retry logic

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Supervisor    │    │  Trusted Advisor │    │   AWS Trusted   │
│   Agent         │───►│  Agent           │───►│   Advisor API   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Amazon         │    │   Legacy        │
                       │   Bedrock        │    │   Support API   │
                       └──────────────────┘    └─────────────────┘
```

### Core Components

- **Lambda Function**: Serverless execution with optimized performance
- **Trusted Advisor Integration**: Direct API access to recommendations
- **AI Enhancement**: Bedrock integration for intelligent insights
- **Dual API Support**: New API with legacy fallback
- **Dependencies Layer**: Shared libraries (Strands SDK, boto3)
- **Error Handling**: Dead letter queue and comprehensive monitoring

## 🚀 **Quick Deployment**

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.11+ installed
- S3 bucket for deployment artifacts
- AWS Support plan (Business/Enterprise recommended for full functionality)

### One-Command Deployment

```bash
./deploy.sh --bucket YOUR_DEPLOYMENT_BUCKET
```

### Custom Deployment

```bash
# Deploy to staging environment
./deploy.sh --bucket my-bucket --env staging --region us-west-2

# Deploy with custom configuration
./deploy.sh --bucket my-bucket --memory 1024 --timeout 600

# Build packages only
./deploy.sh --bucket my-bucket --build-only
```

## 📋 **Configuration**

### CloudFormation Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `DeploymentBucket` | S3 bucket for artifacts | Required | 3-63 chars |
| `Environment` | Deployment environment | `prod` | dev/staging/prod |
| `LambdaTimeout` | Function timeout (seconds) | `300` | 30-900 |
| `LambdaMemorySize` | Memory allocation (MB) | `512` | 128-10240 |
| `LogRetentionDays` | Log retention period | `30` | 1-3653 |
| `EnableLegacySupport` | Enable Support API fallback | `true` | true/false |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REGION` | AWS region | Auto-detected |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Deployment environment | `prod` |
| `ENABLE_LEGACY_SUPPORT` | Legacy API fallback | `true` |
| `POWERTOOLS_SERVICE_NAME` | Service name for observability | `trusted-advisor-agent` |

## 🔧 **Usage**

### Query Examples

The agent responds to Trusted Advisor related queries:

```python
# Example invocation payload
{
    "query": "Show me cost optimization recommendations",
    "context": {
        "user_id": "user123",
        "session_id": "session456"
    }
}
```

### Supported Query Types

- **Cost Optimization**: "Show me cost optimization recommendations"
- **Performance**: "What performance improvements are available?"
- **Security**: "Show me security recommendations"
- **Service Limits**: "Are we approaching any service limits?"
- **Fault Tolerance**: "Show me fault tolerance recommendations"
- **Specific Checks**: "Show me EC2 Reserved Instance recommendations"

## 🏗️ **Building and Deployment**

### Package Build Process

```bash
# Build with defaults
./build_lambda_package.sh

# Build specific components
./build_lambda_package.sh deps    # Dependencies only
./build_lambda_package.sh app     # Application only
./build_lambda_package.sh clean   # Clean build directory
```

### Manual CloudFormation Deployment

```bash
# Upload packages to S3
aws s3 cp dist/app.zip s3://YOUR_BUCKET/trusted-advisor-agent/app.zip
aws s3 cp dist/dependencies.zip s3://YOUR_BUCKET/trusted-advisor-agent/dependencies.zip

# Deploy stack
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name finops-trusted-advisor-agent-prod \
  --parameter-overrides \
    DeploymentBucket=YOUR_BUCKET \
    Environment=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Update Deployment

```bash
# Update packages and redeploy
./build_lambda_package.sh
./deploy.sh --bucket YOUR_BUCKET --deploy-only
```

## 📊 **Monitoring and Observability**

### CloudWatch Metrics

- **Invocations**: Function execution count
- **Duration**: Execution time and percentiles
- **Errors**: Error rate and count
- **Throttles**: Concurrency throttling events
- **Custom Metrics**: Trusted Advisor API calls and response times

### CloudWatch Alarms

- **Error Rate**: Triggers when error rate exceeds 5 errors in 10 minutes
- **Duration**: Monitors execution time approaching timeout
- **API Failures**: Alerts on Trusted Advisor API failures

### Logging

```bash
# View real-time logs
aws logs tail /aws/lambda/finops-trusted-advisor-agent-prod --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-trusted-advisor-agent-prod \
  --filter-pattern "ERROR"

# Search for API calls
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-trusted-advisor-agent-prod \
  --filter-pattern "TrustedAdvisor API"
```

### Custom Metrics

The agent publishes custom metrics to CloudWatch:

- `TrustedAdvisorAPICalls`: Number of API calls made
- `RecommendationsRetrieved`: Number of recommendations fetched
- `APIResponseTime`: Response time for Trusted Advisor APIs
- `LegacyAPIFallbacks`: Number of fallbacks to legacy Support API

## 🔒 **Security**

### IAM Permissions

The agent requires these AWS permissions:

#### New Trusted Advisor API (Recommended)
- `trustedadvisor:ListRecommendations`
- `trustedadvisor:GetRecommendation`
- `trustedadvisor:GetOrganizationRecommendation`
- `trustedadvisor:ListChecks`
- `trustedadvisor:GetCheck`
- `trustedadvisor:GetCheckResult`

#### Legacy Support API (Fallback)
- `support:DescribeTrustedAdvisorChecks`
- `support:DescribeTrustedAdvisorCheckResult`
- `support:DescribeTrustedAdvisorCheckSummaries`
- `support:RefreshTrustedAdvisorCheck`

#### Additional Permissions
- **Bedrock**: Access to foundation models for AI insights
- **CloudWatch**: Metrics and logging
- **Lambda**: Function execution

### Security Features

- **No Hardcoded Credentials**: Uses IAM roles and environment variables
- **Least Privilege Access**: Minimal required permissions
- **API Fallback**: Graceful degradation when APIs are unavailable
- **Input Validation**: Comprehensive request validation
- **Audit Logging**: Complete request/response logging

### AWS Support Plan Requirements

| Feature | Basic | Developer | Business | Enterprise |
|---------|-------|-----------|----------|------------|
| New Trusted Advisor API | ✅ | ✅ | ✅ | ✅ |
| Legacy Support API | ❌ | ❌ | ✅ | ✅ |
| Full Recommendations | ❌ | ❌ | ✅ | ✅ |
| Programmatic Access | ❌ | ❌ | ✅ | ✅ |

## 🧪 **Testing**

### Unit Tests

```bash
# Run unit tests (when available)
python -m pytest tests/ -v
```

### Integration Testing

```bash
# Test with real AWS services
aws lambda invoke \
  --function-name finops-trusted-advisor-agent-prod \
  --payload '{"query": "Show me cost optimization recommendations"}' \
  response.json

cat response.json
```

### API Access Testing

```bash
# Test new Trusted Advisor API
aws trustedadvisor list-checks --language en

# Test legacy Support API (requires Business/Enterprise)
aws support describe-trusted-advisor-checks --language en
```

### Local Testing

```bash
# Test locally with SAM (if available)
sam local invoke TrustedAdvisorAgentFunction \
  --event test-event.json
```

## 🚨 **Troubleshooting**

### Common Issues

1. **Permission Errors**
   ```bash
   # Check IAM role permissions
   aws iam get-role-policy \
     --role-name finops-trusted-advisor-agent-role-prod \
     --policy-name TrustedAdvisorAccess
   ```

2. **Support Plan Issues**
   ```bash
   # Check support plan level
   aws support describe-severity-levels
   
   # If this fails, you may need Business/Enterprise support
   ```

3. **API Access Issues**
   ```bash
   # Test new API access
   aws trustedadvisor list-checks --language en
   
   # Test legacy API access
   aws support describe-trusted-advisor-checks --language en
   ```

4. **Timeout Issues**
   - Increase `LambdaTimeout` parameter
   - Check Trusted Advisor API response times
   - Monitor CloudWatch metrics

### Debug Mode

Enable debug logging:

```bash
aws lambda update-function-configuration \
  --function-name finops-trusted-advisor-agent-prod \
  --environment Variables='{LOG_LEVEL=DEBUG}'
```

### Performance Optimization

- **Memory Allocation**: Increase memory for faster API processing
- **Timeout Configuration**: Adjust based on API response times
- **Caching**: Implement response caching for frequently accessed data
- **Batch Processing**: Process multiple recommendations efficiently

## 📚 **API Reference**

### Input Format

```json
{
  "query": "string",
  "context": {
    "user_id": "string",
    "session_id": "string",
    "preferences": {}
  },
  "options": {
    "include_details": true,
    "check_types": ["cost_optimizing", "performance", "security"],
    "language": "en"
  }
}
```

### Output Format

```json
{
  "response": "string",
  "data": {
    "recommendations": [...],
    "check_results": [...],
    "api_used": "new|legacy"
  },
  "metadata": {
    "execution_time": 1.23,
    "recommendations_count": 5,
    "api_calls_made": 3
  }
}
```

### Trusted Advisor Check Categories

- **Cost Optimizing**: EC2 Reserved Instances, Idle Load Balancers, etc.
- **Performance**: High Utilization EC2 Instances, CloudFront optimizations
- **Security**: Security Groups, IAM Use, Root Access Key
- **Fault Tolerance**: EBS Snapshots, Multi-AZ RDS, Route 53 configurations
- **Service Limits**: Service usage approaching limits

## 🔄 **Updates and Maintenance**

### Updating Dependencies

1. Update `requirements.txt`
2. Rebuild packages: `./build_lambda_package.sh`
3. Redeploy: `./deploy.sh --bucket YOUR_BUCKET --deploy-only`

### Scaling Configuration

```bash
# Update memory and timeout
aws cloudformation update-stack \
  --stack-name finops-trusted-advisor-agent-prod \
  --use-previous-template \
  --parameters \
    ParameterKey=LambdaMemorySize,ParameterValue=1024 \
    ParameterKey=LambdaTimeout,ParameterValue=600
```

### API Migration

The agent supports both new and legacy Trusted Advisor APIs:

- **New API**: Recommended for all new deployments
- **Legacy API**: Automatic fallback for compatibility
- **Migration**: Gradual transition with feature flags

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🤝 **Contributing**

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

**Part of the [FinOps Agent](../README.md) project**
