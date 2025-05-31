"""
Message module for agent communication.

This module defines the message structure and types used for communication
between agents in the FinOps multi-agent system.
"""

import uuid
import json
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict

class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    
    # Request types
    QUERY = "query"                  # General information request
    COST_ANALYSIS = "cost_analysis"  # Request for cost analysis
    OPTIMIZATION = "optimization"    # Request for optimization recommendations
    FORECAST = "forecast"            # Request for cost forecasting
    COMPARISON = "comparison"        # Request for comparison between periods/services
    
    # Response types
    RESULT = "result"                # General result message
    ERROR = "error"                  # Error message
    
    # Control messages
    HEARTBEAT = "heartbeat"          # Heartbeat/keep-alive message
    ACK = "acknowledgement"          # Acknowledgement of message receipt
    STATUS = "status"                # Status update

class MessageStatus(Enum):
    """Status of a message in the processing lifecycle."""
    
    CREATED = "created"              # Message has been created
    SENT = "sent"                    # Message has been sent
    DELIVERED = "delivered"          # Message has been delivered to recipient
    PROCESSING = "processing"        # Message is being processed
    COMPLETED = "completed"          # Processing has completed successfully
    FAILED = "failed"                # Processing has failed
    TIMEOUT = "timeout"              # Processing timed out

@dataclass
class Message:
    """
    Message class for agent communication.
    
    This class represents a message that can be exchanged between agents
    in the FinOps multi-agent system.
    """
    
    # Required fields
    message_type: MessageType
    content: Dict[str, Any]
    
    # Optional fields with defaults
    sender_id: str = field(default="")
    recipient_id: str = field(default="")
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = field(default=None)
    
    # Auto-generated fields
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    status: MessageStatus = field(default=MessageStatus.CREATED)
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dict representation of the message
        """
        result = asdict(self)
        # Convert enums to strings
        result["message_type"] = self.message_type.value
        result["status"] = self.status.value
        return result
    
    def to_json(self) -> str:
        """
        Convert the message to a JSON string.
        
        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a Message from a dictionary.
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            Message object
        """
        # Convert string values to enums
        if "message_type" in data and isinstance(data["message_type"], str):
            data["message_type"] = MessageType(data["message_type"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = MessageStatus(data["status"])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Create a Message from a JSON string.
        
        Args:
            json_str: JSON string containing message data
            
        Returns:
            Message object
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def create_response(self, content: Dict[str, Any], message_type: MessageType = MessageType.RESULT) -> 'Message':
        """
        Create a response message to this message.
        
        Args:
            content: Content of the response
            message_type: Type of the response message
            
        Returns:
            Response Message object
        """
        return Message(
            message_type=message_type,
            content=content,
            sender_id=self.recipient_id,
            recipient_id=self.sender_id,
            conversation_id=self.conversation_id,
            parent_id=self.message_id
        )
    
    def create_error_response(self, error_message: str, error_code: str = "UNKNOWN_ERROR", details: Dict[str, Any] = None) -> 'Message':
        """
        Create an error response message.
        
        Args:
            error_message: Error message
            error_code: Error code
            details: Additional error details
            
        Returns:
            Error Message object
        """
        content = {
            "error_message": error_message,
            "error_code": error_code,
            "details": details or {}
        }
        
        return self.create_response(content, MessageType.ERROR)
    
    def update_status(self, status: MessageStatus) -> None:
        """
        Update the status of this message.
        
        Args:
            status: New status
        """
        self.status = status
        self.metadata["status_history"] = self.metadata.get("status_history", []) + [
            {
                "status": status.value,
                "timestamp": time.time()
            }
        ]
