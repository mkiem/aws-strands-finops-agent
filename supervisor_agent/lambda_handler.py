import json
import os
import boto3
import logging
import concurrent.futures
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
    
    def invoke_budget_management_agent(query: str) -> Dict[str, Any]:
        """Invoke the Budget Management Agent."""
        try:
            logger.info(f"Invoking budget management agent with query: {query}")
            response = lambda_client.invoke(
                FunctionName='budget-management-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            payload = json.loads(response['Payload'].read())
            logger.info(f"Budget management response: {payload}")
            return payload
            
        except Exception as e:
            logger.error(f"Error invoking budget management agent: {str(e)}")
            return {"error": f"Budget management agent error: {str(e)}"}
    
    def get_comprehensive_finops_analysis(query: str, routing_explanation: str, agents_to_invoke: List[str]) -> str:
        """Get comprehensive analysis from selected agents using parallel processing."""
        logger.info(f"Performing comprehensive analysis for query: {query} with agents: {agents_to_invoke}")
        
        combined_response = f"# 🏦 Comprehensive AWS FinOps Analysis\n\n{routing_explanation}\n\n"
        
        # Prepare agent invocation tasks for parallel execution
        agent_tasks = {}
        
        # Use ThreadPoolExecutor for parallel Lambda invocations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit agent invocation tasks
            if "cost_forecast" in agents_to_invoke:
                agent_tasks["cost_forecast"] = executor.submit(invoke_cost_forecast_agent, query)
                logger.info("Submitted cost forecast agent task")
            
            if "trusted_advisor" in agents_to_invoke:
                agent_tasks["trusted_advisor"] = executor.submit(invoke_trusted_advisor_agent, query)
                logger.info("Submitted trusted advisor agent task")
                
            if "budget_management" in agents_to_invoke:
                agent_tasks["budget_management"] = executor.submit(invoke_budget_management_agent, query)
                logger.info("Submitted budget management agent task")
            
            # Collect results from parallel execution
            responses = {}
            for agent_name, future in agent_tasks.items():
                try:
                    responses[agent_name] = future.result(timeout=30)  # 30 second timeout per agent
                    logger.info(f"Completed {agent_name} agent invocation")
                except concurrent.futures.TimeoutError:
                    logger.error(f"Timeout waiting for {agent_name} agent")
                    responses[agent_name] = {"error": f"{agent_name} agent timeout after 30 seconds"}
                except Exception as e:
                    logger.error(f"Error getting result from {agent_name} agent: {str(e)}")
                    responses[agent_name] = {"error": f"{agent_name} agent error: {str(e)}"}
        
        logger.info(f"Parallel processing completed. Received {len(responses)} responses.")
        
        # Add cost analysis section
        if "cost_forecast" in responses:
            cost_response = responses["cost_forecast"]
            if "body" in cost_response and not cost_response.get("error"):
                try:
                    cost_body = json.loads(cost_response["body"]) if isinstance(cost_response["body"], str) else cost_response["body"]
                    combined_response += f"## 📊 Cost Analysis\n\n{cost_body.get('response', 'No cost data available')}\n\n"
                except:
                    combined_response += f"## 📊 Cost Analysis\n\n{cost_response.get('body', 'No cost data available')}\n\n"
            elif cost_response.get("error"):
                combined_response += f"## 📊 Cost Analysis\n\n⚠️ {cost_response['error']}\n\n"
        
        # Add optimization recommendations section
        if "trusted_advisor" in responses:
            advisor_response = responses["trusted_advisor"]
            if "body" in advisor_response and not advisor_response.get("error"):
                try:
                    advisor_body = json.loads(advisor_response["body"]) if isinstance(advisor_response["body"], str) else advisor_response["body"]
                    combined_response += f"## 💡 Optimization Recommendations\n\n{advisor_body.get('response', 'No recommendations available')}\n\n"
                except:
                    combined_response += f"## 💡 Optimization Recommendations\n\n{advisor_response.get('body', 'No recommendations available')}\n\n"
            elif advisor_response.get("error"):
                combined_response += f"## 💡 Optimization Recommendations\n\n⚠️ {advisor_response['error']}\n\n"
        
        # Add budget management section
        if "budget_management" in responses:
            budget_response = responses["budget_management"]
            if "body" in budget_response and not budget_response.get("error"):
                try:
                    budget_body = json.loads(budget_response["body"]) if isinstance(budget_response["body"], str) else budget_response["body"]
                    combined_response += f"## 🎯 Budget Management & Cost Controls\n\n{budget_body.get('response', 'No budget recommendations available')}\n\n"
                except:
                    combined_response += f"## 🎯 Budget Management & Cost Controls\n\n{budget_response.get('body', 'No budget recommendations available')}\n\n"
            elif budget_response.get("error"):
                combined_response += f"## 🎯 Budget Management & Cost Controls\n\n⚠️ {budget_response['error']}\n\n"
        
        # Add comprehensive strategy section if multiple agents were used
        if len(responses) > 1:
            combined_response += f"## 📋 Integrated FinOps Strategy\n\n"
            combined_response += f"This comprehensive analysis combines insights from {len(responses)} specialized agents to provide you with a complete financial operations strategy for your AWS environment. "
            combined_response += f"Use the cost analysis to understand your spending patterns, apply the optimization recommendations to reduce costs, and implement the budget controls to maintain ongoing financial governance.\n\n"
            combined_response += f"*⚡ Analysis completed using parallel processing for optimal performance.*"
        
        return combined_response
    
    def supervisor_agent(query: str):
        """Intelligent supervisor agent with LLM-based query routing."""
        try:
            # Get routing decision from LLM
            routing_decision = router.route_query(query)
            logger.info(f"LLM routing decision: {routing_decision}")
            
            agents_to_invoke = routing_decision["agents"]
            routing_explanation = router.get_routing_explanation(query, routing_decision)
            
            # Handle single agent routing
            if len(agents_to_invoke) == 1:
                agent = agents_to_invoke[0]
                
                if agent == "cost_forecast":
                    logger.info("LLM routed to Cost Forecast Agent only")
                    response = invoke_cost_forecast_agent(query)
                    
                    # Extract response content
                    if "body" in response and not response.get("error"):
                        try:
                            body = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
                            final_response = f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n{body.get('response', 'No cost data available')}"
                        except:
                            final_response = f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n{response.get('body', 'No cost data available')}"
                    else:
                        final_response = f"# 📊 AWS Cost Analysis\n\n{routing_explanation}\n\n⚠️ {response.get('error', 'Unknown error occurred')}"
                    
                    return final_response, routing_decision
                
                elif agent == "trusted_advisor":
                    logger.info("LLM routed to Trusted Advisor Agent only")
                    response = invoke_trusted_advisor_agent(query)
                    
                    # Extract response content
                    if "body" in response and not response.get("error"):
                        try:
                            body = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
                            final_response = f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n{body.get('response', 'No recommendations available')}"
                        except:
                            final_response = f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n{response.get('body', 'No recommendations available')}"
                    else:
                        final_response = f"# 💡 AWS Optimization Recommendations\n\n{routing_explanation}\n\n⚠️ {response.get('error', 'Unknown error occurred')}"
                    
                    return final_response, routing_decision
                
                elif agent == "budget_management":
                    logger.info("LLM routed to Budget Management Agent only")
                    response = invoke_budget_management_agent(query)
                    
                    # Extract response content
                    if "body" in response and not response.get("error"):
                        try:
                            body = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
                            final_response = f"# 🎯 AWS Budget Management\n\n{routing_explanation}\n\n{body.get('response', 'No budget recommendations available')}"
                        except:
                            final_response = f"# 🎯 AWS Budget Management\n\n{routing_explanation}\n\n{response.get('body', 'No budget recommendations available')}"
                    else:
                        final_response = f"# 🎯 AWS Budget Management\n\n{routing_explanation}\n\n⚠️ {response.get('error', 'Unknown error occurred')}"
                    
                    return final_response, routing_decision
            
            else:
                # Multiple agent routing (comprehensive analysis)
                logger.info(f"LLM routed to multiple agents: {agents_to_invoke}")
                final_response = get_comprehensive_finops_analysis(query, routing_explanation, agents_to_invoke)
                return final_response, routing_decision
            
        except Exception as e:
            logger.error(f"Error in supervisor agent: {str(e)}")
            error_metrics = {"routing_method": "error", "routing_time": 0, "agents": []}
            return f"# ⚠️ Error\n\nError processing query: {str(e)}", error_metrics
    
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
        response, routing_metrics = supervisor(query)
        
        # Format the response with performance metrics
        result = {
            "query": query,
            "response": str(response),
            "agent": "AWS-FinOps-Supervisor",
            "timestamp": context.aws_request_id if context else None,
            "routing_method": routing_metrics.get("routing_method", "unknown"),
            "routing_time": routing_metrics.get("routing_time", 0),
            "agents_invoked": routing_metrics.get("agents", [])
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
