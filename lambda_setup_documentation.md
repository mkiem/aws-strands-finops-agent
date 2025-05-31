# AWS Lambda Configuration for FinOps Agent

This document describes the AWS Lambda configuration for the FinOps Agent, including the Lambda functions, IAM roles, and deployment process.

## Lambda Functions

The FinOps Agent consists of three Lambda functions:

1. **Supervisor Agent** (`finops-supervisor-agent`)
   - Coordinates communication between specialized agents
   - Processes user queries and determines which specialized agent to invoke
   - Synthesizes responses from specialized agents

2. **Cost Analysis Agent** (`finops-cost-analysis-agent`)
   - Analyzes AWS cost data using Cost Explorer
   - Provides historical cost analysis
   - Generates cost forecasts

3. **Cost Optimization Agent** (`finops-cost-optimization-agent`)
   - Provides cost optimization recommendations using Trusted Advisor
   - Identifies underutilized resources
   - Suggests cost-saving measures

## Lambda Configuration

All Lambda functions share the following configuration:

- **Runtime**: Python 3.11
- **Memory**: 256 MB
- **Timeout**: 15 minutes (maximum allowed)
- **Provisioned Concurrency**: 1 (to reduce cold starts)
- **Log Retention**: 1 week

## IAM Permissions

The Lambda functions use an IAM role with the following permissions:

- **Basic Lambda Execution** (`AWSLambdaBasicExecutionRole`)
  - CloudWatch Logs access for logging

- **Cost Explorer**
  - `ce:GetCostAndUsage`
  - `ce:GetCostForecast`

- **Trusted Advisor**
  - `support:DescribeTrustedAdvisorChecks`
  - `support:DescribeTrustedAdvisorCheckResult`

- **EC2 and CloudWatch**
  - `ec2:DescribeInstances`
  - `cloudwatch:GetMetricStatistics`

## Environment Variables

The Lambda functions use the following environment variables:

- `MODEL_ID`: The ID of the model to use (default: `amazon.titan-text-express-v1`)
- `TEMPERATURE`: The temperature parameter for the model (default: `0.7`)
- `MAX_TOKENS`: The maximum number of tokens for the model response (default: `4096`)
- `AWS_REGION`: The AWS region to use (automatically set by Lambda)

## Deployment

The Lambda functions are deployed using AWS CDK. The deployment process is as follows:

1. Install dependencies for Lambda functions
2. Install CDK dependencies
3. Deploy the CDK stack

To deploy the Lambda functions, run the following command:

```bash
./scripts/deploy_lambda.sh
```

## Testing

Unit tests for the Lambda handlers are available in the `tests` directory. To run the tests:

```bash
python -m pytest tests/test_lambda_handlers.py -v
```

## Cold Start Optimization

To minimize cold starts, the Lambda functions use the following techniques:

1. **Provisioned Concurrency**: Each function has a provisioned concurrency of 1, ensuring that at least one instance is always warm.

2. **Agent Initialization**: The Strands agents are initialized outside the handler function, so they are only initialized once per Lambda instance.

3. **Memory Allocation**: 256 MB of memory is allocated to each function, which provides a good balance between performance and cost.

## Monitoring and Logging

The Lambda functions log to CloudWatch Logs with a retention period of 1 week. The logs include:

- Request and response details
- Error messages and stack traces
- Agent initialization status

## Next Steps

After deploying the Lambda functions, the next step is to set up AWS AppSync for communication between the frontend and the Lambda functions.
