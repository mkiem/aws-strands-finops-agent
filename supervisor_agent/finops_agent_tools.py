"""
FinOps Agent Tools - Implementing Agents as Tools pattern with Strands SDK
"""
import json
import boto3
import logging
from typing import Dict, Any
from strands import tool

logger = logging.getLogger(__name__)

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

@tool
def cost_forecast_agent(query: str) -> str:
    """
    Analyze AWS costs, spending trends, and provide detailed cost forecasting.
    
    Use this tool when you need to:
    - Analyze current AWS spending patterns
    - Identify cost trends and patterns over time
    - Provide cost breakdowns by service
    - Forecast future costs based on historical data
    - Analyze spending anomalies or changes
    
    Args:
        query: A cost analysis question or request for cost data
        
    Returns:
        Detailed cost analysis and forecasting information
    """
    try:
        logger.info(f"Invoking cost_forecast_agent with query: {query}")
        
        response = lambda_client.invoke(
            FunctionName='aws-cost-forecast-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({'query': query})
        )
        
        payload = json.loads(response['Payload'].read())
        
        if 'errorMessage' in payload:
            logger.error(f"Cost forecast agent error: {payload['errorMessage']}")
            return f"Error from cost forecast agent: {payload['errorMessage']}"
        
        # Extract the response from the agent result
        if isinstance(payload, dict) and 'response' in payload:
            return payload['response']
        elif isinstance(payload, str):
            return payload
        else:
            return str(payload)
            
    except Exception as e:
        logger.error(f"Error invoking cost_forecast_agent: {str(e)}")
        return f"Error analyzing costs: {str(e)}"

@tool
def trusted_advisor_agent(query: str) -> str:
    """
    Provide AWS cost optimization recommendations and savings opportunities.
    
    Use this tool when you need to:
    - Get specific cost optimization recommendations
    - Identify savings opportunities across AWS services
    - Analyze resource utilization and efficiency
    - Provide actionable optimization steps
    - Estimate potential cost savings
    
    Args:
        query: A cost optimization question or request for recommendations
        
    Returns:
        Detailed cost optimization recommendations and savings opportunities
    """
    try:
        logger.info(f"Invoking trusted_advisor_agent with query: {query}")
        
        response = lambda_client.invoke(
            FunctionName='trusted-advisor-agent-trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({'query': query})
        )
        
        payload = json.loads(response['Payload'].read())
        
        if 'errorMessage' in payload:
            logger.error(f"Trusted advisor agent error: {payload['errorMessage']}")
            return f"Error from trusted advisor agent: {payload['errorMessage']}"
        
        # Extract the response from the agent result
        if isinstance(payload, dict) and 'response' in payload:
            return payload['response']
        elif isinstance(payload, str):
            return payload
        else:
            return str(payload)
            
    except Exception as e:
        logger.error(f"Error invoking trusted_advisor_agent: {str(e)}")
        return f"Error getting optimization recommendations: {str(e)}"

@tool
def budget_management_agent(query: str) -> str:
    """
    Provide AWS budget planning, cost controls, and financial governance recommendations.
    
    Use this tool when you need to:
    - Create budget recommendations and planning strategies
    - Set up cost controls and spending limits
    - Provide financial governance guidance
    - Analyze budget performance and variances
    - Recommend budget structures and thresholds
    
    Args:
        query: A budget planning or cost control question
        
    Returns:
        Budget planning recommendations and cost control strategies
    """
    try:
        logger.info(f"Invoking budget_management_agent with query: {query}")
        
        response = lambda_client.invoke(
            FunctionName='budget-management-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({'query': query})
        )
        
        payload = json.loads(response['Payload'].read())
        
        if 'errorMessage' in payload:
            logger.error(f"Budget management agent error: {payload['errorMessage']}")
            return f"Error from budget management agent: {payload['errorMessage']}"
        
        # Extract the response from the agent result
        if isinstance(payload, dict) and 'response' in payload:
            return payload['response']
        elif isinstance(payload, str):
            return payload
        else:
            return str(payload)
            
    except Exception as e:
        logger.error(f"Error invoking budget_management_agent: {str(e)}")
        return f"Error getting budget recommendations: {str(e)}"
