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
    Processes long-running jobs and sends real-time updates via WebSocket
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
    """Process individual FinOps job."""
    try:
        job_id = job_data.get('jobId')
        connection_id = job_data.get('connectionId')
        user_id = job_data.get('userId')
        query = job_data.get('query')
        
        logger.info(f"Processing job: {job_id} for user: {user_id}")
        
        # Update job status to processing
        update_job_status(job_id, 'processing', 'Starting FinOps analysis...')
        send_progress_update(connection_id, job_id, 'processing', 'Starting FinOps analysis...', 10)
        
        # Step 1: Invoke Cost Forecast Agent
        send_progress_update(connection_id, job_id, 'processing', 'Analyzing cost data...', 30)
        cost_result = invoke_cost_agent(query)
        
        # Step 2: Invoke Trusted Advisor Agent
        send_progress_update(connection_id, job_id, 'processing', 'Getting optimization recommendations...', 60)
        advisor_result = invoke_advisor_agent(query)
        
        # Step 3: Combine Results
        send_progress_update(connection_id, job_id, 'processing', 'Combining analysis results...', 90)
        combined_result = combine_results(cost_result, advisor_result, query)
        
        # Step 4: Send Final Result
        update_job_status(job_id, 'completed', 'Analysis completed successfully')
        send_final_result(connection_id, job_id, combined_result)
        
        logger.info(f"Job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        update_job_status(job_id, 'failed', f'Job failed: {str(e)}')
        send_error_result(connection_id, job_id, str(e))

def invoke_cost_agent(query: str) -> Dict[str, Any]:
    """Invoke the cost forecast agent."""
    try:
        response = lambda_client.invoke(
            FunctionName='aws-cost-forecast-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        
        payload = json.loads(response['Payload'].read())
        logger.info(f"Cost agent response: {payload}")
        return payload
        
    except Exception as e:
        logger.error(f"Error invoking cost agent: {str(e)}")
        return {"error": f"Cost analysis failed: {str(e)}"}

def invoke_advisor_agent(query: str) -> Dict[str, Any]:
    """Invoke the trusted advisor agent."""
    try:
        response = lambda_client.invoke(
            FunctionName='trusted-advisor-agent-trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        
        payload = json.loads(response['Payload'].read())
        logger.info(f"Advisor agent response: {payload}")
        return payload
        
    except Exception as e:
        logger.error(f"Error invoking advisor agent: {str(e)}")
        return {"error": f"Optimization analysis failed: {str(e)}"}

def combine_results(cost_result: Dict, advisor_result: Dict, query: str) -> Dict[str, Any]:
    """Combine results from both agents."""
    combined_response = "# AWS FinOps Analysis\n\n"
    
    # Add cost analysis
    if "body" in cost_result:
        try:
            cost_body = json.loads(cost_result["body"])
            combined_response += f"## Cost Analysis\n\n{cost_body.get('response', 'No cost data available')}\n\n"
        except:
            combined_response += f"## Cost Analysis\n\n{cost_result.get('body', 'No cost data available')}\n\n"
    
    # Add optimization recommendations
    if "body" in advisor_result:
        try:
            advisor_body = json.loads(advisor_result["body"])
            combined_response += f"## Optimization Recommendations\n\n{advisor_body.get('response', 'No recommendations available')}"
        except:
            combined_response += f"## Optimization Recommendations\n\n{advisor_result.get('body', 'No recommendations available')}"
    
    return {
        "query": query,
        "response": combined_response,
        "agent": "AWS-FinOps-WebSocket-Supervisor",
        "timestamp": int(time.time()),
        "cost_analysis": cost_result,
        "optimization_recommendations": advisor_result
    }

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
