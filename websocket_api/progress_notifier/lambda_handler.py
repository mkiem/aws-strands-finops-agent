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
    """Process individual FinOps job using Supervisor Agent with streaming."""
    try:
        job_id = job_data.get('jobId')
        connection_id = job_data.get('connectionId')
        user_id = job_data.get('userId')
        query = job_data.get('query')
        
        logger.info(f"Processing job: {job_id} for user: {user_id}")
        
        # Update job status to processing
        update_job_status(job_id, 'processing', 'Starting FinOps analysis...')
        send_progress_update(connection_id, job_id, 'processing', 'Starting FinOps analysis...', 10)
        
        # Step 1: Route query and get streaming analysis
        send_progress_update(connection_id, job_id, 'processing', 'Analyzing query and routing to appropriate agents...', 20)
        
        # Use streaming supervisor invocation
        final_result = invoke_supervisor_agent_streaming(query, connection_id, job_id)
        
        # Step 2: Send Final Result
        update_job_status(job_id, 'completed', 'Analysis completed successfully')
        send_final_result(connection_id, job_id, final_result)
        
        logger.info(f"Job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        update_job_status(job_id, 'failed', f'Job failed: {str(e)}')
        send_error_result(connection_id, job_id, str(e))

def invoke_supervisor_agent_streaming(query: str, connection_id: str, job_id: str) -> Dict[str, Any]:
    """Invoke the Supervisor Agent with streaming support by calling individual agents."""
    try:
        logger.info(f"Starting streaming supervisor analysis for query: {query}")
        
        # Step 1: Get routing decision from supervisor agent (fast routing only)
        send_progress_update(connection_id, job_id, 'processing', 'Determining optimal agent routing...', 30)
        
        # Simple routing logic (can be enhanced later)
        agents_to_invoke = determine_agents_for_query(query)
        logger.info(f"Routing decision: {agents_to_invoke}")
        
        # Send analysis started message
        send_websocket_message(connection_id, {
            'type': 'analysis_started',
            'jobId': job_id,
            'agents': agents_to_invoke,
            'query': query,
            'estimatedTime': f"{len(agents_to_invoke) * 2}-{len(agents_to_invoke) * 5} seconds"
        })
        
        # Step 2: Invoke agents in parallel and stream results
        agent_results = {}
        completed_agents = []
        
        if len(agents_to_invoke) > 1:
            # Parallel invocation for multiple agents
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Submit agent tasks
                agent_futures = {}
                for agent in agents_to_invoke:
                    if agent == 'cost_forecast':
                        agent_futures[agent] = executor.submit(invoke_cost_forecast_agent, query)
                    elif agent == 'trusted_advisor':
                        agent_futures[agent] = executor.submit(invoke_trusted_advisor_agent, query)
                    elif agent == 'budget_management':
                        agent_futures[agent] = executor.submit(invoke_budget_management_agent, query)
                
                # Process results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(agent_futures.values(), timeout=60):  # Increased timeout
                    # Find which agent completed
                    completed_agent = None
                    for agent_name, agent_future in agent_futures.items():
                        if agent_future == future:
                            completed_agent = agent_name
                            break
                    
                    if completed_agent:
                        try:
                            result = future.result(timeout=10)  # Individual agent timeout
                            agent_results[completed_agent] = result
                            completed_agents.append(completed_agent)
                            completed_count += 1
                            
                            # Format and stream individual result
                            formatted_result = format_individual_agent_result(completed_agent, result)
                            
                            progress = int((completed_count / len(agents_to_invoke)) * 70) + 30  # 30-100%
                            send_progress_update(connection_id, job_id, 'processing', 
                                               f'Completed {completed_agent} analysis ({completed_count}/{len(agents_to_invoke)})', 
                                               progress)
                            
                            # Send streaming update
                            send_websocket_message(connection_id, {
                                'type': 'agent_completed',
                                'jobId': job_id,
                                'agent': completed_agent,
                                'result': formatted_result,
                                'progress': progress,
                                'completed_agents': completed_agents,
                                'total_agents': len(agents_to_invoke)
                            })
                            
                        except concurrent.futures.TimeoutError:
                            logger.error(f"Timeout waiting for {completed_agent} agent result")
                            agent_results[completed_agent] = {"error": f"{completed_agent} agent timeout after 10 seconds"}
                            completed_agents.append(completed_agent)
                            completed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing {completed_agent} result: {str(e)}")
                            agent_results[completed_agent] = {"error": f"{completed_agent} agent error: {str(e)}"}
                            completed_agents.append(completed_agent)
                            completed_count += 1
                
                # Handle any remaining unfinished futures
                for agent_name, future in agent_futures.items():
                    if agent_name not in agent_results:
                        try:
                            # Try to get result with short timeout
                            result = future.result(timeout=1)
                            agent_results[agent_name] = result
                            completed_agents.append(agent_name)
                        except:
                            # Agent didn't complete in time
                            logger.warning(f"Agent {agent_name} did not complete in time")
                            agent_results[agent_name] = {"error": f"{agent_name} agent did not complete within timeout"}
                            completed_agents.append(agent_name)
                            
                            # Send error result
                            formatted_result = format_individual_agent_result(agent_name, agent_results[agent_name])
                            send_websocket_message(connection_id, {
                                'type': 'agent_completed',
                                'jobId': job_id,
                                'agent': agent_name,
                                'result': formatted_result,
                                'progress': 90,
                                'completed_agents': completed_agents,
                                'total_agents': len(agents_to_invoke)
                            })
        else:
            # Single agent invocation
            agent = agents_to_invoke[0]
            send_progress_update(connection_id, job_id, 'processing', f'Processing {agent} analysis...', 50)
            
            if agent == 'cost_forecast':
                result = invoke_cost_forecast_agent(query)
            elif agent == 'trusted_advisor':
                result = invoke_trusted_advisor_agent(query)
            elif agent == 'budget_management':
                result = invoke_budget_management_agent(query)
            else:
                result = {"error": f"Unknown agent: {agent}"}
            
            agent_results[agent] = result
            completed_agents.append(agent)
            
            # Stream single result
            formatted_result = format_individual_agent_result(agent, result)
            send_websocket_message(connection_id, {
                'type': 'agent_completed',
                'jobId': job_id,
                'agent': agent,
                'result': formatted_result,
                'progress': 90,
                'completed_agents': completed_agents,
                'total_agents': 1
            })
        
        # Step 3: Build final combined response
        final_response = build_combined_response_streaming(agents_to_invoke, agent_results, query)
        
        # Send completion message
        send_websocket_message(connection_id, {
            'type': 'analysis_completed',
            'jobId': job_id,
            'final_response': final_response,
            'total_agents': len(agents_to_invoke),
            'completed_agents': len(agent_results),
            'processing_time': f"Completed with {len(agent_results)} agents using parallel processing"
        })
        
        return {
            "query": query,
            "response": final_response,
            "agent": "AWS-FinOps-WebSocket-Supervisor-Streaming",
            "timestamp": int(time.time()),
            "agents_invoked": agents_to_invoke,
            "source": "streaming_supervisor"
        }
        
    except Exception as e:
        logger.error(f"Error in streaming supervisor: {str(e)}")
        send_websocket_message(connection_id, {
            'type': 'analysis_error',
            'jobId': job_id,
            'error': str(e)
        })
        return {"error": f"Streaming supervisor failed: {str(e)}"}

def determine_agents_for_query(query: str) -> list:
    """Simple routing logic to determine which agents to invoke."""
    query_lower = query.lower()
    agents = []
    
    # Multi-part query patterns
    if ('forecast' in query_lower and 'budget' in query_lower) or \
       ('prediction' in query_lower and 'budget' in query_lower):
        return ['cost_forecast', 'budget_management']
    
    if ('cost' in query_lower and 'optim' in query_lower):
        return ['cost_forecast', 'trusted_advisor']
    
    if ('comprehensive' in query_lower or 'complete' in query_lower or 
        'everything' in query_lower or 'all aspects' in query_lower):
        return ['cost_forecast', 'trusted_advisor', 'budget_management']
    
    # Single agent routing
    if any(word in query_lower for word in ['budget', 'spending limit', 'cost control']):
        agents.append('budget_management')
    
    if any(word in query_lower for word in ['cost', 'spending', 'expense', 'forecast']):
        agents.append('cost_forecast')
    
    if any(word in query_lower for word in ['optimize', 'saving', 'reduce', 'efficiency']):
        agents.append('trusted_advisor')
    
    # Default to cost forecast if no clear match
    if not agents:
        agents = ['cost_forecast']
    
    return agents

def invoke_cost_forecast_agent(query: str) -> Dict[str, Any]:
    """Invoke the Cost Forecast Agent."""
    try:
        response = lambda_client.invoke(
            FunctionName='aws-cost-forecast-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        return json.loads(response['Payload'].read())
    except Exception as e:
        return {"error": f"Cost forecast agent error: {str(e)}"}

def invoke_trusted_advisor_agent(query: str) -> Dict[str, Any]:
    """Invoke the Trusted Advisor Agent."""
    try:
        response = lambda_client.invoke(
            FunctionName='trusted-advisor-agent-trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        return json.loads(response['Payload'].read())
    except Exception as e:
        return {"error": f"Trusted advisor agent error: {str(e)}"}

def invoke_budget_management_agent(query: str) -> Dict[str, Any]:
    """Invoke the Budget Management Agent."""
    try:
        response = lambda_client.invoke(
            FunctionName='budget-management-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": query})
        )
        return json.loads(response['Payload'].read())
    except Exception as e:
        return {"error": f"Budget management agent error: {str(e)}"}

def format_individual_agent_result(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Format individual agent result for streaming."""
    try:
        if "body" in result and not result.get("error"):
            try:
                body = json.loads(result["body"]) if isinstance(result["body"], str) else result["body"]
                response_text = body.get('response', 'No data available')
            except:
                response_text = result.get('body', 'No data available')
        elif result.get("error"):
            response_text = f"⚠️ {result['error']}"
        else:
            response_text = "No data available"
        
        # Agent-specific formatting
        agent_titles = {
            'cost_forecast': '📊 Cost Analysis',
            'trusted_advisor': '💡 Optimization Recommendations', 
            'budget_management': '🎯 Budget Management & Cost Controls'
        }
        
        return {
            'agent': agent_name,
            'title': agent_titles.get(agent_name, f'{agent_name.title()} Analysis'),
            'content': response_text,
            'status': 'completed' if not result.get("error") else 'error',
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'agent': agent_name,
            'title': f'{agent_name.title()} Analysis',
            'content': f"Error formatting result: {str(e)}",
            'status': 'error',
            'timestamp': time.time()
        }

def build_combined_response_streaming(agents: list, results: Dict[str, Any], query: str) -> str:
    """Build the final combined response from streaming agent results."""
    combined_response = f"# 🏦 Comprehensive AWS FinOps Analysis\n\n"
    
    # Add routing explanation
    combined_response += f"**Query Analysis:** Routed to {len(agents)} specialized agent(s) for optimal analysis.\n\n"
    
    # Add individual agent sections
    for agent in agents:
        if agent in results:
            result = results[agent]
            if "body" in result and not result.get("error"):
                try:
                    body = json.loads(result["body"]) if isinstance(result["body"], str) else result["body"]
                    content = body.get('response', 'No data available')
                except:
                    content = result.get('body', 'No data available')
            elif result.get("error"):
                content = f"⚠️ {result['error']}"
            else:
                content = "No data available"
            
            # Add section based on agent type
            if agent == 'cost_forecast':
                combined_response += f"## 📊 Cost Analysis\n\n{content}\n\n"
            elif agent == 'trusted_advisor':
                combined_response += f"## 💡 Optimization Recommendations\n\n{content}\n\n"
            elif agent == 'budget_management':
                combined_response += f"## 🎯 Budget Management & Cost Controls\n\n{content}\n\n"
    
    # Add summary if multiple agents
    if len(agents) > 1:
        combined_response += f"## 📋 Integrated FinOps Strategy\n\n"
        combined_response += f"This analysis combines insights from {len(agents)} specialized agents using parallel processing with real-time streaming updates. "
        combined_response += f"Each section provides targeted recommendations for your AWS financial operations.\n\n"
        combined_response += f"*⚡ Analysis completed using streaming parallel processing for optimal performance.*"
    
    return combined_response

def send_websocket_message(connection_id: str, message: Dict[str, Any]):
    """Send a message via WebSocket."""
    try:
        apigateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        logger.info(f"Sent streaming message: {message.get('type', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to send streaming message: {str(e)}")
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
