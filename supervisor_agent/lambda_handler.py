import json
import os
import boto3
import logging
from typing import Dict, Any, Optional, List
from llm_router_simple import LLMQueryRouter

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
    """Initialize and return the intelligent supervisor agent with LLM-based routing."""
    lambda_client = boto3.client('lambda')
    router = LLMQueryRouter()
    
    def invoke_cost_forecast_agent(query: str) -> Dict[str, Any]:
        """Invoke the AWS Cost Forecast Agent."""
        try:
            logger.info(f"Invoking cost forecast agent with query: {query}")
            response = lambda_client.invoke(
                FunctionName='aws-cost-forecast-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            payload = json.loads(response['Payload'].read())
            logger.info(f"Cost forecast response: {payload}")
            return payload
            
        except Exception as e:
            logger.error(f"Error invoking cost forecast agent: {str(e)}")
            return {"error": f"Cost forecast agent error: {str(e)}"}
    
    def invoke_trusted_advisor_agent(query: str) -> Dict[str, Any]:
        """Invoke the Trusted Advisor Agent."""
        try:
            logger.info(f"Invoking trusted advisor agent with query: {query}")
            response = lambda_client.invoke(
                FunctionName='trusted-advisor-agent-trusted-advisor-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            payload = json.loads(response['Payload'].read())
            logger.info(f"Trusted advisor response: {payload}")
            return payload
            
        except Exception as e:
            logger.error(f"Error invoking trusted advisor agent: {str(e)}")
            return {"error": f"Trusted advisor agent error: {str(e)}"}
    
    def get_comprehensive_finops_analysis(query: str, routing_explanation: str) -> str:
        """Get comprehensive analysis from both agents."""
        logger.info(f"Performing comprehensive analysis for query: {query}")
        
        # Invoke both agents
        cost_response = invoke_cost_forecast_agent(query)
        advisor_response = invoke_trusted_advisor_agent(query)
        
        # Combine responses
        combined_response = f"# 🏦 Comprehensive AWS FinOps Analysis\n\n{routing_explanation}\n\n"
        
        # Add cost analysis
        if "body" in cost_response and not cost_response.get("error"):
            try:
                cost_body = json.loads(cost_response["body"]) if isinstance(cost_response["body"], str) else cost_response["body"]
                combined_response += f"## 📊 Cost Analysis\n\n{cost_body.get('response', 'No cost data available')}\n\n"
            except:
                combined_response += f"## 📊 Cost Analysis\n\n{cost_response.get('body', 'No cost data available')}\n\n"
        elif cost_response.get("error"):
            combined_response += f"## 📊 Cost Analysis\n\n⚠️ {cost_response['error']}\n\n"
        
        # Add optimization recommendations
        if "body" in advisor_response and not advisor_response.get("error"):
            try:
                advisor_body = json.loads(advisor_response["body"]) if isinstance(advisor_response["body"], str) else advisor_response["body"]
                combined_response += f"## 💡 Optimization Recommendations\n\n{advisor_body.get('response', 'No recommendations available')}"
            except:
                combined_response += f"## 💡 Optimization Recommendations\n\n{advisor_response.get('body', 'No recommendations available')}"
        elif advisor_response.get("error"):
            combined_response += f"## 💡 Optimization Recommendations\n\n⚠️ {advisor_response['error']}"
        
        return combined_response
    
    def supervisor_agent(query: str) -> str:
        """Intelligent supervisor agent with LLM-based query routing."""
        try:
            # Get routing decision from LLM
            routing_decision = router.route_query(query)
            logger.info(f"LLM routing decision: {routing_decision}")
            
            agents_to_invoke = routing_decision["agents"]
            
            # Handle "both" routing decision by converting to explicit agent list
            if "both" in agents_to_invoke:
                agents_to_invoke = ["cost_forecast", "trusted_advisor"]
            
            routing_explanation = router.get_routing_explanation(query, routing_decision)
            
            # Handle "both" routing decision
            if "both" in agents_to_invoke:
                agents_to_invoke = ["cost_forecast", "trusted_advisor"]
            
            # Route to appropriate agent(s) based on LLM decision
            if len(agents_to_invoke) == 1:
                # Single agent routing
                if "cost_forecast" in agents_to_invoke:
                    logger.info("LLM routed to Cost Forecast Agent only")
                    response = invoke_cost_forecast_agent(query)
                    
                    # Extract response content
                    if "body" in response and not response.get("error"):
                        try:
                            body = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
                            return f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n{body.get('response', 'No cost data available')}"
                        except:
                            return f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n{response.get('body', 'No cost data available')}"
                    else:
                        return f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n⚠️ {response.get('error', 'Unknown error occurred')}"
                
                elif "trusted_advisor" in agents_to_invoke:
                    logger.info("LLM routed to Trusted Advisor Agent only")
                    response = invoke_trusted_advisor_agent(query)
                    
                    # Extract response content
                    if "body" in response and not response.get("error"):
                        try:
                            body = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
                            return f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n{body.get('response', 'No recommendations available')}"
                        except:
                            return f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n{response.get('body', 'No recommendations available')}"
                    else:
                        return f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n⚠️ {response.get('error', 'Unknown error occurred')}"
            
            else:
                # Multiple agent routing (comprehensive analysis)
                logger.info("LLM routed to both agents for comprehensive analysis")
                return get_comprehensive_finops_analysis(query, routing_explanation)
            
        except Exception as e:
            logger.error(f"Error in supervisor agent: {str(e)}")
            return f"# ⚠️ Error\n\nError processing query: {str(e)}"
    
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
