# Agent-to-Agent Communication Architecture for FinOps System

## Overview

This document outlines the architecture for implementing agent-to-agent communication in our FinOps system using the Strands framework. Based on our successful deployment of the Trusted Advisor Agent, we can extend this to create a multi-agent ecosystem where specialized agents collaborate to provide comprehensive cost optimization insights.

## Current State

### Successfully Deployed
- **Trusted Advisor Agent**: ✅ Fully functional Strands-based agent
  - Function ARN: `arn:aws:lambda:us-east-1:837882009522:function:trusted-advisor-agent-trusted-advisor-agent`
  - Status: Retrieving 5 cost optimization recommendations worth $247.97 monthly savings
  - API Integration: Working with both new TrustedAdvisor API and legacy Support API
  - Tools: 3 specialized tools for Trusted Advisor integration

### Existing Infrastructure
- **Web UI**: React-based frontend deployed on AWS Amplify
- **API Gateway**: REST API for agent communication
- **S3 Bucket**: `finops-deployment-packages-062025` for deployment packages
- **Authentication**: Amazon Cognito integration

## Agent-to-Agent Communication Patterns

### 1. Orchestration Pattern (Supervisor-Driven)

The Supervisor Agent acts as the central coordinator, managing task distribution and result aggregation.

```python
# Supervisor Agent Implementation
from strands import Agent, tool
import json
import boto3

@tool
def coordinate_cost_analysis(analysis_type: str = "comprehensive") -> str:
    """
    Coordinate a comprehensive cost analysis across multiple specialized agents.
    
    Args:
        analysis_type: Type of analysis (comprehensive, targeted, emergency)
    
    Returns:
        Consolidated analysis results
    """
    # Invoke Trusted Advisor Agent
    ta_results = invoke_agent("trusted-advisor-agent", {
        "query": "Get all cost optimization recommendations with exact savings amounts"
    })
    
    # Trigger Cost Explorer Agent (when implemented)
    ce_results = invoke_agent("cost-explorer-agent", {
        "query": "Analyze spending trends for the resources identified in Trusted Advisor",
        "context": ta_results
    })
    
    # Coordinate Rightsizing Agent (when implemented)
    rs_results = invoke_agent("rightsizing-agent", {
        "query": "Provide rightsizing recommendations for underutilized resources",
        "trusted_advisor_data": ta_results,
        "cost_trends": ce_results
    })
    
    return consolidate_results(ta_results, ce_results, rs_results)

def invoke_agent(function_name: str, payload: dict) -> dict:
    """Invoke another Lambda-based agent and return results."""
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=function_name,
        Payload=json.dumps(payload)
    )
    return json.loads(response['Payload'].read())

supervisor_agent = Agent(
    system_prompt="""
    You are a FinOps Supervisor Agent that coordinates multiple specialized agents.
    Your role is to orchestrate comprehensive cost optimization analysis by:
    1. Delegating specific tasks to specialized agents
    2. Aggregating and synthesizing results
    3. Providing unified recommendations
    4. Ensuring data consistency across agents
    """,
    tools=[coordinate_cost_analysis]
)
```

### 2. Event-Driven Pattern (Asynchronous Communication)

Agents communicate through AWS EventBridge for loose coupling and scalability.

```python
# Event Publishing (from Trusted Advisor Agent)
import boto3

def publish_cost_findings(findings: dict):
    """Publish cost optimization findings to EventBridge."""
    eventbridge = boto3.client('events')
    
    eventbridge.put_events(
        Entries=[
            {
                'Source': 'finops.trusted-advisor-agent',
                'DetailType': 'Cost Optimization Findings',
                'Detail': json.dumps({
                    'total_savings': findings.get('total_savings', 0),
                    'recommendation_count': findings.get('total_count', 0),
                    'high_impact_resources': findings.get('high_impact', []),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        ]
    )

# Event Consumption (in Cost Explorer Agent)
@tool
def process_trusted_advisor_event(event_data: str) -> str:
    """Process incoming Trusted Advisor findings and perform deep analysis."""
    findings = json.loads(event_data)
    
    # Perform cost trend analysis for identified resources
    cost_analysis = analyze_cost_trends(findings['high_impact_resources'])
    
    # Store results for other agents to access
    store_analysis_results(cost_analysis)
    
    return json.dumps(cost_analysis)
```

### 3. Shared Context Pattern (S3-Based Data Sharing)

Agents share context and intermediate results through S3 for persistent communication.

```python
# Context Storage
import boto3
import json
from datetime import datetime

class AgentContextManager:
    def __init__(self, bucket_name: str):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name
    
    def store_context(self, agent_name: str, context_type: str, data: dict):
        """Store agent context in S3 for other agents to access."""
        key = f"agent-context/{agent_name}/{context_type}/{datetime.utcnow().isoformat()}.json"
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(data),
            ContentType='application/json',
            Metadata={
                'agent': agent_name,
                'context_type': context_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return key
    
    def get_latest_context(self, agent_name: str, context_type: str) -> dict:
        """Retrieve the latest context from another agent."""
        prefix = f"agent-context/{agent_name}/{context_type}/"
        
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=1
        )
        
        if 'Contents' in response:
            latest_key = response['Contents'][0]['Key']
            obj = self.s3.get_object(Bucket=self.bucket, Key=latest_key)
            return json.loads(obj['Body'].read())
        
        return {}

# Usage in agents
context_manager = AgentContextManager('finops-agent-context-bucket')

@tool
def share_trusted_advisor_results(results: str) -> str:
    """Share Trusted Advisor results with other agents."""
    data = json.loads(results)
    
    context_manager.store_context(
        agent_name='trusted-advisor-agent',
        context_type='cost-recommendations',
        data=data
    )
    
    return "Results shared successfully"

@tool
def get_trusted_advisor_context() -> str:
    """Retrieve shared Trusted Advisor context."""
    context = context_manager.get_latest_context(
        agent_name='trusted-advisor-agent',
        context_type='cost-recommendations'
    )
    
    return json.dumps(context)
```

### 4. State Synchronization Pattern (DynamoDB)

Agents maintain synchronized state through DynamoDB for consistency and coordination.

```python
# Agent State Management
import boto3
from datetime import datetime

class AgentStateManager:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def update_agent_state(self, agent_name: str, state_data: dict):
        """Update agent state in DynamoDB."""
        self.table.put_item(
            Item={
                'agent_name': agent_name,
                'timestamp': datetime.utcnow().isoformat(),
                'state': state_data,
                'ttl': int((datetime.utcnow().timestamp() + 86400))  # 24 hour TTL
            }
        )
    
    def get_agent_state(self, agent_name: str) -> dict:
        """Get current agent state."""
        response = self.table.get_item(
            Key={'agent_name': agent_name}
        )
        
        return response.get('Item', {}).get('state', {})
    
    def get_all_agent_states(self) -> dict:
        """Get states of all agents for coordination."""
        response = self.table.scan()
        
        states = {}
        for item in response['Items']:
            states[item['agent_name']] = item['state']
        
        return states

# Usage in Supervisor Agent
state_manager = AgentStateManager('finops-agent-states')

@tool
def check_agent_readiness() -> str:
    """Check if all required agents are ready for coordinated analysis."""
    states = state_manager.get_all_agent_states()
    
    required_agents = [
        'trusted-advisor-agent',
        'cost-explorer-agent',
        'rightsizing-agent'
    ]
    
    ready_agents = []
    for agent in required_agents:
        if agent in states and states[agent].get('status') == 'ready':
            ready_agents.append(agent)
    
    return json.dumps({
        'ready_agents': ready_agents,
        'total_required': len(required_agents),
        'all_ready': len(ready_agents) == len(required_agents)
    })
```

## Implementation Roadmap

### Phase 1: Extend Current Trusted Advisor Agent
1. **Add Communication Tools**: Extend the existing Trusted Advisor Agent with tools for:
   - Publishing events to EventBridge
   - Storing results in S3
   - Updating state in DynamoDB

2. **Modify Lambda Handler**: Update the current `lambda_handler.py` to include communication capabilities

### Phase 2: Implement Supervisor Agent
1. **Create Supervisor Agent**: New Strands-based agent that orchestrates other agents
2. **Deploy Infrastructure**: EventBridge rules, S3 bucket, DynamoDB table
3. **Update API Gateway**: Route requests through Supervisor Agent

### Phase 3: Add Specialized Agents
1. **Cost Explorer Agent**: Analyze spending trends and patterns
2. **Rightsizing Agent**: Provide EC2 instance rightsizing recommendations
3. **Budget Agent**: Analyze budget impact and forecasting

### Phase 4: Advanced Features
1. **Agent Discovery**: Dynamic agent registration and discovery
2. **Workflow Orchestration**: Complex multi-step workflows
3. **Error Handling**: Robust error handling and retry mechanisms
4. **Monitoring**: Comprehensive monitoring and alerting

## Benefits of This Architecture

### 1. Scalability
- Each agent can be scaled independently
- New agents can be added without modifying existing ones
- Event-driven architecture supports high throughput

### 2. Maintainability
- Clear separation of concerns
- Each agent has a specific responsibility
- Easier to test and debug individual components

### 3. Flexibility
- Multiple communication patterns for different use cases
- Agents can work synchronously or asynchronously
- Easy to modify or replace individual agents

### 4. Reliability
- Fault isolation between agents
- Retry mechanisms and error handling
- State persistence for recovery

## Integration with Existing System

### Current Trusted Advisor Agent Enhancement
```python
# Add to existing lambda_handler.py
@tool
def publish_findings_to_other_agents(findings: str) -> str:
    """Publish Trusted Advisor findings to other agents via EventBridge."""
    try:
        findings_data = json.loads(findings)
        
        # Publish to EventBridge
        eventbridge = boto3.client('events')
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'finops.trusted-advisor-agent',
                    'DetailType': 'Cost Optimization Findings',
                    'Detail': findings
                }
            ]
        )
        
        # Store in S3 for other agents
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='finops-agent-context',
            Key=f'trusted-advisor/{datetime.utcnow().isoformat()}.json',
            Body=findings,
            ContentType='application/json'
        )
        
        return "Findings published successfully to other agents"
        
    except Exception as e:
        logger.error(f"Error publishing findings: {str(e)}")
        return f"Error publishing findings: {str(e)}"

# Add the new tool to the existing agent
agent = Agent(
    system_prompt=TRUSTED_ADVISOR_SYSTEM_PROMPT,
    tools=[
        get_trusted_advisor_recommendations,
        get_recommendation_details,
        get_cost_optimization_summary,
        publish_findings_to_other_agents  # New tool
    ]
)
```

## Next Steps

1. **Review and Approve Architecture**: Validate the proposed communication patterns
2. **Create Infrastructure**: Deploy EventBridge, S3 bucket, and DynamoDB table
3. **Enhance Trusted Advisor Agent**: Add communication tools to existing agent
4. **Implement Supervisor Agent**: Create the orchestration layer
5. **Test Integration**: Validate agent-to-agent communication
6. **Deploy Additional Agents**: Implement Cost Explorer and Rightsizing agents

This architecture leverages the successful Trusted Advisor Agent as the foundation and extends it with robust communication patterns to create a comprehensive multi-agent FinOps system.
