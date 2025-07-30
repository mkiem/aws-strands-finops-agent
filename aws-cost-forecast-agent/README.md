# AWS Cost Forecast Agent

The AWS Cost Forecast Agent is a serverless component of the FinOps Agent system that provides intelligent cost analysis and forecasting capabilities using AWS Cost Explorer APIs and AI-powered insights.

## 🎯 **Features**

- **Cost Analysis**: Real-time AWS cost and usage analysis
- **Forecasting**: Predictive cost modeling up to 12 months
- **Service Breakdown**: Detailed cost analysis by AWS service
- **Trend Analysis**: Historical cost trends and patterns
- **AI-Powered Insights**: Intelligent cost optimization recommendations
- **Multi-dimensional Analysis**: Cost analysis by region, service, usage type

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Supervisor    │    │  Cost Forecast   │    │   AWS Cost      │
│   Agent         │───►│  Agent           │───►│   Explorer      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Amazon         │
                       │   Bedrock        │
                       └──────────────────┘
```

### Components

- **Lambda Function**: Serverless execution environment
- **IAM Role**: Secure access to AWS Cost Explorer and Bedrock
- **CloudWatch Logs**: Centralized logging and monitoring
- **Dead Letter Queue**: Error handling for failed invocations
- **Dependencies Layer**: Shared libraries (Strands SDK, boto3)

## 🚀 **Quick Deployment**

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.11+ installed
- S3 bucket for deployment artifacts

### One-Command Deployment

```bash
./deploy.sh --bucket YOUR_DEPLOYMENT_BUCKET
```

### Manual Deployment

1. **Build packages**:
   ```bash
   ./build_lambda_package.sh
   ```

2. **Upload to S3**:
   ```bash
   aws s3 cp dist/app.zip s3://YOUR_BUCKET/aws-cost-forecast-agent/app.zip
   aws s3 cp dist/dependencies.zip s3://YOUR_BUCKET/aws-cost-forecast-agent/dependencies.zip
   ```

3. **Deploy CloudFormation**:
   ```bash
   aws cloudformation deploy \
     --template-file cloudformation.yaml \
     --stack-name finops-cost-forecast-agent-prod \
     --parameter-overrides DeploymentBucket=YOUR_BUCKET \
     --capabilities CAPABILITY_NAMED_IAM
   ```

## 📋 **Configuration**

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REGION` | AWS region | Auto-detected |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Deployment environment | `prod` |

### CloudFormation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `DeploymentBucket` | S3 bucket for artifacts | Required |
| `Environment` | Deployment environment | `prod` |
| `LambdaTimeout` | Function timeout (seconds) | `300` |
| `LambdaMemorySize` | Memory allocation (MB) | `512` |
| `LogRetentionDays` | Log retention period | `30` |

## 🔧 **Usage**

### Query Examples

The agent responds to natural language queries about AWS costs:

```python
# Example invocation payload
{
    "query": "What is my current AWS spend?",
    "context": {
        "user_id": "user123",
        "session_id": "session456"
    }
}
```

### Supported Query Types

- **Current Costs**: "What is my current AWS spend?"
- **Service Breakdown**: "Show me costs by service"
- **Time Comparisons**: "Compare this month to last month"
- **Forecasting**: "Forecast my costs for next quarter"
- **Trend Analysis**: "Show me cost trends over the last year"

## 📊 **Monitoring**

### CloudWatch Metrics

- **Invocations**: Function execution count
- **Duration**: Execution time
- **Errors**: Error rate and count
- **Throttles**: Concurrency throttling

### CloudWatch Alarms

- **Error Rate**: Triggers when error rate exceeds threshold
- **Duration**: Monitors execution time
- **Dead Letter Queue**: Alerts on failed invocations

### Log Analysis

```bash
# View recent logs
aws logs tail /aws/lambda/finops-cost-forecast-agent-prod --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-cost-forecast-agent-prod \
  --filter-pattern "ERROR"
```

## 🔒 **Security**

### IAM Permissions

The agent requires these AWS permissions:

- **Cost Explorer**: Full access to cost and usage data
- **Bedrock**: Model invocation for AI insights
- **CloudWatch Logs**: Logging and monitoring

### Security Features

- **No Hardcoded Credentials**: Uses IAM roles
- **Least Privilege Access**: Minimal required permissions
- **Encrypted Logs**: CloudWatch logs encryption
- **VPC Support**: Optional VPC deployment
- **Dead Letter Queue**: Secure error handling

## 🧪 **Testing**

### Unit Tests

```bash
# Run tests (when available)
python -m pytest tests/
```

### Integration Testing

```bash
# Test deployment
aws lambda invoke \
  --function-name finops-cost-forecast-agent-prod \
  --payload '{"query": "What is my current AWS spend?"}' \
  response.json

cat response.json
```

### Load Testing

```bash
# Concurrent invocations
for i in {1..10}; do
  aws lambda invoke \
    --function-name finops-cost-forecast-agent-prod \
    --payload '{"query": "Show me cost trends"}' \
    --invocation-type Event \
    response_$i.json &
done
wait
```

## 🚨 **Troubleshooting**

### Common Issues

1. **Permission Errors**
   ```bash
   # Check IAM role permissions
   aws iam get-role-policy \
     --role-name finops-cost-forecast-agent-role-prod \
     --policy-name CostExplorerAccess
   ```

2. **Timeout Issues**
   - Increase `LambdaTimeout` parameter
   - Optimize query complexity
   - Check Cost Explorer API limits

3. **Memory Issues**
   - Increase `LambdaMemorySize` parameter
   - Monitor CloudWatch metrics
   - Optimize data processing

### Debug Mode

Enable debug logging:

```bash
aws lambda update-function-configuration \
  --function-name finops-cost-forecast-agent-prod \
  --environment Variables='{LOG_LEVEL=DEBUG}'
```

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
    "include_forecast": true,
    "time_range": "last_30_days",
    "granularity": "MONTHLY"
  }
}
```

### Output Format

```json
{
  "response": "string",
  "data": {
    "current_spend": 1234.56,
    "forecast": [...],
    "breakdown": {...}
  },
  "metadata": {
    "execution_time": 1.23,
    "data_freshness": "2024-01-01T00:00:00Z"
  }
}
```

## 🔄 **Updates and Maintenance**

### Updating Dependencies

1. Update `requirements.txt`
2. Rebuild packages: `./build_lambda_package.sh`
3. Redeploy: `./deploy.sh --bucket YOUR_BUCKET --deploy-only`

### Scaling Configuration

```bash
# Update memory and timeout
aws cloudformation update-stack \
  --stack-name finops-cost-forecast-agent-prod \
  --use-previous-template \
  --parameters \
    ParameterKey=LambdaMemorySize,ParameterValue=1024 \
    ParameterKey=LambdaTimeout,ParameterValue=600
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🤝 **Contributing**

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

**Part of the [FinOps Agent](../README.md) project**
