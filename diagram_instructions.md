# FinOps Agent Architecture Diagram Instructions

I've created a draw.io compatible diagram file (`finops_architecture.drawio`) that represents the AWS architecture for our FinOps Agent project based on the design document.

## How to Use This Diagram

1. **Open the diagram in draw.io**:
   - Go to [draw.io](https://app.diagrams.net/)
   - Click on "Open Existing Diagram"
   - Upload the `finops_architecture.drawio` file

2. **The diagram includes**:
   - AWS Cloud border with all components inside
   - Frontend Layer (AWS Amplify, React.js)
   - Authentication Layer (Amazon Cognito, IAM)
   - Communication Layer (AWS AppSync)
   - Agent Layer (Lambda functions for all three agents)
   - MCP Server Layer (Lambda functions for MCP servers)
   - AWS Service Integration (Cost Explorer, Trusted Advisor, EC2)
   - Storage and Logging (DynamoDB, S3, CloudWatch, CloudFormation)
   - All necessary connections between components

3. **Customization options**:
   - Adjust the layout as needed
   - Add additional components if required
   - Modify colors and styles to match your preferences
   - Add text annotations for further explanation

## Key Architecture Components

### Frontend Layer
- **AWS Amplify**: Hosts the React.js frontend application
- **React.js Frontend**: User interface for interacting with the FinOps Agent

### Authentication Layer
- **Amazon Cognito**: Manages user authentication and authorization
- **IAM**: Defines permissions for various components

### Communication Layer
- **AWS AppSync**: Central communication hub with GraphQL API and WebSocket support

### Agent Layer
- **FinOps Supervisor Agent**: Orchestrates the multi-agent system
- **Cost Analysis Agent**: Specializes in cost data analysis
- **Cost Optimization Agent**: Focuses on cost-saving opportunities

### MCP Server Layer
- **MCP Servers**: Specialized tools for agents

### AWS Service Integration
- **AWS Cost Explorer**: Source of cost and usage data
- **AWS Trusted Advisor**: Source of optimization recommendations
- **Amazon EC2/EBS/etc.**: AWS resources being analyzed

### Storage and Logging
- **Amazon DynamoDB**: Persistent storage for the system
- **Amazon S3**: Storage for static assets and data
- **Amazon CloudWatch**: Monitoring and logging
- **AWS CloudFormation**: Infrastructure as Code

## Data Flow

The diagram illustrates the following data flow:

1. User authenticates via Cognito from the Amplify-hosted frontend
2. User submits a query through the chat interface to AppSync
3. AppSync resolvers invoke the appropriate Lambda functions
4. The Supervisor Agent coordinates with specialized agents as needed
5. Agents use MCP servers to interact with AWS services
6. Results flow back through the agent hierarchy to the frontend
7. Real-time updates are pushed via WebSocket subscriptions

This architecture provides a scalable, secure, and cost-effective foundation for the FinOps Agent system, leveraging AWS serverless services to minimize operational overhead while maintaining high performance and reliability.
