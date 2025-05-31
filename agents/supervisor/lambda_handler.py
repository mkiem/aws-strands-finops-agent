"""
AWS Lambda handler for the FinOps Supervisor Agent.

This module provides the AWS Lambda handler function that processes
incoming requests and invokes the FinOps Supervisor Agent.
"""

import os
import json
import logging
from typing import Dict, Any

# Import the Supervisor Agent
from .agent import FinOpsSupervisorAgent

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the agent (done outside the handler for better cold start performance)
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
supervisor_agent = FinOpsSupervisorAgent(model_id=MODEL_ID)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function for the FinOps Supervisor Agent.
    
    Args:
        event: The event dict containing the request parameters
        context: The Lambda context object
        
    Returns:
        Dict containing the agent's response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if this is an AppSync request
        if 'info' in event:
            return handle_appsync_request(event, context)
        
        # Check if this is an agent-to-agent message
        if 'message' in event and isinstance(event['message'], dict):
            return handle_agent_message(event, context)
        
        # Otherwise, assume it's a direct Lambda invocation
        return handle_direct_invocation(event, context)
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f"Error processing request: {str(e)}"
            })
        }

def handle_appsync_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle requests coming from AppSync.
    
    Args:
        event: The AppSync event
        context: The Lambda context object
        
    Returns:
        Dict containing the response for AppSync
    """
    # Extract operation type and field name
    operation_type = event.get('info', {}).get('parentTypeName')
    field_name = event.get('info', {}).get('fieldName')
    
    if operation_type == 'Mutation' and field_name == 'sendMessage':
        # Process a new message
        input_data = event.get('arguments', {}).get('input', {})
        user_message = input_data.get('content', '')
        conversation_id = input_data.get('conversationId')
        user_id = input_data.get('userId')
        
        # Process the message with the agent
        result = supervisor_agent.process_message(
            user_message=user_message,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        # Format the response for AppSync
        return {
            'id': result.get('conversation_id', ''),
            'conversationId': conversation_id,
            'content': result.get('message', ''),
            'sender': 'AGENT',
            'timestamp': result.get('timestamp', ''),
            'agentId': 'supervisor-agent',
            'userId': user_id
        }
    
    elif operation_type == 'Query' and field_name == 'getConversationHistory':
        # Get conversation history
        limit = event.get('arguments', {}).get('limit', 10)
        next_token = event.get('arguments', {}).get('nextToken')
        
        # For now, return a mock response
        # In a real implementation, you would query a database
        return {
            'items': [
                {
                    'id': '1',
                    'conversationId': 'conv-123',
                    'content': 'How can I optimize my AWS costs?',
                    'sender': 'USER',
                    'timestamp': '2025-05-31T00:00:00Z',
                    'userId': 'user-123'
                },
                {
                    'id': '2',
                    'conversationId': 'conv-123',
                    'content': 'I can help you analyze your current costs and suggest optimizations.',
                    'sender': 'AGENT',
                    'timestamp': '2025-05-31T00:00:05Z',
                    'agentId': 'supervisor-agent',
                    'userId': 'user-123'
                }
            ],
            'nextToken': None
        }
    
    elif operation_type == 'Query' and field_name == 'getAgentStatus':
        # Get agent status
        agent_id = event.get('arguments', {}).get('agentId')
        
        # Get active agents
        active_agents = supervisor_agent.comm_handler.get_active_agents()
        
        # Find the requested agent
        agent_info = next((a for a in active_agents if a['agent_id'] == agent_id), None)
        
        if agent_info:
            return {
                'agentId': agent_info['agent_id'],
                'status': 'IDLE',  # For now, just return IDLE
                'lastActive': agent_info['last_heartbeat'],
                'message': f"Agent {agent_info['name']} is ready"
            }
        else:
            return {
                'agentId': agent_id,
                'status': 'OFFLINE',
                'lastActive': None,
                'message': f"Agent {agent_id} is not available"
            }
    
    else:
        logger.error(f"Unsupported operation: {operation_type}.{field_name}")
        return {
            'error': f"Unsupported operation: {operation_type}.{field_name}"
        }

def handle_agent_message(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle messages from other agents.
    
    Args:
        event: The event containing the agent message
        context: The Lambda context object
        
    Returns:
        Dict containing the response
    """
    message_data = event.get('message', {})
    
    # Process the message with the agent
    result = supervisor_agent.process_agent_message(message_data)
    
    return {
        'message': result
    }

def handle_direct_invocation(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle direct Lambda invocations.
    
    Args:
        event: The Lambda event
        context: The Lambda context object
        
    Returns:
        Dict containing the agent's response
    """
    # Extract parameters from the event
    user_message = event.get('message', '')
    conversation_id = event.get('conversation_id')
    user_id = event.get('user_id')
    
    # Process the message with the agent
    result = supervisor_agent.process_message(
        user_message=user_message,
        conversation_id=conversation_id,
        user_id=user_id
    )
    
    return result
