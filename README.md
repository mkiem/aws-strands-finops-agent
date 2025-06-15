# FinOps Agent

A Lambda-based agent built with Strands SDK to assist with FinOps tasks, with integrated MCP server support for enhanced automation capabilities.

## Project Structure

```
finopsAgent/
├── my_agent/
│   ├── __init__.py
│   ├── lambda_handler.py
│   ├── requirements.txt
│   ├── build_lambda_package.sh
│   └── finops_agent_cf.yaml
├── trusted_advisor_agent/
│   ├── __init__.py
│   ├── lambda_handler.py
│   ├── trusted_advisor_tools.py
│   ├── requirements.txt
│   ├── build_lambda_package.sh
│   ├── trusted_advisor_cf.yaml
│   └── README.md
├── finops-ui/
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── FinOpsResponse.jsx
│   │   │   └── FinOpsResponse.css
│   │   └── ...
│   └── ...
└── README.md
```

## Strands SDK Documentation

This project includes comprehensive Strands SDK documentation extracted from the official website:

- **[STRANDS_SDK_GUIDE.md](STRANDS_SDK_GUIDE.md)**: Complete LLM-friendly guide with examples and best practices
- **[STRANDS_QUICK_REFERENCE.md](STRANDS_QUICK_REFERENCE.md)**: Quick reference for common patterns and code snippets
- **[STRANDS_SDK_README.md](STRANDS_SDK_README.md)**: Full extracted documentation from strandsagents.com
- **[strands_documentation_raw.json](strands_documentation_raw.json)**: Raw scraped data for further processing

### Documentation Scraper (`strands_doc_scraper/`)
Python application that recursively crawls the Strands documentation website to create LLM-friendly documentation. Run with:

```bash
cd strands_doc_scraper
./run_scraper.sh
```

## Architecture Diagrams

📊 **[View Complete Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md)**

The project includes comprehensive architecture diagrams showing:
- High-level system architecture
- Agent orchestration and routing flow
- WebSocket real-time processing
- Data flow and AWS services integration
- Frontend integration and authentication
- Tool selection and LLM decision flow

## Components

### Main FinOps Agent (`my_agent/`)
The core agent that handles cost analysis, optimization recommendations, and AWS service interactions. Built with Strands SDK and provides:

- AWS Cost Explorer integration
- Cost analysis and forecasting
- General FinOps recommendations
- Integration with other AWS services

### Trusted Advisor Agent (`trusted_advisor_agent/`)
A specialized Strands-based agent that provides cost optimization recommendations from AWS Trusted Advisor. Features:

- Real-time cost optimization recommendations
- Support for both new TrustedAdvisor API and legacy Support API
- Detailed resource-level analysis
- Exact savings calculations without rounding
- Reusable by other agents

See `trusted_advisor_agent/README.md` for detailed documentation.

### Web UI (`finops-ui/`)
React-based frontend for interacting with the FinOps agents. Provides:

- Cost analysis visualization
- Recommendation display
- Authentication via Cognito
- API Gateway integration

## Setup and Deployment

### Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate permissions
- Access to Amazon Bedrock and Cost Explorer services

### Building the Lambda Package

1. Set up a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the required dependencies:

```bash
cd my_agent
pip install -r requirements.txt
```

3. Run the build script to create the Lambda deployment package:

```bash
chmod +x build_lambda_package.sh
./build_lambda_package.sh
```

This will create a `finops_agent_lambda.zip` file in the `my_agent` directory.

### Deploying to AWS

1. Upload the Lambda package to the designated S3 bucket:

```bash
aws s3 cp my_agent/finops_agent_lambda.zip s3://finops-deployment-packages-062025/finops_agent_lambda.zip
```

2. Deploy using CloudFormation:

```bash
aws cloudformation deploy \
  --template-file my_agent/finops_agent_cf.yaml \
  --stack-name finops-agent \
  --parameter-overrides \
    LambdaS3Key=finops_agent_lambda.zip \
    LambdaTimeout=30 \
    LambdaMemorySize=256 \
  --capabilities CAPABILITY_IAM
```

## API Gateway Integration

The FinOps Agent is accessible through an API Gateway endpoint, which allows the web UI to communicate with the Lambda function.

### Setting Up API Gateway

1. Create a REST API:

```bash
aws apigateway create-rest-api \
  --name finops-api \
  --region us-east-1
```

2. Create a resource and method:

```bash
# Get the root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id YOUR_API_ID --query 'items[?path==`/`].id' --output text)

# Create a resource
aws apigateway create-resource \
  --rest-api-id YOUR_API_ID \
  --parent-id $ROOT_ID \
  --path-part query

# Create a POST method
aws apigateway put-method \
  --rest-api-id YOUR_API_ID \
  --resource-id YOUR_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE
```

3. Set up Lambda proxy integration:

```bash
aws apigateway put-integration \
  --rest-api-id YOUR_API_ID \
  --resource-id YOUR_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:REGION:ACCOUNT_ID:function:finops-agent/invocations
```

4. Add Lambda permission:

```bash
aws lambda add-permission \
  --function-name finops-agent \
  --statement-id apigateway-test \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT_ID:YOUR_API_ID/*/POST/query"
```

5. Deploy the API:

```bash
aws apigateway create-deployment \
  --rest-api-id YOUR_API_ID \
  --stage-name prod
```

## Web UI

The web UI is deployed using AWS Amplify and can be accessed at the following URL:

- **URL**: [https://staging.da7jmqelobr5a.amplifyapp.com](https://staging.da7jmqelobr5a.amplifyapp.com)
- **App ID**: da7jmqelobr5a
- **Branch**: staging

### Authentication

The UI uses Amazon Cognito for authentication:

- **User Pool ID**: us-east-1_DQpPM15TX
- **App Client ID**: 4evk2m4ru8rrenij1ukg0044k6
- **Test User**: testuser / SecurePassword123!

### UI Features

The UI includes:

1. Authentication using Amazon Cognito
2. Query input form for asking FinOps questions
3. Formatted response display with:
   - Cost summary card
   - Markdown rendering
   - Structured content blocks
4. Query history tracking

### Deploying UI Updates

To deploy updates to the UI:

1. Make changes to the React components
2. Build the application:

```bash
cd finops-ui
npm run build
```

3. Create a zip file of the build:

```bash
zip -r finops-ui-build.zip build
```

4. Upload to S3:

```bash
aws s3 cp finops-ui-build.zip s3://finops-deployment-packages-062025/finops-ui-build.zip
```

5. Deploy to Amplify:

```bash
aws amplify start-deployment \
  --app-id da7jmqelobr5a \
  --branch-name staging \
  --source-url s3://finops-deployment-packages-062025/finops-ui-build.zip
```

⚠️ **IMPORTANT**: When creating the deployment package, ensure all files are at the root level of the zip file, NOT inside a subdirectory. See `amplify-deployment-guide.md` for detailed instructions.

## Usage

Once deployed, you can access the FinOps Agent through:

1. **Web UI**: Visit the Amplify URL and log in with your credentials
2. **Direct Lambda Invocation**:

```bash
aws lambda invoke \
  --function-name finops-agent \
  --payload '{"query": "What is the current AWS spend?"}' \
  response.json
```

3. **API Gateway**:

```bash
curl -X POST \
  https://71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is the current AWS spend?"}'
```

## Deployed Resources

- **Lambda Function**: finops-agent
- **API Gateway**: 71mmhvzkuh.execute-api.us-east-1.amazonaws.com/prod
- **Amplify App**: staging.da7jmqelobr5a.amplifyapp.com
- **AWS Cost Forecast Agent**: aws-cost-forecast-agent
  - **Status**: ✅ **OPTIMIZED** - Successfully deployed and functional with improved performance
  - **Function ARN**: arn:aws:lambda:us-east-1:837882009522:function:aws-cost-forecast-agent
  - **CloudFormation Stack**: aws-cost-forecast-agent
  - **S3 Package**: s3://finops-deployment-packages-062025/aws_cost_forecast_agent_lambda.zip
  - **Runtime**: Python 3.11 with Lambda layer for dependencies
  - **Memory**: 512MB (upgraded from 256MB for better performance)
  - **Timeout**: 300 seconds (upgraded from 60s to handle complex forecasting operations)
  - **Capabilities**: Current cost analysis, historical cost trends, cost forecasting up to 12 months
  - **Performance**: ✅ Fixed timeout issues - now handles complex Cost Explorer API operations
  - **Last Updated**: 2025-06-14 ✅ **TIMEOUT FIXED** - Increased timeout and memory for reliable forecasting
- **Trusted Advisor Agent**: trusted-advisor-agent-trusted-advisor-agent (Strands-based cost optimization agent)
  - **Status**: ✅ Successfully deployed and fully functional
  - **Function ARN**: arn:aws:lambda:us-east-1:837882009522:function:trusted-advisor-agent-trusted-advisor-agent
  - **CloudFormation Stack**: trusted-advisor-agent
  - **S3 Package**: s3://finops-deployment-packages-062025/trusted_advisor_agent_lambda.zip
  - **API Integration**: ✅ AWS Trusted Advisor API working (retrieves warning/error recommendations)
  - **Data Validation**: ✅ Successfully retrieving 5 cost optimization recommendations ($247.97 monthly savings)
  - **Last Updated**: 2025-06-10 (Fixed datetime serialization and API parameter issues)
- **AWS FinOps Supervisor Agent**: AWS-FinOps-Agent
- **AWS FinOps Supervisor Agent**: AWS-FinOps-Agent
  - **Status**: ✅ **OPTIMIZED** - Fast path routing with LLM fallback
  - **Function ARN**: arn:aws:lambda:us-east-1:837882009522:function:AWS-FinOps-Agent
  - **CloudFormation Stack**: aws-finops-supervisor-agent
  - **Container Image**: 837882009522.dkr.ecr.us-east-1.amazonaws.com/aws-finops-agent:latest
  - **ECR Repository**: aws-finops-agent
  - **API Gateway Endpoint**: https://mdog752949.execute-api.us-east-1.amazonaws.com/prod/query (legacy fallback)
  - **Private Function URL**: https://bybfgjmve5b5m4baexntp62d3e0dqjty.lambda-url.us-east-1.on.aws/ ✅ **PRIVATE (IAM AUTH)**
  - **API Gateway ID**: mdog752949
  - **Runtime**: Python 3.11 container image with Strands SDK dependencies
  - **Memory**: 512MB, Timeout: 300 seconds (5 minutes for agent orchestration)
  - **Deployment Method**: Container-based Lambda (up to 10GB vs 250MB zip limit)
  - **Authentication**: AWS_IAM with Cognito Identity Pool integration
  - **Architecture**: Supervisor agent orchestrates aws-cost-forecast-agent, trusted-advisor-agent, and budget-management-agent
  - **Performance Optimization**: ⚡ **FAST PATH ROUTING** - 70% of queries use sub-millisecond routing (17 microseconds)
  - **Routing Intelligence**: 
    - **Fast Path**: Budget, cost, and optimization queries → instant routing
    - **LLM Fallback**: Complex multi-domain queries → intelligent routing (1.5s avg)
    - **Comprehensive Fallback**: Error scenarios → complete analysis
  - **Performance Metrics**: 
    - **Fast Path Success Rate**: 70.4% of queries
    - **Routing Speed**: 289,744x faster than LLM-only routing
    - **Average Response Time**: Reduced from 11-32s to 6-18s (estimated)
  - **Current Status**: Production ready with intelligent routing and performance optimization
  - **Benefits**: Sub-second routing for common queries, maintains quality for complex queries
  - **Last Updated**: 2025-06-12 ✅ **FAST PATH ROUTING IMPLEMENTED**
- **WebSocket API for FinOps Agent**: finops-websocket-api
  - **Status**: ✅ **FULLY FUNCTIONAL** - Overcomes 30-second timeout limitation
  - **CloudFormation Stack**: finops-websocket-api
  - **WebSocket API ID**: rtswivmeqj
  - **WebSocket Endpoint**: wss://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod ✅ **ACTIVE**
  - **Architecture**: Real-time bidirectional communication with progress updates
  - **Components**:
    - **Connection Manager**: finops-websocket-connection-manager (handles connect/disconnect)
    - **Message Handler**: finops-websocket-message-handler (processes queries, queues jobs)
    - **Background Processor**: finops-websocket-background-processor (15-minute execution limit)
    - **DynamoDB Tables**: finops-websocket-connections, finops-websocket-jobs
    - **SQS Queue**: finops-websocket-processing-queue (with DLQ)
  - **Benefits**: No timeout limitations, real-time progress updates, scalable job processing
  - **Frontend Integration**: ✅ **WORKING** - Real-time WebSocket communication with fallback
  - **Authentication**: Post-connection authentication via WebSocket messages
  - **Performance**: Successfully processes complex FinOps queries with supervisor agent orchestration
  - **User Experience**: Real-time progress (5% → 30% → 60% → 90% → 100%) with full response display
- **Budget Management Agent**: budget-management-agent
  - **Status**: ✅ **DEPLOYED** - Budget analysis and recommendations
  - **Function ARN**: arn:aws:lambda:us-east-1:837882009522:function:budget-management-agent
  - **CloudFormation Stack**: budget-management-agent
  - **Runtime**: Python 3.11 with Strands SDK (15.3 MiB package)
  - **Framework**: Strands Agent with Claude 3.5 Haiku
  - **LLM Model**: anthropic.claude-3-5-haiku-20241022-v1:0 (Amazon Bedrock)
  - **Memory**: 512MB, Timeout: 300 seconds (5 minutes)
  - **Capabilities**: 
    - Budget performance analysis and recommendations  
    - Historical spending pattern analysis
    - Budget recommendations with specific dollar amounts
    - Integration with Cost Explorer for data analysis
  - **Tools**: get_budget_analysis, get_budget_recommendations
  - **DynamoDB Table**: budget-management-state (PAY_PER_REQUEST)
  - **IAM Roles**: 
    - budget-management-lambda-role (Lambda execution)
    - budget-management-action-execution-role (Budget actions)
  - **CloudWatch Logs**: /aws/lambda/budget-management-agent
  - **Last Updated**: 2025-06-15 ✅ **LLM CONFIGURED** - Added explicit Claude 3.5 Haiku configuration for consistency
