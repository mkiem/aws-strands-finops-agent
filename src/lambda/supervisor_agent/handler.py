"""
Lambda handler for the FinOps Supervisor Agent.
"""

import json
import logging
import os
import traceback
from typing import Dict, Any

from strands import Agent

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the agent outside the handler for better cold start performance
def initialize_agent():
    """Initialize the Strands Agent with appropriate configuration."""
    try:
        # Import tools that will be used by the agent
        from strands_tools import current_time
        
        # Initialize the agent with basic tools
        agent = Agent(
            model_id=os.environ.get("MODEL_ID", "amazon.titan-text-express-v1"),
            region=os.environ.get("AWS_REGION", "us-east-1"),
            temperature=float(os.environ.get("TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("MAX_TOKENS", "4096")),
            tools=[current_time]
        )
        
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Initialize the agent
try:
    finops_agent = initialize_agent()
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    finops_agent = None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for the FinOps Supervisor Agent.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response object
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if agent was initialized successfully
        if finops_agent is None:
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
        response = finops_agent(user_message)
        
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
