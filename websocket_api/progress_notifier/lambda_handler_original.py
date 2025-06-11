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
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
apigateway_management = boto3.client('apigatewaymanagementapi', 
                                   endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT'))

jobs_table = dynamodb.Table(os.environ.get('JOBS_TABLE', 'finops-websocket-jobs'))

def handler(event, context):
    """
    Background Processor for FinOps Queries
    Processes long-running jobs via Supervisor Agent and sends real-time updates via WebSocket
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process SQS messages
        for record in event.get('Records', []):
            message_body = json.loads(record['body'])
            process_job(message_body, context)
            
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in background processor: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def process_job(job_data: Dict[str, Any], context):
    """Process individual FinOps job using Supervisor Agent."""
    try:
        job_id = job_data.get('jobId')
        connection_id = job_data.get('connectionId')
        user_id = job_data.get('userId')
        query = job_data.get('query')
        
        logger.info(f"Processing job: {job_id} for user: {user_id}")
        
        # Update job status to processing
        update_job_status(job_id, 'processing', 'Starting FinOps analysis...')
        send_progress_update(connection_id, job_id, 'processing', 'Starting FinOps analysis...', 10)
        
        # Step 1: Route query through Supervisor Agent (intelligent routing)
        send_progress_update(connection_id, job_id, 'processing', 'Analyzing query and routing to appropriate agents...', 30)
        supervisor_result = invoke_supervisor_agent(query)
        
        # Step 2: Process result
        send_progress_update(connection_id, job_id, 'processing', 'Processing analysis results...', 80)
        final_result = process_supervisor_result(supervisor_result, query)
        
        # Step 3: Send Final Result
        update_job_status(job_id, 'completed', 'Analysis completed successfully')
        send_final_result(connection_id, job_id, final_result)
        
        logger.info(f"Job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        update_job_status(job_id, 'failed', f'Job failed: {str(e)}')
        send_error_result(connection_id, job_id, str(e))

def invoke_supervisor_agent(query: str) -> Dict[str, Any]:
    """Invoke the Supervisor Agent for intelligent routing."""
    try:
        logger.info(f"Invoking Supervisor Agent with query: {query}")
        
        response = lambda_client.invoke(
            FunctionName='AWS-FinOps-Agent',  # Supervisor Agent function name
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        
        payload = json.loads(response['Payload'].read())
        logger.info(f"Supervisor Agent response: {payload}")
        return payload
        
    except Exception as e:
        logger.error(f"Error invoking Supervisor Agent: {str(e)}")
        return {"error": f"Supervisor Agent failed: {str(e)}"}

def process_supervisor_result(supervisor_result: Dict, query: str) -> Dict[str, Any]:
    """Process the Supervisor Agent result."""
    try:
        # Handle different response formats from Supervisor Agent
        if "body" in supervisor_result:
            try:
                # Parse JSON body if it's a string
                if isinstance(supervisor_result["body"], str):
                    body_data = json.loads(supervisor_result["body"])
                else:
                    body_data = supervisor_result["body"]
                
                return {
                    "query": query,
                    "response": body_data.get('response', 'No response available'),
                    "agent": body_data.get('agent', 'AWS-FinOps-WebSocket-Supervisor'),
                    "timestamp": body_data.get('timestamp', int(time.time())),
                    "routing_info": extract_routing_info(body_data.get('response', '')),
                    "source": "supervisor_agent_via_websocket"
                }
                
            except json.JSONDecodeError:
                # Handle non-JSON body
                return {
                    "query": query,
                    "response": supervisor_result.get("body", "No response available"),
                    "agent": "AWS-FinOps-WebSocket-Supervisor",
                    "timestamp": int(time.time()),
                    "source": "supervisor_agent_via_websocket"
                }
        
        # Handle direct response format
        elif "response" in supervisor_result:
            return {
                "query": query,
                "response": supervisor_result.get('response', 'No response available'),
                "agent": supervisor_result.get('agent', 'AWS-FinOps-WebSocket-Supervisor'),
                "timestamp": supervisor_result.get('timestamp', int(time.time())),
                "routing_info": extract_routing_info(supervisor_result.get('response', '')),
                "source": "supervisor_agent_via_websocket"
            }
        
        # Handle error cases
        elif "error" in supervisor_result:
            return {
                "query": query,
                "response": f"Error: {supervisor_result['error']}",
                "agent": "AWS-FinOps-WebSocket-Supervisor",
                "timestamp": int(time.time()),
                "source": "supervisor_agent_via_websocket",
                "error": True
            }
        
        # Fallback for unexpected formats
        else:
            return {
                "query": query,
                "response": json.dumps(supervisor_result, indent=2),
                "agent": "AWS-FinOps-WebSocket-Supervisor",
                "timestamp": int(time.time()),
                "source": "supervisor_agent_via_websocket"
            }
            
    except Exception as e:
        logger.error(f"Error processing supervisor result: {str(e)}")
        return {
            "query": query,
            "response": f"Error processing response: {str(e)}",
            "agent": "AWS-FinOps-WebSocket-Supervisor",
            "timestamp": int(time.time()),
            "source": "supervisor_agent_via_websocket",
            "error": True
        }

def extract_routing_info(response_text: str) -> Dict[str, Any]:
    """Extract routing information from the response text."""
    try:
        routing_info = {}
        
        # Look for routing indicators in the response
        if "🎯 Routing to cost_forecast" in response_text:
            routing_info["routed_to"] = "cost_forecast"
            routing_info["agent_used"] = "AWS Cost Forecast Agent"
        elif "🎯 Routing to trusted_advisor" in response_text:
            routing_info["routed_to"] = "trusted_advisor"
            routing_info["agent_used"] = "AWS Trusted Advisor Agent"
        elif "🎯 Routing to both" in response_text:
            routing_info["routed_to"] = "both"
            routing_info["agent_used"] = "Both Cost Forecast and Trusted Advisor Agents"
        else:
            routing_info["routed_to"] = "unknown"
            routing_info["agent_used"] = "Unknown routing"
        
        return routing_info
        
    except Exception as e:
        logger.error(f"Error extracting routing info: {str(e)}")
        return {"routed_to": "error", "agent_used": "Error extracting routing info"}

def update_job_status(job_id: str, status: str, message: str):
    """Update job status in DynamoDB."""
    try:
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, #message = :message, updatedAt = :timestamp',
            ExpressionAttributeNames={
                '#status': 'status',
                '#message': 'message'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':message': message,
                ':timestamp': int(time.time())
            }
        )
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")

def send_progress_update(connection_id: str, job_id: str, status: str, message: str, progress: int):
    """Send progress update to WebSocket client."""
    try:
        send_message_to_client(connection_id, {
            'type': 'progress_update',
            'jobId': job_id,
            'status': status,
            'message': message,
            'progress': progress,
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error sending progress update: {str(e)}")

def send_final_result(connection_id: str, job_id: str, result: Dict[str, Any]):
    """Send final result to WebSocket client."""
    try:
        send_message_to_client(connection_id, {
            'type': 'job_completed',
            'jobId': job_id,
            'result': result,
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error sending final result: {str(e)}")

def send_error_result(connection_id: str, job_id: str, error_message: str):
    """Send error result to WebSocket client."""
    try:
        send_message_to_client(connection_id, {
            'type': 'job_failed',
            'jobId': job_id,
            'error': error_message,
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error sending error result: {str(e)}")

def send_message_to_client(connection_id: str, message: Dict[str, Any]):
    """Send message to WebSocket client."""
    try:
        apigateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        logger.info(f"Message sent to connection: {connection_id}")
        
    except apigateway_management.exceptions.GoneException:
        logger.warning(f"Connection {connection_id} is gone")
        
    except Exception as e:
        logger.error(f"Error sending message to {connection_id}: {str(e)}")
