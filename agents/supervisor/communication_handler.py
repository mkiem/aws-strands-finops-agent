"""
Communication Handler for the FinOps Supervisor Agent.

This module integrates the Supervisor Agent with the communication framework,
enabling it to exchange messages with specialized agents.
"""

import os
import json
import logging
import boto3
from typing import Dict, Any, Optional, List

from ..common.communication import (
    Message, MessageType, MessageStatus,
    ConversationContext, MessageRouter, AgentRegistry
)

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorCommunicationHandler:
    """
    Communication Handler for the FinOps Supervisor Agent.
    
    This class integrates the Supervisor Agent with the communication framework,
    enabling it to exchange messages with specialized agents.
    """
    
    def __init__(self):
        """Initialize the Communication Handler."""
        # Initialize agent registry
        self.agent_registry = AgentRegistry()
        
        # Register known agents
        self._register_known_agents()
        
        # Initialize message router
        self.message_router = MessageRouter(self.agent_registry)
        
        # Register message handlers
        self._register_message_handlers()
    
    def _register_known_agents(self):
        """Register known agents in the registry."""
        # Register Cost Analysis Agent
        cost_analysis_function = os.environ.get('COST_ANALYSIS_FUNCTION', 'finops-cost-analysis-agent')
        self.agent_registry.register_agent(
            agent_id="cost-analysis-agent",
            agent_info={
                "name": "Cost Analysis Agent",
                "description": "Analyzes AWS cost data",
                "type": "lambda",
                "function_name": cost_analysis_function,
                "capabilities": ["cost_analysis", "forecasting", "comparison"]
            }
        )
        
        # Register Cost Optimization Agent
        optimization_function = os.environ.get('OPTIMIZATION_FUNCTION', 'finops-optimization-agent')
        self.agent_registry.register_agent(
            agent_id="cost-optimization-agent",
            agent_info={
                "name": "Cost Optimization Agent",
                "description": "Provides cost optimization recommendations",
                "type": "lambda",
                "function_name": optimization_function,
                "capabilities": ["optimization", "resource_utilization"]
            }
        )
    
    def _register_message_handlers(self):
        """Register message handlers for different message types."""
        self.message_router.register_handler(
            MessageType.RESULT,
            self._handle_result_message
        )
        
        self.message_router.register_handler(
            MessageType.ERROR,
            self._handle_error_message
        )
        
        self.message_router.register_handler(
            MessageType.HEARTBEAT,
            self._handle_heartbeat_message
        )
    
    def _handle_result_message(self, message: Message) -> Optional[Message]:
        """
        Handle a result message.
        
        Args:
            message: Result message
            
        Returns:
            Response message if needed
        """
        logger.info(f"Received result message: {message.message_id}")
        
        # Process the result
        # In a real implementation, this would update the conversation state
        # and potentially trigger additional actions
        
        # For now, just acknowledge receipt
        return message.create_response(
            content={"status": "received"},
            message_type=MessageType.ACK
        )
    
    def _handle_error_message(self, message: Message) -> Optional[Message]:
        """
        Handle an error message.
        
        Args:
            message: Error message
            
        Returns:
            Response message if needed
        """
        logger.warning(f"Received error message: {message.message_id}")
        error_content = message.content
        
        # Log the error
        logger.error(
            f"Agent error: {error_content.get('error_code', 'UNKNOWN')}: "
            f"{error_content.get('error_message', 'No message')}"
        )
        
        # For now, just acknowledge receipt
        return message.create_response(
            content={"status": "error_logged"},
            message_type=MessageType.ACK
        )
    
    def _handle_heartbeat_message(self, message: Message) -> Optional[Message]:
        """
        Handle a heartbeat message.
        
        Args:
            message: Heartbeat message
            
        Returns:
            Response message if needed
        """
        # Update agent heartbeat
        if message.sender_id:
            self.agent_registry.update_heartbeat(message.sender_id)
        
        # Respond with acknowledgement
        return message.create_response(
            content={"status": "alive", "timestamp": message.timestamp},
            message_type=MessageType.ACK
        )
    
    def send_cost_analysis_request(self, parameters: Dict[str, Any], conversation_context: ConversationContext) -> Message:
        """
        Send a cost analysis request to the Cost Analysis Agent.
        
        Args:
            parameters: Parameters for the cost analysis
            conversation_context: Conversation context
            
        Returns:
            Response message
        """
        # Create message
        message = Message(
            message_type=MessageType.COST_ANALYSIS,
            content={
                "parameters": parameters,
                "context": conversation_context.to_dict()
            },
            sender_id="supervisor-agent",
            recipient_id="cost-analysis-agent",
            conversation_id=conversation_context.conversation_id
        )
        
        # Send message and wait for response
        response = self.message_router.send_message(message, synchronous=True)
        
        if not response:
            # Create error response if no response received
            response = message.create_error_response(
                error_message="No response received from Cost Analysis Agent",
                error_code="NO_RESPONSE"
            )
        
        return response
    
    def send_optimization_request(self, parameters: Dict[str, Any], conversation_context: ConversationContext) -> Message:
        """
        Send an optimization request to the Cost Optimization Agent.
        
        Args:
            parameters: Parameters for the optimization
            conversation_context: Conversation context
            
        Returns:
            Response message
        """
        # Create message
        message = Message(
            message_type=MessageType.OPTIMIZATION,
            content={
                "parameters": parameters,
                "context": conversation_context.to_dict()
            },
            sender_id="supervisor-agent",
            recipient_id="cost-optimization-agent",
            conversation_id=conversation_context.conversation_id
        )
        
        # Send message and wait for response
        response = self.message_router.send_message(message, synchronous=True)
        
        if not response:
            # Create error response if no response received
            response = message.create_error_response(
                error_message="No response received from Cost Optimization Agent",
                error_code="NO_RESPONSE"
            )
        
        return response
    
    def send_forecast_request(self, parameters: Dict[str, Any], conversation_context: ConversationContext) -> Message:
        """
        Send a forecast request to the Cost Analysis Agent.
        
        Args:
            parameters: Parameters for the forecast
            conversation_context: Conversation context
            
        Returns:
            Response message
        """
        # Create message
        message = Message(
            message_type=MessageType.FORECAST,
            content={
                "parameters": parameters,
                "context": conversation_context.to_dict()
            },
            sender_id="supervisor-agent",
            recipient_id="cost-analysis-agent",
            conversation_id=conversation_context.conversation_id
        )
        
        # Send message and wait for response
        response = self.message_router.send_message(message, synchronous=True)
        
        if not response:
            # Create error response if no response received
            response = message.create_error_response(
                error_message="No response received from Cost Analysis Agent",
                error_code="NO_RESPONSE"
            )
        
        return response
    
    def send_comparison_request(self, parameters: Dict[str, Any], conversation_context: ConversationContext) -> Message:
        """
        Send a comparison request to the Cost Analysis Agent.
        
        Args:
            parameters: Parameters for the comparison
            conversation_context: Conversation context
            
        Returns:
            Response message
        """
        # Create message
        message = Message(
            message_type=MessageType.COMPARISON,
            content={
                "parameters": parameters,
                "context": conversation_context.to_dict()
            },
            sender_id="supervisor-agent",
            recipient_id="cost-analysis-agent",
            conversation_id=conversation_context.conversation_id
        )
        
        # Send message and wait for response
        response = self.message_router.send_message(message, synchronous=True)
        
        if not response:
            # Create error response if no response received
            response = message.create_error_response(
                error_message="No response received from Cost Analysis Agent",
                error_code="NO_RESPONSE"
            )
        
        return response
    
    def process_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from another agent.
        
        Args:
            message_data: Message data
            
        Returns:
            Response data
        """
        try:
            # Parse message
            message = Message.from_dict(message_data)
            
            # Route message to appropriate handler
            response = self.message_router.send_message(message, synchronous=True)
            
            if response:
                return response.to_dict()
            else:
                return {
                    "message_type": "error",
                    "content": {
                        "error_message": "No response generated",
                        "error_code": "NO_RESPONSE"
                    }
                }
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}", exc_info=True)
            return {
                "message_type": "error",
                "content": {
                    "error_message": f"Error processing message: {str(e)}",
                    "error_code": "PROCESSING_ERROR"
                }
            }
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get a list of active agents.
        
        Returns:
            List of active agent information
        """
        active_agents = self.agent_registry.get_active_agents()
        return [
            {
                "agent_id": agent_id,
                "name": info.get("name", agent_id),
                "capabilities": info.get("capabilities", []),
                "last_heartbeat": info.get("last_heartbeat", 0)
            }
            for agent_id, info in active_agents.items()
        ]
