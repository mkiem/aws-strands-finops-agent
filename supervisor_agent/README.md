# AWS FinOps Supervisor Agent

The AWS FinOps Supervisor Agent is the central orchestrator for comprehensive AWS financial operations analysis. It coordinates between specialized FinOps agents to provide unified, actionable financial insights.

## Architecture

The supervisor agent orchestrates interactions between:

1. **AWS Cost Forecast Agent** (`aws-cost-forecast-agent`): Provides detailed cost analysis, trends, and forecasting
2. **Trusted Advisor Agent** (`trusted-advisor-agent-trusted-advisor-agent`): Delivers cost optimization recommendations and savings opportunities

## Features

- **Intelligent Query Routing**: Automatically routes queries to appropriate specialized agents
- **Response Synthesis**: Combines responses from multiple agents into coherent insights
- **Comprehensive Analysis**: Provides unified FinOps analysis covering costs and optimization
- **Error Handling**: Gracefully handles agent failures and provides partial results
- **Consistent Formatting**: Maintains consistent monetary formatting ($XX.XX)

## Query Routing Logic

- **Cost analysis queries** → AWS Cost Forecast Agent
- **Optimization queries** → Trusted Advisor Agent  
- **Comprehensive analysis** → Both agents
- **Budget/forecast queries** → AWS Cost Forecast Agent
- **Savings/efficiency queries** → Trusted Advisor Agent

## Tools Available

### `invoke_cost_forecast_agent(query: str)`
Invokes the AWS Cost Forecast Agent for detailed cost analysis.

### `invoke_trusted_advisor_agent(query: str)`
Invokes the Trusted Advisor Agent for cost optimization recommendations.

### `get_comprehensive_finops_analysis(query: str)`
Performs comprehensive analysis by combining data from both agents.

## Deployment

### Prerequisites

- Python 3.11+
- Docker (minimum version 25.0.0)
- AWS CLI configured with appropriate permissions
- Access to invoke other Lambda functions:
  - `aws-cost-forecast-agent`
  - `trusted-advisor-agent-trusted-advisor-agent`

### Container-Based Deployment

The supervisor agent uses container-based Lambda deployment to overcome the 250MB package size limit.

#### Building and Deploying

1. Navigate to the supervisor_agent directory:
```bash
cd supervisor_agent
```

2. Make the build script executable and run it:
```bash
chmod +x build_lambda_package.sh
./build_lambda_package.sh
```

This will:
- Build a Docker container image with all dependencies
- Push the image to Amazon ECR repository: `aws-finops-agent`
- Provide deployment instructions

3. Deploy using CloudFormation:
```bash
aws cloudformation deploy \
  --template-file aws_finops_agent_cf.yaml \
  --stack-name aws-finops-supervisor-agent \
  --parameter-overrides \
    LambdaTimeout=60 \
    LambdaMemorySize=256 \
  --capabilities CAPABILITY_NAMED_IAM
```

#### Container Image Details

- **Base Image**: `public.ecr.aws/lambda/python:3.11`
- **Size Limit**: Up to 10GB (vs 250MB for zip packages)
- **ECR Repository**: `aws-finops-agent`
- **Dependencies**: All Strands SDK dependencies included in container
```

## Usage

### API Gateway Endpoint

After deployment, the supervisor agent is accessible via API Gateway:

```bash
curl -X POST \
  https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are my current AWS costs and optimization opportunities?"}'
```

### Direct Lambda Invocation

```bash
aws lambda invoke \
  --function-name AWS-FinOps-Agent \
  --payload '{"query": "Provide comprehensive FinOps analysis"}' \
  response.json
```

### Supported Input Formats

The supervisor agent accepts queries in multiple formats:

```json
// API Gateway format
{"query": "your question"}

// Direct Lambda formats
{"inputText": "your question"}
{"prompt": "your question"}
{"body": {"query": "your question"}}
```

## Response Format

The supervisor agent returns structured responses:

```json
{
  "query": "original query",
  "response": "synthesized response from agents",
  "agent": "AWS-FinOps-Agent",
  "timestamp": "2025-06-10T02:00:00.000Z"
}
```

## IAM Permissions

The supervisor agent requires permissions to invoke other Lambda functions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:REGION:ACCOUNT:function:aws-cost-forecast-agent",
        "arn:aws:lambda:REGION:ACCOUNT:function:trusted-advisor-agent-trusted-advisor-agent"
      ]
    }
  ]
}
```

## Error Handling

The supervisor agent provides robust error handling:

- **Agent Failures**: Gracefully handles when individual agents fail
- **Partial Results**: Provides available data when some agents are unavailable
- **Clear Error Messages**: Communicates data limitations and suggests alternatives
- **Structured Errors**: Returns consistent error format for programmatic handling

## Integration with Existing System

The supervisor agent is designed to work alongside the existing FinOps system:

- **Backward Compatibility**: Maintains existing API contracts
- **Gradual Migration**: Allows incremental adoption
- **Microservice Architecture**: Follows project's microservice principles
- **Consistent Response Format**: Matches existing UI expectations

## Future Enhancements

- **Async Processing**: Implement parallel agent invocation for better performance
- **Caching**: Add response caching for frequently requested data
- **Additional Agents**: Easy integration of new specialized agents
- **Advanced Routing**: ML-based query routing for better agent selection
