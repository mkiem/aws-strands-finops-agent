"""
Agent Invoker Tool for the FinOps Supervisor Agent.

This tool invokes specialized agents (Cost Analysis, Cost Optimization)
to process specific parts of user queries.
"""

import json
import logging
import boto3
from typing import Dict, Any, List, Optional
from strands_agents.tools import Tool

# Configure logging
logger = logging.getLogger(__name__)

class AgentInvokerTool(Tool):
    """
    Tool for invoking specialized agents.
    
    This tool handles the communication with specialized agents by invoking
    their Lambda functions and processing their responses.
    """
    
    name = "agent_invoker"
    description = "Invokes specialized agents to process specific parts of user queries"
    
    def __init__(self, cost_analysis_function: str, optimization_function: str, lambda_client=None):
        """
        Initialize the Agent Invoker Tool.
        
        Args:
            cost_analysis_function: Name of the Cost Analysis Agent Lambda function
            optimization_function: Name of the Cost Optimization Agent Lambda function
            lambda_client: Optional boto3 Lambda client (for testing)
        """
        super().__init__()
        self.cost_analysis_function = cost_analysis_function
        self.optimization_function = optimization_function
        self.lambda_client = lambda_client or boto3.client('lambda')
    
    def _run(self, agents_to_invoke: List[str], parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invoke specialized agents based on the intent and parameters.
        
        Args:
            agents_to_invoke: List of agent types to invoke
            parameters: Parameters extracted from the user message
            context: Optional context information
            
        Returns:
            Dict containing responses from the invoked agents
        """
        logger.info(f"Invoking agents: {agents_to_invoke}")
        
        results = {}
        
        # Prepare the payload for Lambda invocation
        payload = {
            "parameters": parameters,
            "context": context or {}
        }
        
        # Invoke Cost Analysis Agent if needed
        if "COST_ANALYSIS" in agents_to_invoke:
            try:
                cost_analysis_result = self._invoke_lambda(
                    self.cost_analysis_function,
                    payload
                )
                results["cost_analysis"] = cost_analysis_result
                logger.info("Successfully invoked Cost Analysis Agent")
            except Exception as e:
                logger.error(f"Error invoking Cost Analysis Agent: {str(e)}", exc_info=True)
                results["cost_analysis"] = {
                    "error": f"Failed to invoke Cost Analysis Agent: {str(e)}"
                }
        
        # Invoke Cost Optimization Agent if needed
        if "COST_OPTIMIZATION" in agents_to_invoke:
            try:
                optimization_result = self._invoke_lambda(
                    self.optimization_function,
                    payload
                )
                results["cost_optimization"] = optimization_result
                logger.info("Successfully invoked Cost Optimization Agent")
            except Exception as e:
                logger.error(f"Error invoking Cost Optimization Agent: {str(e)}", exc_info=True)
                results["cost_optimization"] = {
                    "error": f"Failed to invoke Cost Optimization Agent: {str(e)}"
                }
        
        return results
    
    def _invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a Lambda function and process the response.
        
        Args:
            function_name: Name of the Lambda function to invoke
            payload: Payload to send to the Lambda function
            
        Returns:
            Dict containing the Lambda function's response
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Process the response
            if response['StatusCode'] == 200:
                response_payload = json.loads(response['Payload'].read().decode('utf-8'))
                return response_payload
            else:
                logger.error(f"Lambda invocation failed with status code: {response['StatusCode']}")
                return {
                    "error": f"Lambda invocation failed with status code: {response['StatusCode']}"
                }
        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_name}: {str(e)}", exc_info=True)
            raise
