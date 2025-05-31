"""
FinOps Supervisor Agent - Main Agent Module

This module implements the core functionality of the FinOps Supervisor Agent,
which orchestrates the multi-agent system for AWS cost management.
"""

import os
import json
import logging
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import Strands SDK components
from strands_agents import Agent, Message, AgentConfig
from strands_agents.tools import Tool

# Import communication framework
from ..common.communication import ConversationContext
from .communication_handler import SupervisorCommunicationHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinOpsSupervisorAgent:
    """
    FinOps Supervisor Agent that orchestrates the multi-agent system.
    
    This agent is responsible for:
    1. Processing natural language queries related to AWS costs
    2. Determining which specialized agent(s) to invoke
    3. Coordinating communication between specialized agents
    4. Synthesizing responses from multiple agents into coherent answers
    5. Maintaining conversation context and history
    """
    
    def __init__(self, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """
        Initialize the FinOps Supervisor Agent.
        
        Args:
            model_id: The ID of the Bedrock model to use for the agent
        """
        self.model_id = model_id
        self.conversation_history = []
        self.lambda_client = boto3.client('lambda')
        self.cost_analysis_function = os.environ.get('COST_ANALYSIS_FUNCTION', 'finops-cost-analysis-agent')
        self.optimization_function = os.environ.get('OPTIMIZATION_FUNCTION', 'finops-optimization-agent')
        
        # Initialize the Strands Agent
        self.agent = self._initialize_agent()
        
        # Initialize the communication handler
        self.comm_handler = SupervisorCommunicationHandler()
        
        logger.info(f"FinOps Supervisor Agent initialized with model: {model_id}")
    
    def _initialize_agent(self) -> Agent:
        """
        Initialize the Strands Agent with appropriate configuration.
        
        Returns:
            Agent: Configured Strands Agent
        """
        # Define agent configuration
        config = AgentConfig(
            model=self.model_id,
            temperature=0.2,  # Lower temperature for more deterministic responses
            max_tokens=4096,  # Allow for detailed responses
            system_prompt=self._get_system_prompt()
        )
        
        # Create the agent with tools
        agent = Agent(config=config, tools=self._get_tools())
        
        return agent
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the agent.
        
        Returns:
            str: System prompt
        """
        return """
        You are the FinOps Supervisor Agent, an AI assistant specialized in AWS cost management and optimization.
        Your role is to help users understand their AWS costs, identify optimization opportunities, and provide
        actionable recommendations to reduce cloud spending.
        
        You have access to specialized agents:
        1. Cost Analysis Agent: For retrieving and analyzing AWS cost data
        2. Cost Optimization Agent: For identifying cost-saving opportunities
        
        When responding to user queries:
        - Determine which specialized agent(s) to invoke based on the query
        - Coordinate communication between specialized agents when needed
        - Synthesize information from multiple sources into coherent answers
        - Maintain conversation context to provide consistent responses
        - Be specific and actionable in your recommendations
        - Use clear, concise language appropriate for technical and non-technical users
        - Format numerical data appropriately (e.g., currency with two decimal places)
        
        Always prioritize accuracy and clarity in your responses.
        """
    
    def _get_tools(self) -> List[Tool]:
        """
        Get the tools available to the agent.
        
        Returns:
            List[Tool]: List of tools
        """
        # Import tools here to avoid circular imports
        from .tools.intent_classifier import IntentClassifierTool
        from .tools.parameter_extractor import ParameterExtractorTool
        from .tools.agent_invoker import AgentInvokerTool
        from .tools.response_synthesizer import ResponseSynthesizerTool
        
        return [
            IntentClassifierTool(),
            ParameterExtractorTool(),
            AgentInvokerTool(
                cost_analysis_function=self.cost_analysis_function,
                optimization_function=self.optimization_function,
                lambda_client=self.lambda_client
            ),
            ResponseSynthesizerTool()
        ]
    
    def process_message(self, user_message: str, conversation_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The message from the user
            conversation_id: Optional ID for the conversation
            user_id: Optional ID for the user
            
        Returns:
            Dict: Response containing the agent's message and metadata
        """
        try:
            # Create or retrieve conversation context
            conversation_context = self._get_conversation_context(conversation_id, user_id)
            
            # Add user message to conversation history and context
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            conversation_context.add_message("user", user_message)
            
            # Create message context with conversation history
            context = {
                "conversation_history": self.conversation_history,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Process the message with the agent
            message = Message(content=user_message, context=context)
            response = self.agent.process_message(message)
            
            # Add agent response to conversation history and context
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content,
                "timestamp": datetime.utcnow().isoformat()
            })
            conversation_context.add_message("assistant", response.content)
            
            # Limit conversation history size
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Format the response
            result = {
                "message": response.content,
                "conversation_id": conversation_context.conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": response.metadata
            }
            
            logger.info(f"Processed message: {user_message[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": f"I apologize, but I encountered an error while processing your request. Please try again or rephrase your question. Error details: {str(e)}",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _get_conversation_context(self, conversation_id: str = None, user_id: str = None) -> ConversationContext:
        """
        Get or create a conversation context.
        
        Args:
            conversation_id: Optional ID for the conversation
            user_id: Optional ID for the user
            
        Returns:
            ConversationContext: Conversation context
        """
        # In a real implementation, this would retrieve the context from a database
        # For now, create a new context each time
        return ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id
        )
    
    def process_agent_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message from another agent.
        
        Args:
            message_data: Message data from another agent
            
        Returns:
            Dict: Response data
        """
        return self.comm_handler.process_incoming_message(message_data)
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
