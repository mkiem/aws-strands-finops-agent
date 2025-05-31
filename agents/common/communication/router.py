"""
Message Router module for agent communication.

This module provides routing functionality for messages between agents,
handling message delivery, tracking, and error handling.
"""

import json
import time
import logging
import boto3
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor

from .message import Message, MessageType, MessageStatus
from .registry import AgentRegistry

# Configure logging
logger = logging.getLogger(__name__)

class MessageRouter:
    """
    Message Router for handling communication between agents.
    
    This class is responsible for routing messages between agents,
    handling message delivery, tracking, and error handling.
    """
    
    def __init__(self, agent_registry: AgentRegistry, lambda_client=None, dynamodb_client=None):
        """
        Initialize the Message Router.
        
        Args:
            agent_registry: Registry of available agents
            lambda_client: Optional boto3 Lambda client (for testing)
            dynamodb_client: Optional boto3 DynamoDB client (for testing)
        """
        self.agent_registry = agent_registry
        self.lambda_client = lambda_client or boto3.client('lambda')
        self.dynamodb_client = dynamodb_client or boto3.client('dynamodb')
        self.message_handlers = {}
        self.message_history = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.local_handlers = {}
    
    def register_handler(self, message_type: MessageType, handler_func: Callable[[Message], Optional[Message]]) -> None:
        """
        Register a handler function for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler_func: Function to handle the message
        """
        self.local_handlers[message_type] = handler_func
        logger.info(f"Registered local handler for message type: {message_type.value}")
    
    def send_message(self, message: Message, synchronous: bool = False) -> Optional[Message]:
        """
        Send a message to its recipient.
        
        Args:
            message: Message to send
            synchronous: Whether to wait for a response
            
        Returns:
            Response message if synchronous, None otherwise
        """
        # Update message status
        message.update_status(MessageStatus.SENT)
        
        # Store message in history
        self.message_history[message.message_id] = message
        
        # Check if recipient is a local handler
        if not message.recipient_id and message.message_type in self.local_handlers:
            logger.info(f"Routing message {message.message_id} to local handler for {message.message_type.value}")
            return self._handle_locally(message)
        
        # Get recipient agent info
        recipient_info = self.agent_registry.get_agent(message.recipient_id)
        if not recipient_info:
            logger.error(f"Unknown recipient: {message.recipient_id}")
            error_message = message.create_error_response(
                error_message=f"Unknown recipient: {message.recipient_id}",
                error_code="UNKNOWN_RECIPIENT"
            )
            return error_message
        
        # Route based on agent type
        if recipient_info.get("type") == "lambda":
            return self._send_to_lambda(message, recipient_info, synchronous)
        else:
            logger.error(f"Unsupported agent type: {recipient_info.get('type')}")
            error_message = message.create_error_response(
                error_message=f"Unsupported agent type: {recipient_info.get('type')}",
                error_code="UNSUPPORTED_AGENT_TYPE"
            )
            return error_message
    
    def _handle_locally(self, message: Message) -> Optional[Message]:
        """
        Handle a message locally using registered handlers.
        
        Args:
            message: Message to handle
            
        Returns:
            Response message if available
        """
        handler = self.local_handlers.get(message.message_type)
        if not handler:
            logger.error(f"No local handler for message type: {message.message_type.value}")
            return message.create_error_response(
                error_message=f"No local handler for message type: {message.message_type.value}",
                error_code="NO_HANDLER"
            )
        
        try:
            message.update_status(MessageStatus.PROCESSING)
            response = handler(message)
            message.update_status(MessageStatus.COMPLETED)
            
            if response:
                response.update_status(MessageStatus.SENT)
                self.message_history[response.message_id] = response
            
            return response
        except Exception as e:
            logger.error(f"Error handling message locally: {str(e)}", exc_info=True)
            message.update_status(MessageStatus.FAILED)
            return message.create_error_response(
                error_message=f"Error handling message: {str(e)}",
                error_code="HANDLER_ERROR",
                details={"exception": str(e)}
            )
    
    def _send_to_lambda(self, message: Message, recipient_info: Dict[str, Any], synchronous: bool) -> Optional[Message]:
        """
        Send a message to a Lambda function.
        
        Args:
            message: Message to send
            recipient_info: Information about the recipient
            synchronous: Whether to wait for a response
            
        Returns:
            Response message if synchronous, None otherwise
        """
        function_name = recipient_info.get("function_name")
        if not function_name:
            logger.error(f"No function name for Lambda agent: {message.recipient_id}")
            return message.create_error_response(
                error_message=f"No function name for Lambda agent: {message.recipient_id}",
                error_code="MISSING_FUNCTION_NAME"
            )
        
        # Prepare payload
        payload = {
            "message": message.to_dict()
        }
        
        try:
            if synchronous:
                # Invoke synchronously
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                # Process response
                if response['StatusCode'] == 200:
                    response_payload = json.loads(response['Payload'].read().decode('utf-8'))
                    if 'message' in response_payload:
                        response_message = Message.from_dict(response_payload['message'])
                        self.message_history[response_message.message_id] = response_message
                        message.update_status(MessageStatus.COMPLETED)
                        return response_message
                    else:
                        logger.warning(f"Lambda response missing message: {response_payload}")
                        message.update_status(MessageStatus.COMPLETED)
                        return None
                else:
                    logger.error(f"Lambda invocation failed: {response}")
                    message.update_status(MessageStatus.FAILED)
                    return message.create_error_response(
                        error_message=f"Lambda invocation failed with status code: {response['StatusCode']}",
                        error_code="LAMBDA_ERROR",
                        details={"status_code": response['StatusCode']}
                    )
            else:
                # Invoke asynchronously
                self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                )
                message.update_status(MessageStatus.DELIVERED)
                return None
                
        except Exception as e:
            logger.error(f"Error invoking Lambda function: {str(e)}", exc_info=True)
            message.update_status(MessageStatus.FAILED)
            return message.create_error_response(
                error_message=f"Error invoking Lambda function: {str(e)}",
                error_code="LAMBDA_INVOCATION_ERROR",
                details={"exception": str(e)}
            )
    
    def send_message_async(self, message: Message) -> None:
        """
        Send a message asynchronously.
        
        Args:
            message: Message to send
        """
        self.executor.submit(self.send_message, message, False)
    
    def broadcast(self, message_type: MessageType, content: Dict[str, Any], sender_id: str = "") -> List[str]:
        """
        Broadcast a message to all registered agents.
        
        Args:
            message_type: Type of message to broadcast
            content: Content of the message
            sender_id: ID of the sender
            
        Returns:
            List of message IDs
        """
        message_ids = []
        agents = self.agent_registry.list_agents()
        
        for agent_id, agent_info in agents.items():
            if agent_id != sender_id:  # Don't send to self
                message = Message(
                    message_type=message_type,
                    content=content,
                    sender_id=sender_id,
                    recipient_id=agent_id
                )
                self.send_message_async(message)
                message_ids.append(message.message_id)
        
        return message_ids
    
    def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """
        Get the status of a message.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Message status if found, None otherwise
        """
        if message_id in self.message_history:
            return self.message_history[message_id].status
        return None
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get a message by ID.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Message if found, None otherwise
        """
        return self.message_history.get(message_id)
    
    def get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages in the conversation
        """
        return [
            message for message in self.message_history.values()
            if message.conversation_id == conversation_id
        ]
    
    def clear_history(self, max_age_seconds: Optional[float] = None) -> int:
        """
        Clear message history.
        
        Args:
            max_age_seconds: Maximum age of messages to keep
            
        Returns:
            Number of messages cleared
        """
        if max_age_seconds is None:
            # Clear all
            count = len(self.message_history)
            self.message_history = {}
            return count
        else:
            # Clear old messages
            current_time = time.time()
            to_remove = [
                message_id for message_id, message in self.message_history.items()
                if current_time - message.timestamp > max_age_seconds
            ]
            
            for message_id in to_remove:
                del self.message_history[message_id]
            
            return len(to_remove)
