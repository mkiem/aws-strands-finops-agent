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
from typing import Dict, Any, Optional, List, Callable, Tuple
from llm_router_simple import EnhancedLLMQueryRouter
from intelligent_finops_supervisor import IntelligentFinOpsSupervisor
from strands_supervisor_agent import get_strands_supervisor

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
            "Access-Control-Allow-Origin": "https://staging.${AMPLIFY_APP_ID}.amplifyapp.com",
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
            "Access-Control-Allow-Origin": "https://staging.${AMPLIFY_APP_ID}.amplifyapp.com",
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

def should_proceed_with_synthesis(responses: Dict[str, Any], min_success_ratio: float = 0.5) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Determine if we have enough successful responses to proceed with synthesis.
    
    IMPROVED: More lenient error handling - proceed with even 1 successful agent
    
    Args:
        responses: Agent responses (including errors)
        min_success_ratio: Minimum ratio of successful agents (default: 50%)
    
    Returns:
        (should_proceed, successful_responses_only, failed_agents)
    """
    successful_responses = {}
    failed_agents = []
    
    for agent, response in responses.items():
        if response.get('error'):
            failed_agents.append(agent)
            logger.warning(f"Agent {agent} failed: {response['error']}")
        else:
            successful_responses[agent] = response
            logger.info(f"Agent {agent} succeeded")
    
    success_ratio = len(successful_responses) / len(responses) if responses else 0
    
    # IMPROVED: Always proceed if we have at least 1 successful response
    should_proceed = len(successful_responses) >= 1
    
    logger.info(f"Success analysis: {len(successful_responses)}/{len(responses)} agents succeeded "
               f"({success_ratio:.1%}). Min threshold: {min_success_ratio:.1%}. "
               f"Proceed: {should_proceed} (improved: always proceed with ≥1 success)")
    
    return should_proceed, successful_responses, failed_agents

def format_partial_success_response(successful_responses: Dict[str, Any], 
                                  failed_agents: List[str], 
                                  synthesis_result: str,
                                  query: str) -> str:
    """Format response when some agents succeed and others fail."""
    
    # Map agent names to user-friendly names
    agent_display_names = {
        'cost_forecast': 'Cost Analysis',
        'aws-cost-forecast-agent': 'Cost Analysis',
        'trusted_advisor': 'Optimization Recommendations',
        'trusted-advisor-agent-trusted-advisor-agent': 'Optimization Recommendations',
        'budget_management': 'Budget Management',
        'budget-management-agent': 'Budget Management'
    }
    
    successful_names = [agent_display_names.get(agent, agent) for agent in successful_responses.keys()]
    failed_names = [agent_display_names.get(agent, agent) for agent in failed_agents]
    
    response = f"# 🏦 AWS FinOps Analysis (Partial Results)\n\n"
    response += f"⚠️ **Analysis Status**: Completed with {len(successful_responses)} of {len(successful_responses) + len(failed_agents)} services available.\n\n"
    
    if successful_names:
        response += f"✅ **Available Analysis**: {', '.join(successful_names)}\n\n"
    
    if failed_names:
        response += f"❌ **Temporarily Unavailable**: {', '.join(failed_names)}\n\n"
    
    response += "---\n\n"
    response += synthesis_result
    response += f"\n\n---\n\n"
    response += f"💡 **Note**: This analysis is based on available data. For complete insights including {', '.join(failed_names)}, please try again in a few moments when all services are responsive."
    
    return response

def format_insufficient_success_response(successful_responses: Dict[str, Any], 
                                       failed_agents: List[str], 
                                       query: str) -> str:
    """Format response when too few agents succeeded to provide meaningful analysis."""
    
    agent_display_names = {
        'cost_forecast': 'Cost Analysis',
        'aws-cost-forecast-agent': 'Cost Analysis', 
        'trusted_advisor': 'Optimization Recommendations',
        'trusted-advisor-agent-trusted-advisor-agent': 'Optimization Recommendations',
        'budget_management': 'Budget Management',
        'budget-management-agent': 'Budget Management'
    }
    
    successful_names = [agent_display_names.get(agent, agent) for agent in successful_responses.keys()]
    failed_names = [agent_display_names.get(agent, agent) for agent in failed_agents]
    
    response = f"# ⚠️ Analysis Temporarily Unavailable\n\n"
    response += f"I apologize, but I'm currently unable to provide a comprehensive analysis for your request: \"{query}\"\n\n"
    response += f"**Current Status**:\n"
    response += f"- ❌ Unavailable: {', '.join(failed_names)}\n"
    
    if successful_names:
        response += f"- ✅ Available: {', '.join(successful_names)}\n"
    
    response += f"\n**What happened**: {len(failed_agents)} of {len(successful_responses) + len(failed_agents)} required services are temporarily unresponsive, "
    response += f"which prevents me from providing the comprehensive analysis you requested.\n\n"
    response += f"**Next steps**:\n"
    response += f"1. Please try your request again in 1-2 minutes\n"
    response += f"2. If the issue persists, you can ask for specific analysis from available services\n"
    response += f"3. For urgent needs, contact your AWS support team\n\n"
    response += f"*I'll be ready to provide your complete FinOps analysis as soon as all services are responsive.*"
    
    return response

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
            
            # Collect results from parallel execution with optimized timeouts
            for agent_name, future in agent_tasks.items():
                try:
                    # Use different timeouts based on agent type
                    if agent_name in ['cost_forecast', 'aws-cost-forecast-agent']:
                        timeout = 180  # 3 minutes for cost forecast agent
                    else:
                        timeout = 60   # 1 minute for other agents
                    
                    responses[agent_name] = future.result(timeout=timeout)
                    logger.info(f"Completed {agent_name} agent invocation in {timeout}s timeout")
                except concurrent.futures.TimeoutError:
                    logger.error(f"Timeout waiting for {agent_name} agent after {timeout} seconds")
                    responses[agent_name] = {"error": f"{agent_name} agent timeout after {timeout} seconds"}
                except Exception as e:
                    logger.error(f"Error getting result from {agent_name} agent: {str(e)}")
                    responses[agent_name] = {"error": f"{agent_name} agent error: {str(e)}"}
        
        return responses
    
    def execute_agents_parallel_streaming(agents_to_invoke: List[str], query: str, 
                                        connection_id: str = None, job_id: str = None) -> Dict[str, Any]:
        """Execute multiple agents in parallel with streaming support and proper timeout handling."""
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
            
            # Stream results as they complete with optimized timeout handling
            try:
                # Use different timeouts based on agent composition
                max_timeout = 300  # 5 minutes overall maximum
                if 'cost_forecast' in agents_to_invoke or 'aws-cost-forecast-agent' in agents_to_invoke:
                    max_timeout = 240  # 4 minutes if cost forecast is involved
                
                for future in concurrent.futures.as_completed(agent_tasks.values(), timeout=max_timeout):
                    # Find which agent completed
                    completed_agent = None
                    for agent_name, agent_future in agent_tasks.items():
                        if agent_future == future:
                            completed_agent = agent_name
                            break
                    
                    if completed_agent:
                        try:
                            # Extract result (should be immediate since future is completed)
                            result = future.result()
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
                            
                        except Exception as e:
                            logger.error(f"Error getting result from {completed_agent} agent: {str(e)}")
                            responses[completed_agent] = {"error": f"{completed_agent} agent error: {str(e)}"}
                            
            except concurrent.futures.TimeoutError:
                # Handle overall timeout - some agents didn't complete
                logger.error(f"Overall timeout waiting for agents after {max_timeout}s. Completed: {len(completed_agents)}/{len(agents_to_invoke)}")
                
                # Mark remaining agents as timed out
                for agent_name, future in agent_tasks.items():
                    if agent_name not in responses:
                        logger.error(f"Agent {agent_name} did not complete within {max_timeout}s timeout")
                        responses[agent_name] = {"error": f"{agent_name} agent timeout after {max_timeout} seconds"}
                        
                        # Cancel the future to clean up
                        future.cancel()
                
                # Send timeout notification via WebSocket
                if connection_id:
                    send_websocket_message(connection_id, {
                        'type': 'analysis_timeout',
                        'jobId': job_id,
                        'completed_agents': completed_agents,
                        'total_agents': len(agents_to_invoke),
                        'message': f'Analysis partially completed: {len(completed_agents)}/{len(agents_to_invoke)} agents responded'
                    })
        
        logger.info(f"Streaming processing completed. Received {len(responses)} responses.")
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
                logger.info(f"Multi-agent path: {len(agents_to_invoke)} agents - {agents_to_invoke}")
                needs_synthesis = supervisor.should_synthesize(query, agents_to_invoke)
                logger.info(f"Synthesis decision: {needs_synthesis} for query: '{query[:100]}...'")
                
                if needs_synthesis:
                    # SYNTHESIS PATH: Intelligent LLM-based synthesis
                    logger.info(f"SYNTHESIS PATH: {len(agents_to_invoke)} agents with intelligent synthesis")
                    
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
                    
                    # PHASE 1 FIX: Implement graceful degradation
                    should_proceed, successful_responses, failed_agents = should_proceed_with_synthesis(responses)
                    
                    if should_proceed:
                        # Sufficient successful responses - proceed with synthesis
                        logger.info(f"Proceeding with synthesis using {len(successful_responses)} successful responses")
                        
                        # Update routing context for synthesis
                        synthesis_routing_context = routing_context.copy()
                        synthesis_routing_context['successful_agents'] = list(successful_responses.keys())
                        synthesis_routing_context['failed_agents'] = failed_agents
                        
                        # Perform intelligent synthesis with successful responses only
                        synthesis_start = time.time()
                        synthesis_result = supervisor.synthesize_responses(query, successful_responses, synthesis_routing_context)
                        synthesis_time = time.time() - synthesis_start
                        
                        # Format final response based on whether we have partial or complete success
                        if failed_agents:
                            # Partial success - some agents failed
                            final_response = format_partial_success_response(
                                successful_responses, failed_agents, synthesis_result, query
                            )
                            logger.info(f"Partial synthesis completed: {len(successful_responses)} successful, {len(failed_agents)} failed")
                        else:
                            # Complete success - all agents succeeded
                            final_response = synthesis_result
                            logger.info(f"Complete synthesis completed: all {len(successful_responses)} agents successful")
                        
                        processing_time = time.time() - start_time
                        logger.info(f"Synthesis processing completed in {processing_time:.2f}s "
                                  f"(synthesis: {synthesis_time:.2f}s)")
                        
                    else:
                        # Insufficient successful responses - cannot provide meaningful synthesis
                        logger.warning(f"Insufficient successful responses for synthesis: {len(successful_responses)}/{len(responses)}")
                        final_response = format_insufficient_success_response(successful_responses, failed_agents, query)
                        
                        processing_time = time.time() - start_time
                        logger.info(f"Insufficient success processing completed in {processing_time:.2f}s")
                    
                    # Send final completion message for streaming
                    if connection_id:
                        completion_message = {
                            'type': 'analysis_completed',
                            'jobId': job_id,
                            'final_response': final_response,
                            'total_agents': len(agents_to_invoke),
                            'successful_agents': len(successful_responses),
                            'failed_agents': len(failed_agents),
                            'processing_time': f"Completed in {processing_time:.1f}s with intelligent synthesis"
                        }
                        
                        # Add synthesis time if synthesis was performed
                        if should_proceed:
                            completion_message['synthesis_time'] = f"{synthesis_time:.1f}s"
                            completion_message['analysis_status'] = 'partial' if failed_agents else 'complete'
                        else:
                            completion_message['analysis_status'] = 'insufficient_data'
                        
                        send_websocket_message(connection_id, completion_message)
                    
                    return final_response, routing_decision
                
                else:
                    # AGGREGATION PATH: Enhanced aggregation with optional synthesis
                    logger.info(f"AGGREGATION PATH: {len(agents_to_invoke)} agents with enhanced aggregation")
                    
                    # Execute agents in parallel
                    responses = execute_agents_parallel(agents_to_invoke, query)
                    
                    # IMPROVED: Always proceed if we have at least 1 successful response
                    should_proceed, successful_responses, failed_agents = should_proceed_with_synthesis(responses, min_success_ratio=0.5)
                    
                    if should_proceed:
                        # IMPROVED: Use synthesis even in aggregation path for better results
                        if len(successful_responses) >= 2:
                            # Multiple successful responses - use synthesis for better integration
                            logger.info(f"Using synthesis for {len(successful_responses)} successful responses in aggregation path")
                            
                            synthesis_routing_context = routing_context.copy()
                            synthesis_routing_context['successful_agents'] = list(successful_responses.keys())
                            synthesis_routing_context['failed_agents'] = failed_agents
                            
                            synthesis_start = time.time()
                            synthesis_result = supervisor.synthesize_responses(query, successful_responses, synthesis_routing_context)
                            synthesis_time = time.time() - synthesis_start
                            
                            if failed_agents:
                                # Partial success with synthesis
                                final_response = format_partial_success_response(
                                    successful_responses, failed_agents, synthesis_result, query
                                )
                                logger.info(f"Partial synthesis in aggregation path: {len(successful_responses)} successful, {len(failed_agents)} failed")
                            else:
                                # Complete success with synthesis
                                final_response = synthesis_result
                                logger.info(f"Complete synthesis in aggregation path: all {len(successful_responses)} agents successful")
                        else:
                            # Single successful response - use simple formatting
                            logger.info(f"Single successful response in aggregation path")
                            agent_name = list(successful_responses.keys())[0]
                            response = successful_responses[agent_name]
                            
                            if failed_agents:
                                # Single success with failures
                                final_response = format_partial_success_response(
                                    successful_responses, failed_agents, 
                                    supervisor.format_single_agent_response(agent_name, response, routing_explanation), 
                                    query
                                )
                            else:
                                # Single success, no failures
                                final_response = supervisor.format_single_agent_response(agent_name, response, routing_explanation)
                    else:
                        # No successful responses
                        logger.error(f"No successful responses in aggregation path")
                        final_response = format_insufficient_success_response(successful_responses, failed_agents, query)
                    
                    processing_time = time.time() - start_time
                    logger.info(f"Enhanced aggregation processing completed in {processing_time:.2f}s")
                    
                    return final_response, routing_decision
            
        except Exception as e:
            logger.error(f"Error in enhanced supervisor agent: {str(e)}")
            error_metrics = {"routing_method": "error", "routing_time": 0, "agents": []}
            return f"# ⚠️ Error\n\nError processing query: {str(e)}", error_metrics
    
    return enhanced_supervisor_agent

def build_simple_aggregation(routing_explanation: str, responses: Dict[str, Any]) -> str:
    """
    Build simple aggregated response without LLM synthesis.
    
    Note: This function now expects only successful responses (errors filtered out by graceful degradation).
    """
    supervisor = IntelligentFinOpsSupervisor()
    
    combined_response = f"# 🏦 AWS FinOps Analysis\n\n{routing_explanation}\n\n"
    
    # Add each agent's response in separate sections
    # Note: All responses should be successful since errors are filtered out before this function
    for agent_name, response in responses.items():
        agent_display_name = supervisor._get_agent_display_name(agent_name)
        agent_content = supervisor._extract_agent_content(response)
        
        # Since we filter errors before calling this function, we should only have successful responses
        # But keep error handling as a safety net
        if response.get("error"):
            logger.warning(f"Unexpected error response in build_simple_aggregation for {agent_name}: {response['error']}")
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

def lambda_handler(event, context):
    """
    Enhanced Lambda handler with Strands-based intelligent synthesis.
    """
    try:
        # Extract query from various event formats
        query = extract_query(event)
        if not query:
            return format_response(400, {
                "error": "Invalid input",
                "message": "Please provide a query about AWS costs or optimization opportunities.",
                "agent": "AWS-FinOps-Supervisor"
            })
        
        logger.info(f"Processing query: {query}")
        
        # Check if we should use Strands-based approach (new architecture)
        use_strands = os.environ.get('USE_STRANDS_AGENT', 'true').lower() == 'true'
        
        if use_strands:
            # NEW: Use Strands-based supervisor with proper "Agents as Tools" pattern
            return handle_strands_based_query(query, event, context)
        else:
            # LEGACY: Use existing manual routing approach
            return handle_legacy_query(query, event, context)
            
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        return format_response(500, {
            "error": "Internal server error",
            "message": str(e),
            "agent": "AWS-FinOps-Supervisor-Enhanced"
        })

def handle_strands_based_query(query: str, event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle query using Strands-based supervisor with intelligent agent tool selection.
    """
    try:
        logger.info("Using Strands-based supervisor agent")
        
        # Get the Strands supervisor instance
        supervisor = get_strands_supervisor()
        
        # Check if this is a WebSocket request for streaming
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        if connection_id:
            # Handle WebSocket streaming
            return handle_strands_streaming(supervisor, query, connection_id)
        else:
            # Handle direct invocation
            return handle_strands_direct(supervisor, query)
            
    except Exception as e:
        logger.error(f"Error in Strands-based query handling: {str(e)}")
        return format_response(500, {
            "error": "Error in Strands analysis",
            "message": str(e),
            "agent": "AWS-FinOps-Supervisor-Strands"
        })

def handle_strands_direct(supervisor, query: str) -> Dict[str, Any]:
    """Handle direct Strands-based analysis without streaming."""
    try:
        start_time = time.time()
        
        # Let the Strands agent handle tool selection and synthesis
        response = supervisor.analyze(query)
        
        processing_time = time.time() - start_time
        
        result = {
            "query": query,
            "response": response,
            "agent": "AWS-FinOps-Supervisor-Strands",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "processing_time": f"{processing_time:.1f}s",
            "architecture": "strands_agents_as_tools"
        }
        
        return format_response(200, result)
        
    except Exception as e:
        logger.error(f"Error in direct Strands analysis: {str(e)}")
        raise

def handle_strands_streaming(supervisor, query: str, connection_id: str) -> Dict[str, Any]:
    """Handle WebSocket streaming with Strands-based analysis."""
    try:
        logger.info(f"Starting Strands streaming analysis for connection: {connection_id}")
        
        # Send initial acknowledgment
        send_websocket_message(connection_id, {
            'type': 'analysis_started',
            'query': query,
            'architecture': 'strands_agents_as_tools',
            'message': 'Starting intelligent FinOps analysis with Strands agent...'
        })
        
        # Stream the analysis
        response_parts = []
        for event in supervisor.stream_analyze(query):
            # Handle different event types from Strands streaming
            if hasattr(event, 'data') and event.data:
                # Text generation event
                response_parts.append(event.data)
                send_websocket_message(connection_id, {
                    'type': 'text_chunk',
                    'data': event.data
                })
            elif hasattr(event, 'tool_name'):
                # Tool invocation event
                send_websocket_message(connection_id, {
                    'type': 'tool_invocation',
                    'tool_name': event.tool_name,
                    'message': f'Consulting {event.tool_name}...'
                })
        
        # Send completion message
        final_response = ''.join(response_parts)
        send_websocket_message(connection_id, {
            'type': 'analysis_complete',
            'response': final_response,
            'architecture': 'strands_agents_as_tools'
        })
        
        return {"statusCode": 200}
        
    except Exception as e:
        logger.error(f"Error in Strands streaming: {str(e)}")
        send_websocket_message(connection_id, {
            'type': 'analysis_error',
            'error': str(e)
        })
        return {"statusCode": 500}

def handle_legacy_query(query: str, event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle query using legacy manual routing approach."""
    # Use the existing enhanced supervisor agent
    connection_id = event.get('requestContext', {}).get('connectionId')
    supervisor_agent = get_enhanced_supervisor_agent()
    response, routing_metrics = supervisor_agent(query, connection_id)
    
    result = {
        "query": query,
        "response": response,
        "agent": "AWS-FinOps-Supervisor-Enhanced",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "routing_metrics": routing_metrics
    }
    
    return format_response(200, result)
