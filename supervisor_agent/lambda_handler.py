"""
Enhanced Lambda Handler with Latency-Optimized Intelligent Synthesis
Integrates the IntelligentFinOpsSupervisor with existing architecture.
"""

import json
import os
import boto3
import logging
import concurrent.futures
import uuid
import time
from typing import Dict, Any, Optional, List, Callable
from llm_router_simple import EnhancedLLMQueryRouter
from intelligent_finops_supervisor import IntelligentFinOpsSupervisor

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# WebSocket client for streaming responses
websocket_client = None

def get_websocket_client():
    """Get or create WebSocket client for streaming responses."""
    global websocket_client
    if websocket_client is None:
        websocket_client = boto3.client('apigatewaymanagementapi', 
                                      endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT'))
    return websocket_client

def send_websocket_message(connection_id: str, message: Dict[str, Any]) -> bool:
    """Send a message via WebSocket."""
    try:
        if not connection_id:
            logger.warning("No connection ID provided for WebSocket message")
            return False
            
        client = get_websocket_client()
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        logger.info(f"Sent WebSocket message: {message.get('type', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {str(e)}")
        return False

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

def get_enhanced_supervisor_agent():
    """Initialize and return the enhanced intelligent supervisor agent."""
    lambda_client = boto3.client('lambda')
    router = EnhancedLLMQueryRouter()
    supervisor = IntelligentFinOpsSupervisor()
    
    def invoke_cost_forecast_agent(query: str) -> Dict[str, Any]:
        """Invoke the AWS Cost Forecast Agent."""
        try:
            logger.info(f"Invoking cost forecast agent with query: {query}")
            response = lambda_client.invoke(
                FunctionName='aws-cost-forecast-agent:PROD',  # Use PROD alias for provisioned concurrency
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query})
            )
            
            payload = json.loads(response['Payload'].read())
            logger.info(f"Cost forecast response received")
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
            logger.info(f"Trusted advisor response received")
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
            logger.info(f"Budget management response received")
            return payload
            
        except Exception as e:
            logger.error(f"Error invoking budget management agent: {str(e)}")
            return {"error": f"Budget management agent error: {str(e)}"}
    
    def execute_agents_parallel(agents_to_invoke: List[str], query: str) -> Dict[str, Any]:
        """Execute multiple agents in parallel."""
        agent_functions = {
            'cost_forecast': invoke_cost_forecast_agent,
            'aws-cost-forecast-agent': invoke_cost_forecast_agent,
            'trusted_advisor': invoke_trusted_advisor_agent,
            'trusted-advisor-agent-trusted-advisor-agent': invoke_trusted_advisor_agent,
            'budget_management': invoke_budget_management_agent,
            'budget-management-agent': invoke_budget_management_agent
        }
        
        responses = {}
        
        # Use ThreadPoolExecutor for parallel Lambda invocations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit agent invocation tasks
            agent_tasks = {}
            for agent_name in agents_to_invoke:
                if agent_name in agent_functions:
                    agent_tasks[agent_name] = executor.submit(agent_functions[agent_name], query)
                    logger.info(f"Submitted {agent_name} agent task")
            
            # Collect results from parallel execution
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
        
        return responses
    
    def execute_agents_parallel_streaming(agents_to_invoke: List[str], query: str, 
                                        connection_id: str = None, job_id: str = None) -> Dict[str, Any]:
        """Execute multiple agents in parallel with streaming support."""
        agent_functions = {
            'cost_forecast': invoke_cost_forecast_agent,
            'aws-cost-forecast-agent': invoke_cost_forecast_agent,
            'trusted_advisor': invoke_trusted_advisor_agent,
            'trusted-advisor-agent-trusted-advisor-agent': invoke_trusted_advisor_agent,
            'budget_management': invoke_budget_management_agent,
            'budget-management-agent': invoke_budget_management_agent
        }
        
        responses = {}
        completed_agents = []
        
        # Use ThreadPoolExecutor for parallel Lambda invocations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit agent invocation tasks
            agent_tasks = {}
            for agent_name in agents_to_invoke:
                if agent_name in agent_functions:
                    agent_tasks[agent_name] = executor.submit(agent_functions[agent_name], query)
                    logger.info(f"Submitted {agent_name} agent task")
            
            # Stream results as they complete
            for future in concurrent.futures.as_completed(agent_tasks.values(), timeout=35):
                # Find which agent completed
                completed_agent = None
                for agent_name, agent_future in agent_tasks.items():
                    if agent_future == future:
                        completed_agent = agent_name
                        break
                
                if completed_agent:
                    try:
                        result = future.result(timeout=5)
                        responses[completed_agent] = result
                        completed_agents.append(completed_agent)
                        
                        logger.info(f"Completed {completed_agent} agent invocation")
                        
                        # Stream individual result if WebSocket available
                        if connection_id:
                            formatted_result = format_individual_agent_result(completed_agent, result)
                            
                            send_websocket_message(connection_id, {
                                'type': 'agent_completed',
                                'jobId': job_id,
                                'agent': completed_agent,
                                'result': formatted_result,
                                'progress': int((len(completed_agents) / len(agents_to_invoke)) * 100),
                                'completed_agents': completed_agents,
                                'total_agents': len(agents_to_invoke)
                            })
                        
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Timeout waiting for {completed_agent} agent")
                        responses[completed_agent] = {"error": f"{completed_agent} agent timeout after 30 seconds"}
                    except Exception as e:
                        logger.error(f"Error getting result from {completed_agent} agent: {str(e)}")
                        responses[completed_agent] = {"error": f"{completed_agent} agent error: {str(e)}"}
        
        return responses
    
    def enhanced_supervisor_agent(query: str, connection_id: str = None):
        """Enhanced intelligent supervisor agent with latency-optimized routing."""
        try:
            start_time = time.time()
            
            # Get routing decision from LLM
            routing_decision = router.route_query(query)
            logger.info(f"LLM routing decision: {routing_decision}")
            
            agents_to_invoke = routing_decision["agents"]
            routing_explanation = router.get_routing_explanation(query, routing_decision)
            
            routing_context = {
                'reasoning': routing_explanation,
                'scope': f"Analysis involving {len(agents_to_invoke)} specialized systems",
                'agents': agents_to_invoke,
                'routing_decision': routing_decision
            }
            
            # LATENCY-OPTIMIZED ROUTING LOGIC
            if len(agents_to_invoke) == 1:
                # FAST PATH: Single agent - direct routing with minimal overhead
                logger.info(f"Fast path: Single agent routing to {agents_to_invoke[0]}")
                
                agent = agents_to_invoke[0]
                agent_functions = {
                    'cost_forecast': invoke_cost_forecast_agent,
                    'aws-cost-forecast-agent': invoke_cost_forecast_agent,
                    'trusted_advisor': invoke_trusted_advisor_agent,
                    'trusted-advisor-agent-trusted-advisor-agent': invoke_trusted_advisor_agent,
                    'budget_management': invoke_budget_management_agent,
                    'budget-management-agent': invoke_budget_management_agent
                }
                
                if agent in agent_functions:
                    response = agent_functions[agent](query)
                    final_response = supervisor.format_single_agent_response(
                        agent, response, routing_explanation
                    )
                    
                    processing_time = time.time() - start_time
                    logger.info(f"Single agent processing completed in {processing_time:.2f}s")
                    
                    return final_response, routing_decision
                else:
                    return f"# ⚠️ Error\n\nUnknown agent: {agent}", routing_decision
            
            else:
                # MULTI-AGENT PATH: Check if synthesis is needed
                needs_synthesis = supervisor.should_synthesize(query, agents_to_invoke)
                
                if needs_synthesis:
                    # SYNTHESIS PATH: Intelligent LLM-based synthesis
                    logger.info(f"Synthesis path: {len(agents_to_invoke)} agents with intelligent synthesis")
                    
                    # Generate job ID for streaming
                    job_id = str(uuid.uuid4()) if connection_id else None
                    
                    # Send initial acknowledgment for streaming
                    if connection_id:
                        send_websocket_message(connection_id, {
                            'type': 'analysis_started',
                            'jobId': job_id,
                            'agents': agents_to_invoke,
                            'query': query,
                            'estimatedTime': f"{len(agents_to_invoke) * 2}-{len(agents_to_invoke) * 5} seconds",
                            'routing_explanation': routing_explanation,
                            'synthesis_enabled': True
                        })
                    
                    # Execute agents in parallel
                    if connection_id:
                        responses = execute_agents_parallel_streaming(agents_to_invoke, query, connection_id, job_id)
                    else:
                        responses = execute_agents_parallel(agents_to_invoke, query)
                    
                    # Perform intelligent synthesis
                    synthesis_start = time.time()
                    final_response = supervisor.synthesize_responses(query, responses, routing_context)
                    synthesis_time = time.time() - synthesis_start
                    
                    processing_time = time.time() - start_time
                    logger.info(f"Synthesis processing completed in {processing_time:.2f}s "
                              f"(synthesis: {synthesis_time:.2f}s)")
                    
                    # Send final completion message for streaming
                    if connection_id:
                        send_websocket_message(connection_id, {
                            'type': 'analysis_completed',
                            'jobId': job_id,
                            'final_response': final_response,
                            'total_agents': len(agents_to_invoke),
                            'completed_agents': len(responses),
                            'processing_time': f"Completed in {processing_time:.1f}s with intelligent synthesis",
                            'synthesis_time': f"{synthesis_time:.1f}s"
                        })
                    
                    return final_response, routing_decision
                
                else:
                    # AGGREGATION PATH: Simple template-based combination
                    logger.info(f"Aggregation path: {len(agents_to_invoke)} agents with simple aggregation")
                    
                    # Execute agents in parallel
                    responses = execute_agents_parallel(agents_to_invoke, query)
                    
                    # Use simple aggregation (existing logic)
                    final_response = build_simple_aggregation(routing_explanation, responses)
                    
                    processing_time = time.time() - start_time
                    logger.info(f"Aggregation processing completed in {processing_time:.2f}s")
                    
                    return final_response, routing_decision
            
        except Exception as e:
            logger.error(f"Error in enhanced supervisor agent: {str(e)}")
            error_metrics = {"routing_method": "error", "routing_time": 0, "agents": []}
            return f"# ⚠️ Error\n\nError processing query: {str(e)}", error_metrics
    
    return enhanced_supervisor_agent

def build_simple_aggregation(routing_explanation: str, responses: Dict[str, Any]) -> str:
    """Build simple aggregated response without LLM synthesis."""
    supervisor = IntelligentFinOpsSupervisor()
    
    combined_response = f"# 🏦 AWS FinOps Analysis\n\n{routing_explanation}\n\n"
    
    # Add each agent's response in separate sections
    for agent_name, response in responses.items():
        agent_display_name = supervisor._get_agent_display_name(agent_name)
        agent_content = supervisor._extract_agent_content(response)
        
        if response.get("error"):
            combined_response += f"## {agent_display_name}\n\n⚠️ {response['error']}\n\n"
        else:
            combined_response += f"## {agent_display_name}\n\n{agent_content}\n\n"
    
    # Add simple summary for multiple agents
    if len(responses) > 1:
        combined_response += f"## Summary\n\n"
        combined_response += f"This analysis combines insights from {len(responses)} specialized agents. "
        combined_response += f"Review each section above for detailed recommendations and next steps.\n\n"
        combined_response += f"*⚡ Analysis completed using parallel processing.*"
    
    return combined_response

def format_individual_agent_result(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Format individual agent result for streaming."""
    supervisor = IntelligentFinOpsSupervisor()
    
    return {
        'agent': agent_name,
        'title': supervisor._get_agent_display_name(agent_name),
        'content': supervisor._extract_agent_content(result),
        'status': 'error' if result.get('error') else 'completed',
        'timestamp': time.time()
    }

def handler(event, context):
    """Enhanced Lambda handler function with intelligent synthesis."""
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
        connection_id = event.get('requestContext', {}).get('connectionId')  # Extract WebSocket connection ID
        
        if not query:
            return format_response(400, {
                "error": "Invalid input",
                "message": "Please provide a query about AWS costs or optimization opportunities.",
                "agent": "AWS-FinOps-Supervisor"
            })
        
        logger.info(f"Processing query: {query}")
        if connection_id:
            logger.info(f"WebSocket connection ID: {connection_id}")
        
        # Get enhanced supervisor agent
        supervisor_agent = get_enhanced_supervisor_agent()
        
        # Process query with enhanced routing
        response, routing_metrics = supervisor_agent(query, connection_id)
        
        # Format final response
        result = {
            "query": query,
            "response": response,
            "agent": "AWS-FinOps-Supervisor-Enhanced",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "routing_metrics": routing_metrics
        }
        
        logger.info("Enhanced supervisor processing completed successfully")
        return format_response(200, result)
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return format_response(500, {
            "error": "Internal server error",
            "message": str(e),
            "agent": "AWS-FinOps-Supervisor-Enhanced"
        })
