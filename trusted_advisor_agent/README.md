# Trusted Advisor Agent

A Strands-based AWS Lambda agent that provides cost optimization recommendations from AWS Trusted Advisor. This agent can be used standalone or integrated with other FinOps agents.

## Overview

The Trusted Advisor Agent specializes in retrieving and analyzing cost optimization recommendations from AWS Trusted Advisor. It provides real-time data on:

- Underutilized EC2 instances
- Idle or unused resources
- Reserved Instance opportunities
- Over-provisioned resources
- Storage optimization opportunities
- Load balancer utilization

## Features

### Strands Tools Available

1. **`get_trusted_advisor_recommendations()`**
   - Retrieves all cost optimization recommendations
   - Returns structured data with potential savings
   - Sorts findings by estimated monthly savings

2. **`get_recommendation_details(recommendation_identifier)`**
   - Gets detailed information for a specific recommendation
   - Includes all affected resources and metadata
   - Provides specific optimization actions

3. **`get_cost_optimization_summary()`**
   - Provides high-level summary of optimization opportunities
   - Categorizes findings by service type
   - Shows top savings opportunities

### Key Capabilities

- **Real-time Data**: Direct integration with AWS Trusted Advisor API
- **Exact Calculations**: No rounding or estimation of cost savings
- **Structured Output**: JSON-formatted responses for easy integration
- **Error Handling**: Comprehensive error handling and logging
- **Reusable**: Can be called by other Strands agents

## Project Structure

```
trusted_advisor_agent/
├── __init__.py                    # Package initialization
├── lambda_handler.py              # Main Lambda handler
├── trusted_advisor_tools.py       # Strands tools implementation
├── requirements.txt               # Python dependencies
├── build_lambda_package.sh        # Build script
├── trusted_advisor_cf.yaml        # CloudFormation template
└── README.md                      # This file
```

## Setup and Deployment

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate permissions
- Access to AWS Support API (Business or Enterprise support plan required)
- Strands SDK

### Building the Lambda Package

1. Navigate to the agent directory:
```bash
cd trusted_advisor_agent
```

2. Run the build script:
```bash
./build_lambda_package.sh
```

This creates `trusted_advisor_agent_lambda.zip` ready for deployment.

### Deploying to AWS

1. Upload the Lambda package to S3:
```bash
aws s3 cp trusted_advisor_agent_lambda.zip s3://finops-deployment-packages-062025/
```

2. Deploy using CloudFormation:
```bash
aws cloudformation deploy \
  --template-file trusted_advisor_cf.yaml \
  --stack-name trusted-advisor-agent \
  --parameter-overrides \
    LambdaS3Key=trusted_advisor_agent_lambda.zip \
    LambdaTimeout=300 \
    LambdaMemorySize=512 \
  --capabilities CAPABILITY_NAMED_IAM
```

## Usage

### Direct Lambda Invocation

```bash
aws lambda invoke \
  --function-name trusted-advisor-agent \
  --payload '{"query": "What are my current cost optimization opportunities?"}' \
  response.json
```

### Integration with Other Agents

The Trusted Advisor Agent can be called by other Strands agents:

```python
from trusted_advisor_tools import get_trusted_advisor_recommendations

# Get all recommendations
recommendations = get_trusted_advisor_recommendations()
```

### Bedrock Agent Integration

The agent supports Bedrock agent action groups with the following functions:

- `get_trusted_advisor_recommendations`
- `get_recommendation_details`
- `get_cost_optimization_summary`

## Response Format

### Recommendations Response
```json
{
  "summary": {
    "totalFindings": 15,
    "totalPotentialSavings": 1250.75,
    "lastUpdated": "2025-06-09 23:00:00"
  },
  "findings": [
    {
      "recommendationIdentifier": "check-id",
      "checkName": "Low Utilization Amazon EC2 Instances",
      "status": "warning",
      "description": "Check description...",
      "recommendedAction": "Review and address...",
      "resourceCount": 5,
      "estimatedMonthlySavings": 450.25,
      "resources": [...]
    }
  ]
}
```

## IAM Permissions Required

The agent requires the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "support:DescribeTrustedAdvisorChecks",
        "support:DescribeTrustedAdvisorCheckResult",
        "support:DescribeTrustedAdvisorCheckSummaries",
        "support:RefreshTrustedAdvisorCheck"
      ],
      "Resource": "*"
    }
  ]
}
```

## Limitations

- Requires AWS Business or Enterprise support plan
- Support API is only available in us-east-1 region
- Rate limits apply to Trusted Advisor API calls
- Some checks may not provide exact savings calculations

## Integration with FinOps Agent

This agent is designed to be integrated with the main FinOps agent system. It can be called as a tool to provide Trusted Advisor data alongside Cost Explorer and other AWS cost management services.

## Troubleshooting

### Common Issues

1. **Access Denied**: Ensure AWS Support plan includes Trusted Advisor API access
2. **Region Issues**: Support API only works in us-east-1
3. **Rate Limiting**: Implement retry logic for API calls
4. **Missing Data**: Some checks may not have cost savings data available

### Logging

The agent uses structured logging. Check CloudWatch logs for detailed execution information:

```bash
aws logs tail /aws/lambda/trusted-advisor-agent --follow
```

## Contributing

When modifying this agent:

1. Follow Strands SDK patterns for tool definitions
2. Maintain exact cost calculations without rounding
3. Preserve error handling and logging
4. Update tests and documentation
5. Follow the project's coding standards

## License

This project is part of the FinOps Agent system and follows the same licensing terms.
