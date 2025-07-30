# FinOps Supervisor Agent

The FinOps Supervisor Agent is the central orchestration component of the FinOps Agent system. It provides intelligent query routing, agent coordination, and response synthesis using advanced AI capabilities and the Strands SDK.

## 🎯 **Features**

- **Intelligent Query Routing**: AI-powered routing to specialized agents
- **Fast-Path Processing**: Sub-millisecond routing for 70% of queries
- **Response Synthesis**: Combines responses from multiple agents
- **Real-time Communication**: WebSocket and HTTP support
- **Container-based Deployment**: Optimized Lambda container image
- **Provisioned Concurrency**: Reduced cold start latency
- **Multi-Agent Orchestration**: Coordinates cost, advisor, and budget agents

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Supervisor      │    │  Specialized    │
│   Application   │───►│  Agent           │───►│  Agents         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Amazon         │    │  AWS APIs       │
                       │   Bedrock        │    │  (Cost Explorer,│
                       └──────────────────┘    │  Trusted Advisor)│
                                               └─────────────────┘
```

### Core Components

- **Lambda Function**: Container-based serverless execution
- **Query Router**: Intelligent routing logic with LLM integration
- **Agent Orchestrator**: Manages communication with specialized agents
- **Response Synthesizer**: Combines and formats responses
- **Function URL**: Direct HTTPS endpoint for real-time communication
- **API Gateway**: Optional legacy REST API support

## 🚀 **Quick Deployment**

### Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- ECR repository access

### One-Command Deployment

```bash
./deploy.sh
```

### Custom Deployment

```bash
# Deploy to staging environment
./deploy.sh --env staging --region us-west-2

# Deploy with custom configuration
./deploy.sh --memory 2048 --timeout 600 --concurrency 5

# Build container only
./deploy.sh --build-only
```

## 📋 **Configuration**

### CloudFormation Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `ECRRepository` | ECR repository name | `finops-supervisor-agent` | 2-256 chars |
| `ImageTag` | Container image tag | `latest` | 1-128 chars |
| `Environment` | Deployment environment | `prod` | dev/staging/prod |
| `LambdaTimeout` | Function timeout (seconds) | `300` | 30-900 |
| `LambdaMemorySize` | Memory allocation (MB) | `1024` | 128-10240 |
| `ProvisionedConcurrency` | Provisioned executions | `2` | 0-100 |
| `CorsOrigins` | Allowed CORS origins | `localhost` | Comma-delimited |
| `EnableApiGateway` | Enable API Gateway | `true` | true/false |
| `LogRetentionDays` | Log retention period | `30` | 1-3653 |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POWERTOOLS_SERVICE_NAME` | Service name for observability | `finops-supervisor-agent` |
| `POWERTOOLS_METRICS_NAMESPACE` | CloudWatch metrics namespace | `FinOpsAgent` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Deployment environment | `prod` |
| `PYTHONPATH` | Python module path | `/var/task` |

## 🔧 **Usage**

### Direct Function URL

```bash
# Get Function URL from CloudFormation outputs
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name finops-supervisor-agent-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`SupervisorAgentFunctionUrl`].OutputValue' \
  --output text)

# Send query
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my current AWS spend?"}'
```

### API Gateway (Legacy)

```bash
# Get API Gateway endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name finops-supervisor-agent-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`SupervisorApiGatewayEndpoint`].OutputValue' \
  --output text)

# Send query
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me cost optimization recommendations"}'
```

### Query Examples

The supervisor agent handles various types of FinOps queries:

```json
{
  "query": "What is my current AWS spend?",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Supported Query Types:**
- **Cost Analysis**: "What is my current AWS spend?"
- **Forecasting**: "Forecast my costs for next quarter"
- **Optimization**: "Show me cost optimization recommendations"
- **Budget Management**: "How am I tracking against my budget?"
- **Service Analysis**: "Which services are most expensive?"
- **Trend Analysis**: "Show me cost trends over time"

## 🏗️ **Building and Deployment**

### Container Build Process

```bash
# Build with defaults
./build_lambda_package.sh

# Build with custom options
./build_lambda_package.sh \
  --name my-supervisor-agent \
  --tag v1.0 \
  --region us-west-2

# Build only (don't push to ECR)
./build_lambda_package.sh --build-only
```

### Manual CloudFormation Deployment

```bash
# Deploy stack
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name finops-supervisor-agent-prod \
  --parameter-overrides \
    ECRRepository=finops-supervisor-agent \
    ImageTag=latest \
    Environment=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Update Deployment

```bash
# Update container image
./build_lambda_package.sh --tag v2.0

# Update Lambda function
aws lambda update-function-code \
  --function-name finops-supervisor-agent-prod \
  --image-uri ACCOUNT.dkr.ecr.REGION.amazonaws.com/finops-supervisor-agent:v2.0
```

## 📊 **Monitoring and Observability**

### CloudWatch Metrics

- **Invocations**: Function execution count
- **Duration**: Execution time and percentiles
- **Errors**: Error rate and count
- **Throttles**: Concurrency throttling events
- **ProvisionedConcurrencyInvocations**: Warm start invocations

### CloudWatch Alarms

- **Error Rate**: Triggers when error rate exceeds 10 errors in 10 minutes
- **Duration**: Monitors execution time approaching timeout
- **Throttles**: Alerts on concurrency throttling

### Logging

```bash
# View real-time logs
aws logs tail /aws/lambda/finops-supervisor-agent-prod --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-supervisor-agent-prod \
  --filter-pattern "ERROR"

# Search for specific queries
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-supervisor-agent-prod \
  --filter-pattern "\"What is my current AWS spend\""
```

### Custom Metrics

The agent publishes custom metrics to CloudWatch:

- `QueryProcessingTime`: Time to process and route queries
- `AgentInvocations`: Number of specialized agent invocations
- `FastPathHits`: Queries processed via fast-path routing
- `ResponseSynthesisTime`: Time to combine agent responses

## 🔒 **Security**

### IAM Permissions

The supervisor agent requires these permissions:

- **Lambda Invoke**: Invoke specialized agents
- **Bedrock**: Access to foundation models for AI routing
- **CloudWatch**: Metrics and logging
- **ECR**: Container image access (for deployment)

### Security Features

- **No Hardcoded Credentials**: Uses IAM roles and environment variables
- **Least Privilege Access**: Minimal required permissions
- **CORS Configuration**: Configurable allowed origins
- **Request Validation**: Input sanitization and validation
- **Audit Logging**: Comprehensive request/response logging

### Network Security

- **VPC Support**: Optional VPC deployment for network isolation
- **Security Groups**: Configurable network access controls
- **Function URLs**: Built-in HTTPS encryption
- **API Gateway**: Additional security layers and throttling

## 🧪 **Testing**

### Unit Tests

```bash
# Run unit tests
cd tests/
python -m pytest test_*.py -v

# Run specific test
python test_fast_path_routing.py
```

### Integration Testing

```bash
# Test with real AWS services
python test_enhanced_routing.py

# Test parallel processing
python test_parallel_processing.py

# Test budget integration
python test_budget_integration.py
```

### Load Testing

```bash
# Concurrent invocations
for i in {1..50}; do
  curl -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is my current AWS spend?"}' &
done
wait
```

### Local Testing

```bash
# Run container locally
docker run --rm -p 9000:8080 finops-supervisor-agent:latest

# Test locally
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"query": "test query"}'
```

## 🚨 **Troubleshooting**

### Common Issues

1. **Container Build Failures**
   ```bash
   # Check Docker daemon
   docker info
   
   # Check Dockerfile syntax
   docker build --no-cache .
   ```

2. **ECR Push Failures**
   ```bash
   # Re-authenticate with ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
   ```

3. **Lambda Function Errors**
   ```bash
   # Check function configuration
   aws lambda get-function --function-name finops-supervisor-agent-prod
   
   # View recent errors
   aws logs filter-log-events \
     --log-group-name /aws/lambda/finops-supervisor-agent-prod \
     --start-time $(date -d '1 hour ago' +%s)000 \
     --filter-pattern "ERROR"
   ```

4. **Agent Communication Issues**
   ```bash
   # Test agent connectivity
   aws lambda invoke \
     --function-name finops-cost-forecast-agent-prod \
     --payload '{"test": true}' \
     response.json
   ```

### Debug Mode

Enable debug logging:

```bash
aws lambda update-function-configuration \
  --function-name finops-supervisor-agent-prod \
  --environment Variables='{LOG_LEVEL=DEBUG}'
```

### Performance Optimization

- **Memory Allocation**: Increase memory for CPU-intensive operations
- **Provisioned Concurrency**: Enable for consistent performance
- **Container Optimization**: Use multi-stage builds to reduce image size
- **Fast-Path Routing**: Optimize routing logic for common queries

## 📚 **API Reference**

### Request Format

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
    "timeout": 30,
    "agents": ["cost", "advisor", "budget"]
  }
}
```

### Response Format

```json
{
  "response": "string",
  "data": {
    "routing_decision": "string",
    "agents_invoked": ["string"],
    "processing_time": 1.23
  },
  "metadata": {
    "request_id": "string",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

## 🔄 **Updates and Maintenance**

### Updating Dependencies

1. Update `requirements.txt`
2. Rebuild container: `./build_lambda_package.sh`
3. Redeploy: `./deploy.sh --deploy-only`

### Scaling Configuration

```bash
# Update provisioned concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name finops-supervisor-agent-prod \
  --qualifier prod \
  --provisioned-concurrency-executions 10

# Update memory and timeout
aws cloudformation update-stack \
  --stack-name finops-supervisor-agent-prod \
  --use-previous-template \
  --parameters \
    ParameterKey=LambdaMemorySize,ParameterValue=2048 \
    ParameterKey=LambdaTimeout,ParameterValue=600
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🤝 **Contributing**

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

**Part of the [FinOps Agent](../README.md) project**
