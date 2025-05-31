"""
Lambda handler for the Cost Analysis Agent.
"""

import json
import logging
import os
import traceback
from typing import Dict, Any

import boto3
from strands import Agent, tool

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define custom tools for the Cost Analysis Agent
@tool
def get_cost_data(start_date: str, end_date: str, granularity: str = "DAILY") -> Dict[str, Any]:
    """
    Get AWS cost data for a specified time period.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Data granularity (DAILY, MONTHLY, or HOURLY)
        
    Returns:
        Cost data for the specified period
    """
    try:
        ce_client = boto3.client('ce', region_name=os.environ.get("AWS_REGION", "us-east-1"))
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        return response
    except Exception as e:
        logger.error(f"Error getting cost data: {str(e)}")
        return {"error": str(e)}

@tool
def get_cost_forecast(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Get AWS cost forecast for a specified time period.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Cost forecast for the specified period
    """
    try:
        ce_client = boto3.client('ce', region_name=os.environ.get("AWS_REGION", "us-east-1"))
        
        response = ce_client.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Metric='UNBLENDED_COST',
            Granularity='MONTHLY'
        )
        
        return response
    except Exception as e:
        logger.error(f"Error getting cost forecast: {str(e)}")
        return {"error": str(e)}

# Initialize the agent outside the handler for better cold start performance
def initialize_agent():
    """Initialize the Strands Agent with appropriate configuration."""
    try:
        # Import tools that will be used by the agent
        from strands_tools import current_time
        
        # Initialize the agent with cost analysis tools
        agent = Agent(
            model_id=os.environ.get("MODEL_ID", "amazon.titan-text-express-v1"),
            region=os.environ.get("AWS_REGION", "us-east-1"),
            temperature=float(os.environ.get("TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("MAX_TOKENS", "4096")),
            tools=[current_time, get_cost_data, get_cost_forecast]
        )
        
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Initialize the agent
try:
    cost_analysis_agent = initialize_agent()
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    cost_analysis_agent = None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for the Cost Analysis Agent.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response object
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if agent was initialized successfully
        if cost_analysis_agent is None:
            raise Exception("Agent failed to initialize")
        
        # Extract the user message from the event
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        user_message = body.get('message', '')
        session_id = body.get('session_id', '')
        
        if not user_message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No message provided'})
            }
        
        logger.info(f"Processing message: {user_message}")
        
        # Process the message with the agent
        response = cost_analysis_agent(user_message)
        
        # Return the response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': response,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error processing request: {str(e)}"
            })
        }
