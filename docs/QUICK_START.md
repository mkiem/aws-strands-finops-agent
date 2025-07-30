# Quick Start Guide

Get FinOps Agent up and running in minutes!

## 🚀 **One-Command Setup**

```bash
git clone https://github.com/finopsagent/finopsagent.git
cd finopsagent
./scripts/setup.sh
```

## 📋 **Prerequisites**

Before you begin, ensure you have:

- **AWS Account** with appropriate permissions
- **Python 3.11+** installed
- **Node.js 18+** installed
- **AWS CLI** configured
- **Git** installed

### AWS Permissions Required

Your AWS user/role needs these permissions:
- `cost-explorer:*`
- `support:*` (for Trusted Advisor)
- `budgets:*`
- `lambda:*`
- `apigateway:*`
- `cloudformation:*`
- `s3:*` (for deployment artifacts)

## 🛠️ **Manual Setup**

If you prefer manual setup:

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/finopsagent/finopsagent.git
cd finopsagent

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.template .env
# Edit .env with your configuration
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Deployment Configuration
S3_DEPLOYMENT_BUCKET=your-deployment-bucket
STACK_NAME_PREFIX=finops-agent

# Optional: Custom Configuration
LOG_LEVEL=INFO
ENABLE_DEBUG=false
```

### 3. Install Frontend Dependencies

```bash
cd finops-ui
npm install
cd ..
```

### 4. Deploy Backend Services

```bash
# Build and deploy each agent
cd supervisor_agent
./build_lambda_package.sh
cd ..

cd aws-cost-forecast-agent
./build_lambda_package.sh
cd ..

cd trusted_advisor_agent
./build_lambda_package.sh
cd ..

cd budget_management_agent
./build_lambda_package.sh
cd ..

cd websocket_api
./build_all_packages.sh
cd ..
```

### 5. Deploy Infrastructure

```bash
# Deploy CloudFormation stacks
aws cloudformation deploy \
  --template-file supervisor_agent/supervisor_agent_cf.yaml \
  --stack-name finops-supervisor-agent \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides S3Bucket=your-deployment-bucket

# Deploy other stacks similarly...
```

### 6. Start Frontend

```bash
cd finops-ui
npm start
```

## 🧪 **Verify Installation**

### Run Tests

```bash
# Python tests
source venv/bin/activate
pytest

# Frontend tests
cd finops-ui
npm test
```

### Test API Endpoints

```bash
# Test supervisor agent
curl -X POST https://your-api-gateway-url/supervisor \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my current AWS spend?"}'
```

## 🎯 **First Queries**

Once deployed, try these example queries:

### Cost Analysis
```
"What is my current AWS spend?"
"Show me my top 5 most expensive services"
"What was my spend last month compared to this month?"
```

### Forecasting
```
"Forecast my costs for the next 6 months"
"What will my EC2 costs be next quarter?"
"Show me cost trends for the last year"
```

### Optimization
```
"What cost optimization recommendations do you have?"
"Show me underutilized resources"
"How can I reduce my AWS costs?"
```

### Budget Management
```
"How am I tracking against my budget?"
"Show me budget alerts"
"Analyze my budget performance"
```

## 🔧 **Development Mode**

For development and testing:

### 1. Local Development

```bash
# Start backend services locally (requires additional setup)
source venv/bin/activate
python supervisor_agent/app.py

# Start frontend in development mode
cd finops-ui
npm start
```

### 2. Environment Variables for Development

```bash
# .env for development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Use local endpoints
API_BASE_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8001
```

## 📊 **Monitoring and Logs**

### CloudWatch Logs

Monitor your deployment:

```bash
# View supervisor agent logs
aws logs tail /aws/lambda/finops-supervisor-agent --follow

# View API Gateway logs
aws logs tail API-Gateway-Execution-Logs --follow
```

### Health Checks

```bash
# Check agent health
curl https://your-api-gateway-url/health

# Check WebSocket connection
wscat -c wss://your-websocket-url
```

## 🚨 **Troubleshooting**

### Common Issues

**1. Permission Errors**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:user/USERNAME \
  --action-names cost-explorer:GetCostAndUsage
```

**2. Deployment Failures**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name finops-supervisor-agent

# View detailed error logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-supervisor-agent \
  --start-time $(date -d '1 hour ago' +%s)000
```

**3. Frontend Issues**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Getting Help

- **Documentation**: Check the [docs/](../docs/) folder
- **Issues**: Report problems on [GitHub Issues](https://github.com/finopsagent/finopsagent/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/finopsagent/finopsagent/discussions)

## 🎉 **Success!**

You should now have FinOps Agent running! The web interface will be available at `http://localhost:3000` (development) or your deployed URL.

## 📚 **Next Steps**

- Read the [Architecture Guide](architecture/) to understand the system
- Check out [Examples](../examples/) for more query ideas
- Review [Contributing Guidelines](../CONTRIBUTING.md) to contribute
- Join our community discussions

---

**Need help?** Don't hesitate to ask in our [GitHub Discussions](https://github.com/finopsagent/finopsagent/discussions)!
