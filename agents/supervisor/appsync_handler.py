import json
import boto3
import os
import logging
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
appsync_client = boto3.client('appsync')
lambda_client = boto3.client('lambda')

# Environment variables
COST_ANALYSIS_FUNCTION = os.environ.get('COST_ANALYSIS_FUNCTION', 'finops-cost-analysis-agent')
OPTIMIZATION_FUNCTION = os.environ.get('OPTIMIZATION_FUNCTION', 'finops-optimization-agent')
API_ID = os.environ.get('APPSYNC_API_ID')

def handler(event, context):
    """
    Main handler for the Supervisor Agent's AppSync interactions.
    This function processes GraphQL operations from AppSync.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract operation type and field name
    operation_type = event.get('info', {}).get('parentTypeName')
    field_name = event.get('info', {}).get('fieldName')
    
    # Process based on operation type and field
    if operation_type == 'Query':
        return handle_query(field_name, event)
    elif operation_type == 'Mutation':
        return handle_mutation(field_name, event)
    else:
        logger.error(f"Unsupported operation type: {operation_type}")
        return {
            'error': f"Unsupported operation type: {operation_type}"
        }

def handle_query(field_name, event):
    """Handle GraphQL query operations"""
    arguments = event.get('arguments', {})
    
    if field_name == 'getAgentStatus':
        return get_agent_status(arguments.get('agentId'))
    elif field_name == 'getConversationHistory':
        return get_conversation_history(
            arguments.get('limit', 10),
            arguments.get('nextToken')
        )
    else:
        logger.error(f"Unsupported query field: {field_name}")
        return {
            'error': f"Unsupported query field: {field_name}"
        }

def handle_mutation(field_name, event):
    """Handle GraphQL mutation operations"""
    arguments = event.get('arguments', {})
    
    if field_name == 'sendMessage':
        return send_message(arguments.get('input', {}))
    else:
        logger.error(f"Unsupported mutation field: {field_name}")
        return {
            'error': f"Unsupported mutation field: {field_name}"
        }

def get_agent_status(agent_id):
    """Get the status of a specific agent"""
    # In a real implementation, you might check a DynamoDB table or other state storage
    # For now, return a mock response
    return {
        'agentId': agent_id,
        'status': 'IDLE',
        'lastActive': datetime.utcnow().isoformat(),
        'message': 'Agent is ready to process requests'
    }

def get_conversation_history(limit, next_token):
    """Get conversation history with pagination"""
    # In a real implementation, you would query a database like DynamoDB
    # For now, return mock data
    return {
        'items': [
            {
                'id': str(uuid.uuid4()),
                'conversationId': 'conv-123',
                'content': 'How can I optimize my AWS costs?',
                'sender': 'USER',
                'timestamp': datetime.utcnow().isoformat(),
                'userId': 'user-123'
            },
            {
                'id': str(uuid.uuid4()),
                'conversationId': 'conv-123',
                'content': 'I can help you analyze your current costs and suggest optimizations.',
                'sender': 'AGENT',
                'timestamp': datetime.utcnow().isoformat(),
                'agentId': 'supervisor-agent'
            }
        ],
        'nextToken': None  # No more results
    }

def send_message(input_data):
    """Process a new message from the user"""
    message_id = str(uuid.uuid4())
    conversation_id = input_data.get('conversationId', f"conv-{str(uuid.uuid4())}")
    content = input_data.get('content', '')
    user_id = input_data.get('userId', '')
    
    # Log the incoming message
    logger.info(f"New message from user {user_id}: {content}")
    
    # Create message object
    message = {
        'id': message_id,
        'conversationId': conversation_id,
        'content': content,
        'sender': 'USER',
        'timestamp': datetime.utcnow().isoformat(),
        'userId': user_id
    }
    
    # In a real implementation, you would:
    # 1. Store the message in a database
    # 2. Process the message content to determine intent
    # 3. Route to appropriate agent or handle directly
    # 4. Generate and publish a response
    
    # For now, just return the message object
    return message

def publish_to_subscription(subscription_name, data):
    """Publish data to an AppSync subscription"""
    if not API_ID:
        logger.warning("AppSync API ID not configured, skipping subscription publish")
        return
    
    try:
        response = appsync_client.create_graphql_api(
            apiId=API_ID,
            payload=json.dumps({
                'data': data,
                'extensions': {
                    'subscription': {
                        'mqttTopic': subscription_name
                    }
                }
            })
        )
        logger.info(f"Published to subscription {subscription_name}: {response}")
    except Exception as e:
        logger.error(f"Error publishing to subscription: {str(e)}")

def invoke_agent_lambda(function_name, payload):
    """Invoke another agent Lambda function"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        logger.info(f"Invoked Lambda {function_name}: {response}")
        return True
    except Exception as e:
        logger.error(f"Error invoking Lambda {function_name}: {str(e)}")
        return False
