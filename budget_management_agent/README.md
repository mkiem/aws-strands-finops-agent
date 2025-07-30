# Budget Management Agent

A specialized Strands SDK-based agent for proactive AWS cost control and governance through automated budget management.

## Overview

The Budget Management Agent provides comprehensive budget management capabilities including:
- Automated budget creation and monitoring
- Proactive cost control through budget actions
- Budget performance analysis and recommendations
- Real-time budget alerts and governance

## Features

### 🎯 **Core Capabilities**
- **Budget Creation**: Automated budget creation based on cost analysis
- **Budget Monitoring**: Real-time budget performance tracking
- **Automated Actions**: IAM policy enforcement and resource controls
- **Governance**: Organization-wide spending controls
- **Recommendations**: AI-driven budget optimization suggestions

### 📊 **Budget Types Supported**
- **Cost Budgets**: Service-level and organization-wide spending limits
- **Usage Budgets**: Resource usage monitoring and control
- **Reserved Instance Budgets**: RI utilization and coverage tracking
- **Savings Plans Budgets**: Savings Plans optimization monitoring

### 🚀 **Advanced Features**
- **Dynamic Thresholds**: Adaptive budget limits based on usage patterns
- **Multi-Level Actions**: Graduated response (notifications → warnings → restrictions)
- **Historical Analysis**: Budget performance trending and variance analysis
- **Integration Ready**: Designed for supervisor agent orchestration

## Architecture

### **Component Structure**
```
budget_management_agent/
├── lambda_handler.py              # Main agent implementation
├── requirements.txt               # Python dependencies
├── build_lambda_package.sh        # Deployment package builder
├── cloudformation/
│   └── budget-management-agent.yaml  # Infrastructure template
├── build/                         # Build artifacts (created during build)
└── README.md                      # This documentation
```

### **AWS Services Integration**
- **AWS Budgets API**: Core budget management functionality
- **AWS Cost Explorer**: Historical cost data for recommendations
- **Amazon DynamoDB**: Budget state and performance tracking
- **AWS Lambda**: Serverless execution environment
- **Amazon CloudWatch**: Logging and monitoring

## Deployment

### **Prerequisites**
- AWS CLI configured with appropriate permissions
- Python 3.11+
- S3 bucket for deployment packages: `${DEPLOYMENT_BUCKET}`

### **Build and Deploy**

1. **Build the deployment package:**
   ```bash
   cd budget_management_agent
   ./build_lambda_package.sh
   ```

2. **Upload to S3:**
   ```bash
   aws s3 cp budget-management-agent.zip s3://${DEPLOYMENT_BUCKET}/
   ```

3. **Deploy with CloudFormation:**
   ```bash
   aws cloudformation deploy \
     --template-file cloudformation/budget-management-agent.yaml \
     --parameter-overrides \
       ProjectName=budget-management \
       LambdaS3Bucket=${DEPLOYMENT_BUCKET} \
       LambdaS3Key=budget-management-agent.zip \
     --capabilities CAPABILITY_NAMED_IAM \
     --stack-name budget-management-agent
   ```

### **Deployed Resources**
- **Lambda Function**: `budget-management-agent`
- **DynamoDB Table**: `budget-management-state`
- **IAM Roles**: Lambda execution and budget action roles
- **CloudWatch Log Group**: `/aws/lambda/budget-management-agent`

## Usage

### **Available Actions**

#### **1. Analyze Budgets**
```python
{
    "action": "analyze_budgets",
    "parameters": {}
}
```
Returns comprehensive analysis of all existing budgets including utilization, forecasts, and performance insights.

#### **2. Create Budget**
```python
{
    "action": "create_budget",
    "parameters": {
        "budget_name": "EC2-Monthly-Budget",
        "budget_type": "COST",
        "amount": 1000,
        "time_unit": "MONTHLY",
        "service_filter": "Amazon Elastic Compute Cloud - Compute",
        "notification_email": "admin@company.com"
    }
}
```

#### **3. Monitor Budgets**
```python
{
    "action": "monitor_budgets",
    "parameters": {}
}
```
Real-time monitoring with alerts for budgets exceeding thresholds.

#### **4. Recommend Budgets**
```python
{
    "action": "recommend_budgets",
    "parameters": {}
}
```
AI-driven budget recommendations based on historical spending patterns.

#### **5. Create Budget Actions**
```python
{
    "action": "create_budget_actions",
    "parameters": {
        "budget_name": "EC2-Monthly-Budget",
        "action_type": "APPLY_IAM_POLICY",
        "threshold": 90,
        "policy_arn": "arn:aws:iam::aws:policy/AWSDenyAll",
        "target_roles": ["DeveloperRole"],
        "approval_model": "AUTOMATIC"
    }
}
```

#### **6. Get Budget Performance**
```python
{
    "action": "get_budget_performance",
    "parameters": {
        "budget_name": "EC2-Monthly-Budget"
    }
}
```

### **Response Format**
All responses follow the standard agent format:
```json
{
    "agent": "BudgetManagementAgent",
    "action": "action_name",
    "status": "success|error",
    "data": { ... },
    "timestamp": "2025-06-11T20:30:00Z"
}
```

## Integration with FinOps Agent

### **Supervisor Agent Integration**
The Budget Management Agent is designed to work with the existing supervisor agent:

```python
# Example supervisor orchestration
cost_analysis = await invoke_agent("cost-forecast-agent", cost_query)
optimization = await invoke_agent("trusted-advisor-agent", optimization_query)
budget_control = await invoke_agent("budget-management-agent", {
    "action": "recommend_budgets",
    "parameters": {
        "cost_data": cost_analysis,
        "optimization_data": optimization
    }
})
```

### **WebSocket Integration**
Real-time budget alerts can be sent through the WebSocket API:
- Budget threshold breaches
- Action execution notifications
- Performance updates

### **Data Flow**
```
Cost Analysis → Optimization → Budget Recommendations → Automated Controls
     ↓              ↓                    ↓                     ↓
WebSocket Updates ← Real-time Monitoring ← Budget Actions ← Governance
```

## Configuration

### **Environment Variables**
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `BUDGET_STATE_TABLE`: DynamoDB table for state management
- `AWS_ACCOUNT_ID`: AWS account ID for budget operations

### **IAM Permissions Required**
- **AWS Budgets**: Full access for budget management
- **Cost Explorer**: Read access for cost data
- **DynamoDB**: Read/write access to state table
- **CloudWatch Logs**: Write access for logging

## Monitoring and Troubleshooting

### **CloudWatch Logs**
Monitor agent execution in CloudWatch Logs:
```bash
aws logs tail /aws/lambda/budget-management-agent --follow
```

### **Common Issues**
1. **Permission Errors**: Verify IAM roles have required permissions
2. **Budget Limits**: AWS accounts have limits on number of budgets
3. **Action Failures**: Check budget action execution role permissions

### **Performance Metrics**
- Function duration and memory usage
- Budget API call success rates
- Error rates and types

## Security

### **Access Control**
- IAM roles with least privilege access
- Budget action execution role separation
- DynamoDB table encryption at rest

### **Data Protection**
- No sensitive data stored in logs
- State data encrypted in DynamoDB
- Secure API communication

## Future Enhancements

### **Planned Features**
- Machine learning-based budget optimization
- Advanced governance rules engine
- Multi-account budget management
- Custom notification channels
- Budget template library

### **Integration Opportunities**
- AWS Organizations integration
- Service Catalog integration
- AWS Config compliance rules
- Third-party cost management tools

## Support

For issues and questions:
1. Check CloudWatch logs for error details
2. Verify IAM permissions and resource access
3. Review AWS Budgets service limits
4. Consult AWS Budgets API documentation

## Version History

- **v1.0.0**: Initial release with core budget management capabilities
  - Budget creation, monitoring, and analysis
  - Automated actions and governance
  - Integration with FinOps Agent architecture
