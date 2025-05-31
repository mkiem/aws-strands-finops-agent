"""
Conversation Context module for agent communication.

This module provides context management for conversations between agents,
enabling context sharing and persistence across agent invocations.
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class ConversationContext:
    """
    Conversation Context for maintaining state across agent interactions.
    
    This class represents the shared context for a conversation, including
    conversation history, extracted parameters, and agent-specific state.
    """
    
    # Conversation identification
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    
    # Conversation history
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Extracted parameters and entities
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Agent-specific state
    agent_state: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            Dict representation of the context
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert the context to a JSON string.
        
        Returns:
            JSON string representation of the context
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """
        Create a ConversationContext from a dictionary.
        
        Args:
            data: Dictionary containing context data
            
        Returns:
            ConversationContext object
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversationContext':
        """
        Create a ConversationContext from a JSON string.
        
        Args:
            json_str: JSON string containing context data
            
        Returns:
            ConversationContext object
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            metadata: Additional metadata for the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.updated_at = time.time()
    
    def update_parameters(self, new_parameters: Dict[str, Any]) -> None:
        """
        Update the extracted parameters.
        
        Args:
            new_parameters: New parameters to add/update
        """
        self.parameters.update(new_parameters)
        self.updated_at = time.time()
    
    def get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the state for a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent state dictionary
        """
        if agent_id not in self.agent_state:
            self.agent_state[agent_id] = {}
        
        return self.agent_state[agent_id]
    
    def update_agent_state(self, agent_id: str, state_updates: Dict[str, Any]) -> None:
        """
        Update the state for a specific agent.
        
        Args:
            agent_id: ID of the agent
            state_updates: State updates to apply
        """
        if agent_id not in self.agent_state:
            self.agent_state[agent_id] = {}
        
        self.agent_state[agent_id].update(state_updates)
        self.updated_at = time.time()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent messages from the conversation history.
        
        Args:
            count: Number of messages to retrieve
            
        Returns:
            List of recent messages
        """
        return self.messages[-count:] if self.messages else []
    
    def get_conversation_summary(self) -> str:
        """
        Generate a summary of the conversation.
        
        Returns:
            Summary string
        """
        if not self.messages:
            return "No conversation history."
        
        # Count messages by role
        role_counts = {}
        for message in self.messages:
            role = message.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Format summary
        summary_parts = [
            f"Conversation ID: {self.conversation_id}",
            f"Messages: {len(self.messages)} total"
        ]
        
        for role, count in role_counts.items():
            summary_parts.append(f"- {role}: {count}")
        
        if self.parameters:
            summary_parts.append(f"Parameters: {len(self.parameters)} extracted")
        
        first_timestamp = self.messages[0].get("timestamp") if self.messages else None
        last_timestamp = self.messages[-1].get("timestamp") if self.messages else None
        
        if first_timestamp and last_timestamp:
            summary_parts.append(f"Timespan: {first_timestamp} to {last_timestamp}")
        
        return "\n".join(summary_parts)
    
    def prune_history(self, max_messages: int = 50) -> None:
        """
        Prune the conversation history to limit its size.
        
        Args:
            max_messages: Maximum number of messages to keep
        """
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
            self.updated_at = time.time()
            self.metadata["pruned_at"] = datetime.utcnow().isoformat()
            self.metadata["pruned_count"] = self.metadata.get("pruned_count", 0) + 1
