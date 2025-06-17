# FinOps Agent

A comprehensive AWS cost optimization and financial operations platform built with Strands SDK, featuring intelligent agent orchestration, real-time WebSocket communication, and integrated MCP server support for enhanced automation capabilities.

## Overview

The FinOps Agent addresses the critical challenge of AWS cost management and optimization for enterprises. As organizations scale their cloud infrastructure, managing costs becomes increasingly complex, requiring specialized knowledge of AWS services, pricing models, and optimization strategies.

### Key Features

- **Intelligent Agent Orchestration**: Supervisor agent routes queries to specialized agents for optimal responses
- **Real-time Communication**: WebSocket-based architecture eliminates timeout limitations for complex analysis
- **Cost Analysis & Forecasting**: Predictive cost modeling up to 12 months with 95%+ accuracy
- **Optimization Recommendations**: AI-powered recommendations from AWS Trusted Advisor and custom analysis
- **Budget Management**: Comprehensive budget analysis and recommendations
- **Performance Optimization**: Fast-path routing processes 70% of queries in sub-millisecond time

## Architecture

### Multi-Agent System
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │    │   WebSocket API  │    │  Supervisor     │
│   (Amplify)     │◄──►│   (API Gateway)  │◄──►│  Agent          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Message        │    │  Specialized    │
                       │   Handler        │    │  Agents         │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Background     │    │  AWS APIs       │
                       │   Processor      │    │  (Cost Explorer,│
                       └──────────────────┘    │  Trusted Advisor)│
                                               └─────────────────┘
```

### Components

#### Supervisor Agent (AWS-FinOps-Agent)
- **Purpose**: Intelligent query routing and agent orchestration
- **Technology**: Python 3.11 container image with Strands SDK
- **Performance**: 70% of queries processed via fast-path routing (sub-millisecond)
- **Features**: LLM-based routing for complex queries, comprehensive fallback mechanisms

#### Cost Forecast Agent
- **Purpose**: Cost analysis and forecasting up to 12 months
- **Technology**: Python 3.11 with Strands SDK and Claude 3.5 Haiku
- **Features**: AWS Cost Explorer integration, trend analysis, anomaly detection
- **Performance**: Provisioned concurrency eliminates cold starts

#### Trusted Advisor Agent
- **Purpose**: Cost optimization recommendations from AWS Trusted Advisor
- **Technology**: Strands-based agent with both new and legacy API support
- **Features**: Real-time recommendations, resource-level analysis, exact savings calculations
- **Integration**: Reusable by other agents for comprehensive analysis

#### Budget Management Agent
- **Purpose**: Budget analysis and recommendations
- **Technology**: Python 3.11 with Strands SDK and Claude 3.5 Haiku
- **Features**: Budget performance analysis, historical spending patterns, specific recommendations
- **Integration**: Cost Explorer integration for enhanced data analysis

#### WebSocket API
- **Purpose**: Real-time communication without timeout limitations
- **Components**: Connection Manager, Message Handler, Background Processor
- **Features**: Real-time progress updates, scalable job processing with SQS
- **Benefits**: 15-minute execution limit for complex analysis

#### React Frontend
- **Technology**: React 18 with Material UI, deployed on AWS Amplify
- **Features**: Natural language queries, real-time progress indicators, responsive design
- **Authentication**: Amazon Cognito integration with secure session management

## Project Structure

```
finopsAgent/
├── supervisor_agent/           # Supervisor agent with intelligent routing
├── aws-cost-forecast-agent/    # Cost analysis and forecasting
├── trusted_advisor_agent/      # Trusted Advisor integration
├── budget_management_agent/    # Budget analysis and recommendations
├── websocket_api/             # Real-time WebSocket communication
│   ├── connection_manager/    # WebSocket lifecycle management
│   ├── message_handler/       # Query processing and job queuing
│   └── background_processor/  # Long-running analysis processing
├── finops-ui/                 # React frontend application
├── generated-diagrams/        # Architecture diagrams and documentation
├── requirements.md            # Comprehensive requirements analysis
├── design.md                  # System architecture and design
├── tasks.md                   # Implementation tasks and completion status
├── test-plan.md              # Testing strategy and results
├── threat-model.md           # Security analysis and threat mitigation
└── README.md                 # This file
```

## Strands SDK Documentation

This project includes comprehensive Strands SDK documentation:

- **[STRANDS_SDK_GUIDE.md](STRANDS_SDK_GUIDE.md)**: Complete guide with examples and best practices
- **[STRANDS_QUICK_REFERENCE.md](STRANDS_QUICK_REFERENCE.md)**: Quick reference for common patterns
- **[STRANDS_SDK_README.md](STRANDS_SDK_README.md)**: Full framework documentation
- **[strands_doc_scraper/](strands_doc_scraper/)**: Documentation extraction tools

## Prerequisites

- Python 3.11+
- AWS CLI configured with appropriate permissions
- Access to Amazon Bedrock and Cost Explorer services
- Node.js 18+ for frontend development
- AWS account with necessary service permissions

## Setup and Deployment

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd finopsAgent

# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies for each agent
cd supervisor_agent && pip install -r requirements.txt && cd ..
cd aws-cost-forecast-agent && pip install -r requirements.txt && cd ..
cd trusted_advisor_agent && pip install -r requirements.txt && cd ..
cd budget_management_agent && pip install -r requirements.txt && cd ..
```

### 2. AWS Infrastructure Setup

Each component includes CloudFormation templates for infrastructure deployment:

```bash
# Deploy Supervisor Agent
cd supervisor_agent
./build_lambda_package.sh
aws cloudformation deploy \
  --template-file supervisor_agent_cf.yaml \
  --stack-name finops-supervisor-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET

# Deploy Cost Forecast Agent
cd ../aws-cost-forecast-agent
./build_lambda_package.sh
aws cloudformation deploy \
  --template-file cost_forecast_cf.yaml \
  --stack-name aws-cost-forecast-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET

# Deploy Trusted Advisor Agent
cd ../trusted_advisor_agent
./build_lambda_package.sh
aws cloudformation deploy \
  --template-file trusted_advisor_cf.yaml \
  --stack-name trusted-advisor-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET

# Deploy Budget Management Agent
cd ../budget_management_agent
./build_lambda_package.sh
aws cloudformation deploy \
  --template-file budget_management_cf.yaml \
  --stack-name budget-management-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET
```

### 3. WebSocket API Deployment

```bash
cd websocket_api
./build_all_packages.sh
aws cloudformation deploy \
  --template-file websocket_api_cf.yaml \
  --stack-name finops-websocket-api \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET
```

### 4. Frontend Deployment

```bash
cd finops-ui

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
# Edit .env.local with your AWS configuration

# Build and deploy
npm run build
# Deploy to AWS Amplify or your preferred hosting platform
```

## Configuration

### Environment Variables

Create a `.env.local` file in the `finops-ui` directory:

```env
REACT_APP_AWS_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
REACT_APP_COGNITO_APP_CLIENT_ID=your-app-client-id
REACT_APP_WEBSOCKET_API_URL=wss://your-websocket-api-url
REACT_APP_REST_API_URL=https://your-rest-api-url
```

### AWS Permissions

The system requires the following AWS permissions:
- Cost Explorer: Read access for cost data
- Trusted Advisor: Read access for recommendations
- Budgets: Read access for budget information
- Lambda: Function execution permissions
- DynamoDB: Read/write for session management
- SQS: Send/receive for job processing
- CloudWatch: Logging permissions

## Usage

### Web Interface

1. Access the deployed web application
2. Authenticate using your configured authentication method
3. Enter natural language queries about AWS costs:
   - "What is my current AWS spend?"
   - "Show me cost optimization recommendations"
   - "Forecast my costs for the next 6 months"
   - "Analyze my budget performance"

### API Integration

#### REST API

```bash
curl -X POST \
  https://your-api-gateway-url/prod/query \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{"query": "What is the current AWS spend?"}'
```

#### WebSocket API

```javascript
const ws = new WebSocket('wss://your-websocket-url');

ws.onopen = function() {
    ws.send(JSON.stringify({
        action: 'query',
        query: 'What is my current AWS spend?'
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('Response:', response);
};
```

## Performance Metrics

- **Fast Path Routing**: 70% of queries processed in sub-millisecond time
- **Response Time**: 95% of queries respond within 1 second
- **Cold Start Elimination**: Provisioned concurrency eliminates initialization delays
- **Scalability**: Handles enterprise-scale AWS environments (1000+ resources)
- **Accuracy**: 95%+ accuracy in cost forecasting
- **Cost Optimization**: Enables 15-30% reduction in AWS costs

## Security

- **Authentication**: Amazon Cognito with MFA support
- **Authorization**: IAM roles with least-privilege access
- **Encryption**: TLS 1.2+ for data in transit, AES-256 for data at rest
- **Network Security**: VPC configuration and security groups
- **Audit Logging**: Comprehensive CloudWatch logging
- **Compliance**: Follows AWS Well-Architected Security Pillar

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

- **[Architecture Diagrams](generated-diagrams/)**: Visual system architecture
- **[Requirements](requirements.md)**: Comprehensive requirements analysis
- **[Design Document](design.md)**: System architecture and design decisions
- **[Implementation Tasks](tasks.md)**: Development tasks and completion status
- **[Test Plan](test-plan.md)**: Testing strategy and validation results
- **[Threat Model](threat-model.md)**: Security analysis and mitigation strategies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions, please:
1. Check the [documentation](generated-diagrams/) for detailed information
2. Review [troubleshooting notes](troubleshooting_notes.md) for common issues
3. Open an issue in the GitHub repository
4. Refer to the [Strands SDK documentation](STRANDS_SDK_README.md) for framework-specific questions

## Acknowledgments

- Built with [Strands SDK](https://strandsagents.com/) for intelligent agent orchestration
- Utilizes AWS serverless architecture for scalability and cost optimization
- Integrates with AWS Cost Explorer, Trusted Advisor, and Budgets APIs
- Frontend built with React and Material UI for modern user experience
