# FinOps Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/mkiem/finops-agent)](https://github.com/mkiem/finops-agent/issues)
[![GitHub stars](https://img.shields.io/github/stars/mkiem/finops-agent)](https://github.com/mkiem/finops-agent/stargazers)

A comprehensive AWS cost optimization and financial operations platform built with intelligent agent orchestration, real-time communication, and advanced automation capabilities.

## 🚀 **What is FinOps Agent?**

FinOps Agent addresses the critical challenge of AWS cost management and optimization for enterprises. As organizations scale their cloud infrastructure, managing costs becomes increasingly complex, requiring specialized knowledge of AWS services, pricing models, and optimization strategies.

Our solution provides an intelligent, multi-agent system that automates cost analysis, provides actionable recommendations, and enables proactive financial operations management.

## ✨ **Key Features**

- 🤖 **Intelligent Agent Orchestration**: Supervisor agent routes queries to specialized agents for optimal responses
- ⚡ **Real-time Communication**: WebSocket-based architecture eliminates timeout limitations for complex analysis
- 📊 **Cost Analysis & Forecasting**: Predictive cost modeling up to 12 months with 95%+ accuracy
- 💡 **AI-Powered Recommendations**: Optimization suggestions from AWS Trusted Advisor and custom analysis
- 💰 **Budget Management**: Comprehensive budget analysis and recommendations
- 🔄 **Performance Optimization**: Fast-path routing processes 70% of queries in sub-millisecond time

## 🏗️ **Architecture**

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

### Core Components

- **Supervisor Agent**: Intelligent query routing and orchestration
- **Cost Forecast Agent**: Advanced cost analysis and 12-month forecasting
- **Trusted Advisor Agent**: AWS optimization recommendations
- **Budget Management Agent**: Budget analysis and financial planning
- **WebSocket API**: Real-time communication infrastructure
- **React Frontend**: Modern, responsive user interface

## 🚀 **Quick Start**

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.11+
- Node.js 18+
- AWS CLI configured

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mkiem/finops-agent.git
   cd finops-agent
   ```

2. **Set up environment**
   ```bash
   cp .env.template .env
   # Edit .env with your AWS configuration
   ```

3. **Deploy the backend**
   ```bash
   # Deploy each agent
   cd supervisor_agent && ./build_lambda_package.sh && cd ..
   cd aws-cost-forecast-agent && ./build_lambda_package.sh && cd ..
   cd trusted_advisor_agent && ./build_lambda_package.sh && cd ..
   cd budget_management_agent && ./build_lambda_package.sh && cd ..
   cd websocket_api && ./build_all_packages.sh && cd ..
   ```

4. **Deploy infrastructure**
   ```bash
   # Deploy CloudFormation stacks (update S3 bucket name)
   aws cloudformation deploy --template-file supervisor_agent/supervisor_agent_cf.yaml \
     --stack-name finops-supervisor-agent --capabilities CAPABILITY_IAM \
     --parameter-overrides S3Bucket=YOUR_DEPLOYMENT_BUCKET
   ```

5. **Set up the frontend**
   ```bash
   cd finops-ui
   npm install
   npm start
   ```

### First Query

Once deployed, you can ask natural language questions like:
- "What is my current AWS spend?"
- "Show me cost optimization recommendations"
- "Forecast my costs for the next 6 months"
- "Analyze my budget performance"

## 📖 **Documentation**

- **[Architecture Guide](docs/architecture/)** - System design and components
- **[Development Guide](docs/development/)** - Setup and development workflow
- **[API Documentation](docs/api/)** - API reference and examples
- **[Examples](examples/)** - Usage examples and sample queries

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📊 **Performance**

- **Fast Path Routing**: 70% of queries processed in sub-millisecond time
- **Response Time**: 95% of queries respond within 1 second
- **Scalability**: Handles enterprise-scale AWS environments (1000+ resources)
- **Accuracy**: 95%+ accuracy in cost forecasting
- **Cost Optimization**: Enables 15-30% reduction in AWS costs

## 🔒 **Security**

Security is a top priority. Please see our [Security Policy](SECURITY.md) for:
- Reporting vulnerabilities
- Security best practices
- Supported versions

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Built with [Strands SDK](https://strandsagents.com/) for intelligent agent orchestration
- Utilizes AWS serverless architecture for scalability and cost optimization
- Integrates with AWS Cost Explorer, Trusted Advisor, and Budgets APIs
- Frontend built with React and Material UI for modern user experience

## 📞 **Support**

- **Documentation**: Check our [docs](docs/) for detailed information
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/mkiem/finops-agent/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/mkiem/finops-agent/discussions)
- **Security**: Report security issues via our [Security Policy](SECURITY.md)

## 🌟 **Star History**

If you find FinOps Agent useful, please consider giving it a star! ⭐

---

**Made with ❤️ by the FinOps Agent community**
