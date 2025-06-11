import json
import boto3
import os
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'finops-websocket-connections'))

def format_response(status_code: int, body: str = '') -> Dict[str, Any]:
    """Format WebSocket response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': body
    }

def handler(event, context):
    """
    WebSocket Connection Manager
    Handles connect, disconnect, and default route events
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        if route_key == '$connect':
            return handle_connect(event, connection_id)
        elif route_key == '$disconnect':
            return handle_disconnect(event, connection_id)
        elif route_key == '$default':
            return handle_default(event, connection_id)
        else:
            logger.warning(f"Unknown route: {route_key}")
            return format_response(400, 'Unknown route')
            
    except Exception as e:
        logger.error(f"Error in connection manager: {str(e)}")
        return format_response(500, f'Internal server error: {str(e)}')

def handle_connect(event, connection_id):
    """Handle new WebSocket connection."""
    try:
        # Extract connection info
        request_context = event.get('requestContext', {})
        
        # Store connection in DynamoDB with basic info
        # User authentication will be handled when they send their first message
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'userId': 'pending',  # Will be updated when user authenticates
                'connectedAt': int(time.time()),
                'ttl': int(time.time()) + 3600,  # 1 hour TTL
                'stage': request_context.get('stage', 'prod'),
                'requestId': request_context.get('requestId', '')
            }
        )
        
        logger.info(f"Connection established: {connection_id}")
        return format_response(200, 'Connected')
        
    except Exception as e:
        logger.error(f"Error handling connect: {str(e)}")
        return format_response(500, f'Connection failed: {str(e)}')

def handle_disconnect(event, connection_id):
    """Handle WebSocket disconnection."""
    try:
        # Remove connection from DynamoDB
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        logger.info(f"Connection disconnected: {connection_id}")
        return format_response(200, 'Disconnected')
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {str(e)}")
        return format_response(500, f'Disconnect failed: {str(e)}')

def handle_default(event, connection_id):
    """Handle default route (catch-all for unmatched routes)."""
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', 'unknown')
        
        logger.info(f"Default route called with action: {action} for connection: {connection_id}")
        
        if action == 'authenticate':
            return handle_authenticate(connection_id, body)
        elif action == 'finops_query':
            return handle_finops_query(connection_id, body)
        else:
            return format_response(400, json.dumps({
                'type': 'error',
                'message': f'Unknown action: {action}'
            }))
            
    except Exception as e:
        logger.error(f"Error handling default route: {str(e)}")
        return format_response(500, f'Default route failed: {str(e)}')

def handle_authenticate(connection_id, body):
    """Handle user authentication."""
    try:
        user_id = body.get('userId', 'anonymous')
        username = body.get('username', 'anonymous')
        
        # Update connection with user info
        connections_table.update_item(
            Key={'connectionId': connection_id},
            UpdateExpression='SET userId = :userId, username = :username, authenticatedAt = :timestamp',
            ExpressionAttributeValues={
                ':userId': user_id,
                ':username': username,
                ':timestamp': int(time.time())
            }
        )
        
        logger.info(f"User authenticated: {username} ({user_id}) on connection: {connection_id}")
        
        # Send authentication confirmation
        send_message_to_connection(connection_id, {
            'type': 'authenticated',
            'message': f'Welcome {username}! WebSocket connection established.',
            'userId': user_id,
            'connectionId': connection_id
        })
        
        return format_response(200, 'Authenticated')
        
    except Exception as e:
        logger.error(f"Error handling authentication: {str(e)}")
        return format_response(500, f'Authentication failed: {str(e)}')

def handle_finops_query(connection_id, body):
    """Handle FinOps query - forward to message handler."""
    try:
        # This will be handled by the message handler Lambda
        # For now, just acknowledge receipt
        send_message_to_connection(connection_id, {
            'type': 'query_received',
            'message': 'Your FinOps query has been received and is being processed...',
            'query': body.get('query', '')
        })
        
        return format_response(200, 'Query received')
        
    except Exception as e:
        logger.error(f"Error handling FinOps query: {str(e)}")
        return format_response(500, f'Query handling failed: {str(e)}')

def send_message_to_connection(connection_id, message):
    """Send message to WebSocket connection."""
    try:
        # Initialize API Gateway Management API client
        apigateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT', 
                                      'https://rtswivmeqj.execute-api.us-east-1.amazonaws.com/prod')
        )
        
        apigateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        logger.info(f"Message sent to connection: {connection_id}")
        
    except apigateway_management.exceptions.GoneException:
        logger.warning(f"Connection {connection_id} is gone, removing from database")
        # Remove stale connection
        connections_table.delete_item(Key={'connectionId': connection_id})
        
    except Exception as e:
        logger.error(f"Error sending message to {connection_id}: {str(e)}")
