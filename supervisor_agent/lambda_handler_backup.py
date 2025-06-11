import json
import os
import boto3
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def format_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format response with CORS headers for Function URL."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://staging.da7jmqelobr5a.amplifyapp.com",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token,X-Amz-Content-Sha256",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Max-Age": "300"
        },
        "body": json.dumps(body)
    }

def format_options_response() -> Dict[str, Any]:
    """Format OPTIONS response for CORS preflight."""
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "https://staging.da7jmqelobr5a.amplifyapp.com",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token,X-Amz-Content-Sha256",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Max-Age": "300"
        },
        "body": ""
    }

def extract_query(event: dict) -> Optional[str]:
    """Extract query from various input formats."""
    if isinstance(event, dict):
        # Handle API Gateway format
        if "body" in event:
            try:
                body = event["body"]
                if isinstance(body, str):
                    body = json.loads(body)
                return body.get("query")
            except json.JSONDecodeError:
                logger.error("Failed to parse request body")
                return None
        
        # Handle direct Lambda invocation format
        if "query" in event:
            return event["query"]
    
    return None

def get_supervisor_agent():
    """Initialize and return the supervisor agent."""
    lambda_client = boto3.client('lambda')
    
    def supervisor_agent(query: str) -> str:
        """Process query through cost forecast and trusted advisor agents."""
        try:
            # Invoke cost forecast agent
            cost_response = lambda_client.invoke(
                FunctionName='aws-cost-forecast-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            cost_payload = json.loads(cost_response['Payload'].read())
            logger.info(f"Cost forecast response: {cost_payload}")
            
            # Invoke trusted advisor agent
            advisor_response = lambda_client.invoke(
                FunctionName='trusted-advisor-agent-trusted-advisor-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            advisor_payload = json.loads(advisor_response['Payload'].read())
            logger.info(f"Trusted advisor response: {advisor_payload}")
            
            # Combine responses
            combined_response = "# AWS FinOps Analysis\n\n"
            
            # Add cost analysis
            if "body" in cost_payload:
                try:
                    cost_body = json.loads(cost_payload["body"])
                    combined_response += f"## Cost Analysis\n\n{cost_body.get('response', 'No cost data available')}\n\n"
                except:
                    combined_response += f"## Cost Analysis\n\n{cost_payload.get('body', 'No cost data available')}\n\n"
            
            # Add optimization recommendations
            if "body" in advisor_payload:
                try:
                    advisor_body = json.loads(advisor_payload["body"])
                    combined_response += f"## Optimization Recommendations\n\n{advisor_body.get('response', 'No recommendations available')}"
                except:
                    combined_response += f"## Optimization Recommendations\n\n{advisor_payload.get('body', 'No recommendations available')}"
            
            return combined_response
            
        except Exception as e:
            logger.error(f"Error in supervisor agent: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    return supervisor_agent

def handler(event, context):
    """Lambda handler function."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle OPTIONS request for CORS preflight
        request_context = event.get('requestContext', {})
        http_method = request_context.get('http', {}).get('method')
        
        # Check for OPTIONS method in different event formats
        if (http_method == 'OPTIONS' or 
            event.get('httpMethod') == 'OPTIONS' or 
            event.get('requestContext', {}).get('httpMethod') == 'OPTIONS'):
            logger.info("Handling OPTIONS preflight request")
            return format_options_response()
        
        query = extract_query(event)
        
        if not query:
            return format_response(400, {
                "error": "Invalid input",
                "message": "Please provide a query about AWS costs or optimization opportunities.",
                "agent": "AWS-FinOps-Supervisor"
            })
        
        logger.info(f"Processing query: {query}")
        
        # Get the supervisor agent and process the query
        supervisor = get_supervisor_agent()
        response = supervisor(query)
        
        # Format the response
        result = {
            "query": query,
            "response": str(response),
            "agent": "AWS-FinOps-Supervisor",
            "timestamp": context.aws_request_id if context else None
        }
        
        logger.info(f"Supervisor response: {result}")
        return format_response(200, result)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return format_response(500, {
            "error": str(e),
            "message": "An error occurred processing your request",
            "agent": "AWS-FinOps-Supervisor"
        })
