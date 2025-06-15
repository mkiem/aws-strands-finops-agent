# FinOps Agent Architecture Diagrams

This document contains comprehensive architecture diagrams for the FinOps Agent project, reflecting the current state of the system as of June 2025.

## 📊 **Architecture Overview**

The FinOps Agent system is a sophisticated AWS-based solution that provides intelligent cost analysis, optimization recommendations, and budget management through AI-powered agents. The system leverages Claude 3.5 Haiku via Amazon Bedrock and implements advanced routing and real-time processing capabilities.

## 🎨 **Architecture Diagrams**

### **1. High-Level System Architecture**
![FinOps System Architecture](generated-diagrams/finops_system_architecture.png)

**Key Components:**
- **Frontend**: React UI hosted on AWS Amplify with Cognito authentication
- **API Layer**: REST API Gateway and WebSocket API for real-time communication
- **Agent Orchestration**: Supervisor agent with specialized FinOps agents
- **Real-time Processing**: WebSocket-based background processing with SQS queues
- **Data Integration**: Direct integration with AWS Cost Explorer, Trusted Advisor, and Budgets APIs
- **AI Processing**: Claude 3.5 Haiku via Amazon Bedrock for all agents

### **2. Agent Orchestration and Routing Flow**
![Agent Orchestration Flow](generated-diagrams/agent_orchestration_flow.png)

**Routing Intelligence:**
- **Fast Path Routing**: 70% of queries routed in 17 microseconds using keyword matching
- **LLM-based Routing**: 30% of complex queries using Claude 3.5 Haiku (1.5s average)
- **Intelligent Synthesis**: Cross-agent analysis for comprehensive responses

**Specialized Agents:**
- **Cost Forecast Agent**: Cost analysis, forecasting, and historical trends
- **Trusted Advisor Agent**: Cost optimization recommendations with API fallback
- **Budget Management Agent**: Budget analysis, recommendations, and governance

### **3. WebSocket Real-time Architecture**
![WebSocket Real-time Architecture](generated-diagrams/websocket_realtime_architecture.png)

**Real-time Features:**
- **WebSocket API**: Overcomes 30-second Lambda timeout limitations
- **Background Processing**: 15-minute execution limit for complex operations
- **Progress Updates**: Real-time progress tracking (5% → 30% → 60% → 90% → 100%)
- **State Management**: DynamoDB for connection and job state persistence
- **Error Handling**: SQS Dead Letter Queue for failed message processing

### **4. Data Flow and AWS Services Integration**
![Data Flow & AWS Integration](generated-diagrams/data_flow_aws_integration.png)

**AWS Service Integration:**
- **Cost Explorer**: `get_cost_and_usage()`, `get_cost_forecast()`, `get_usage_forecast()`
- **Trusted Advisor**: `list_recommendations()` with Support API fallback
- **AWS Budgets**: `describe_budgets()` for budget analysis
- **Amazon Bedrock**: Claude 3.5 Haiku for natural language processing
- **Strands SDK**: Framework for agent tool integration

### **5. Frontend Integration and Authentication**
![Frontend Integration Architecture](generated-diagrams/frontend_integration_architecture.png)

**Frontend Features:**
- **Authentication**: Amazon Cognito with test user integration
- **Real-time UI**: WebSocket client for live updates
- **Response Rendering**: Cost summary cards, markdown rendering, structured content blocks
- **API Integration**: REST API Gateway and WebSocket API endpoints

### **6. Tool Selection and LLM Decision Flow**
![Tool Selection & LLM Flow](generated-diagrams/tool_selection_llm_flow.png)

**Tool Selection Process:**
1. **Intent Analysis**: Understanding user goals
2. **Keyword Analysis**: Identifying specific tool requirements
3. **Context Analysis**: Determining required data sources
4. **Tool Capability Matching**: Selecting appropriate tools

**Agent Tools:**
- **Cost Forecast Agent**: `get_aws_cost_summary()`, `calculator`, `current_time`
- **Trusted Advisor Agent**: `get_trusted_advisor_recommendations()`, `get_cost_optimization_summary()`
- **Budget Management Agent**: `get_budget_analysis()`, `get_budget_recommendations()`

## 🔧 **Technical Specifications**

### **Performance Metrics**
- **Fast Path Success Rate**: 70.4% of queries
- **Routing Speed**: 289,744x faster than LLM-only routing
- **Average Response Time**: Reduced from 11-32s to 6-18s
- **WebSocket Processing**: Up to 15-minute execution time

### **AWS Services Used**
- **Compute**: Lambda (Python 3.11), ECS containers
- **Storage**: DynamoDB, S3
- **API**: API Gateway (REST & WebSocket), SQS
- **AI/ML**: Amazon Bedrock (Claude 3.5 Haiku)
- **FinOps**: Cost Explorer, Trusted Advisor, AWS Budgets
- **Frontend**: Amplify, Cognito
- **Monitoring**: CloudWatch, X-Ray

### **Security & Authentication**
- **Authentication**: Amazon Cognito User Pools
- **Authorization**: IAM roles and policies
- **API Security**: AWS_IAM authentication for API Gateway
- **Data Encryption**: In-transit and at-rest encryption

## 📈 **System Benefits**

### **Performance Optimization**
- **Sub-second Routing**: Fast path routing for common queries
- **Intelligent Synthesis**: Cross-agent analysis for comprehensive insights
- **Real-time Processing**: WebSocket-based communication eliminates timeout issues
- **Scalable Architecture**: Container-based Lambda functions with auto-scaling

### **User Experience**
- **Natural Language Interface**: Claude 3.5 Haiku for conversational interactions
- **Real-time Feedback**: Progress updates during processing
- **Comprehensive Analysis**: Multi-agent orchestration for complete FinOps insights
- **Responsive UI**: React-based frontend with real-time updates

### **Cost Optimization**
- **Intelligent Routing**: Reduces unnecessary LLM calls by 70%
- **Efficient Processing**: Optimized Lambda functions with appropriate timeouts
- **Resource Management**: Pay-per-request DynamoDB and serverless architecture
- **API Optimization**: Direct AWS service integration without intermediary layers

## 🚀 **Deployment Status**

All components are currently deployed and operational:
- ✅ **Supervisor Agent**: Container-based Lambda with fast path routing
- ✅ **Cost Forecast Agent**: Optimized with 300s timeout and 512MB memory
- ✅ **Trusted Advisor Agent**: Fully functional with API fallback
- ✅ **Budget Management Agent**: Configured with explicit Claude 3.5 Haiku
- ✅ **WebSocket API**: Real-time processing with background jobs
- ✅ **Frontend**: React UI deployed on Amplify with authentication

## 📝 **Architecture Evolution**

The system has evolved through several optimization phases:
1. **Initial Implementation**: Basic agent structure with Strands SDK
2. **Performance Optimization**: Fast path routing implementation
3. **Real-time Enhancement**: WebSocket API for timeout elimination
4. **LLM Standardization**: Explicit Claude 3.5 Haiku configuration across all agents
5. **Current State**: Production-ready system with intelligent routing and synthesis

This architecture provides a robust, scalable, and intelligent FinOps solution that leverages the best of AWS services and AI capabilities.
