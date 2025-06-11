import json
import boto3
import os
import uuid
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
apigateway_management = boto3.client('apigatewaymanagementapi', 
                                   endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT'))

jobs_table = dynamodb.Table(os.environ.get('JOBS_TABLE', 'finops-websocket-jobs'))
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'finops-websocket-connections'))

def handler(event, context):
    """
    WebSocket Message Handler
    Processes WebSocket messages and queues long-running jobs
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle direct WebSocket route invocation
        if 'requestContext' in event and 'routeKey' in event['requestContext']:
            return handle_websocket_message(event, context)
        
        # Handle SQS message processing
        for record in event.get('Records', []):
            message_body = json.loads(record['body'])
            process_message(message_body, context)
            
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def handle_websocket_message(event, context):
    """Handle direct WebSocket message."""
    try:
        connection_id = event.get('requestContext', {}).get('connectionId')
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        logger.info(f"WebSocket message: {action} from connection: {connection_id}")
        
        if action == 'finops_query':
            return handle_finops_query_direct(connection_id, body, context)
        else:
            return {'statusCode': 400, 'body': f'Unknown action: {action}'}
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def handle_finops_query_direct(connection_id: str, body: Dict, context):
    """Handle FinOps query directly from WebSocket."""
    try:
        query = body.get('query')
        user_id = body.get('userId', 'anonymous')
        username = body.get('username', 'anonymous')
        
        if not query:
            send_error_to_client(connection_id, "Query is required")
            return {'statusCode': 400, 'body': 'Query is required'}
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Store job in DynamoDB
        jobs_table.put_item(
            Item={
                'jobId': job_id,
                'connectionId': connection_id,
                'userId': user_id,
                'username': username,
                'query': query,
                'status': 'queued',
                'createdAt': int(time.time()),
                'ttl': int(time.time()) + 3600  # 1 hour TTL
            }
        )
        
        # Send acknowledgment to client
        send_message_to_client(connection_id, {
            'type': 'job_queued',
            'jobId': job_id,
            'message': 'Your FinOps query has been queued for processing...',
            'query': query,
            'progress': 5
        })
        
        # Queue job for background processing
        sqs.send_message(
            QueueUrl=os.environ.get('PROCESSING_QUEUE_URL'),
            MessageBody=json.dumps({
                'jobId': job_id,
                'connectionId': connection_id,
                'userId': user_id,
                'username': username,
                'query': query,
                'action': 'process_finops_query'
            }),
            MessageAttributes={
                'jobType': {
                    'StringValue': 'finops_query',
                    'DataType': 'String'
                }
            }
        )
        
        logger.info(f"FinOps query queued: {job_id} for user: {username}")
        return {'statusCode': 200, 'body': 'Query queued'}
        
    except Exception as e:
        logger.error(f"Error handling FinOps query: {str(e)}")
        send_error_to_client(connection_id, f"Query processing error: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def process_message(message: Dict[str, Any], context):
    """Process individual WebSocket message from SQS."""
    try:
        connection_id = message.get('connectionId')
        user_id = message.get('userId')
        query = message.get('query')
        action = message.get('action')
        
        if action == 'process_finops_query':
            handle_finops_query(connection_id, user_id, query, context)
        else:
            send_error_to_client(connection_id, f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        send_error_to_client(connection_id, f"Processing error: {str(e)}")

def handle_finops_query(connection_id: str, user_id: str, query: str, context):
    """Handle FinOps query request (legacy SQS processing)."""
    try:
        # This is now handled directly in handle_finops_query_direct
        # This function is kept for backward compatibility
        logger.info(f"Legacy SQS processing for query: {query}")
        
    except Exception as e:
        logger.error(f"Error handling FinOps query: {str(e)}")
        send_error_to_client(connection_id, f"Query processing error: {str(e)}")

def send_message_to_client(connection_id: str, message: Dict[str, Any]):
    """Send message to WebSocket client."""
    try:
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

def send_error_to_client(connection_id: str, error_message: str):
    """Send error message to WebSocket client."""
    send_message_to_client(connection_id, {
        'type': 'error',
        'message': error_message,
        'timestamp': int(time.time())
    })
