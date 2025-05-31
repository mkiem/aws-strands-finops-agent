"""
Agent Communication Framework.

This package provides the communication framework for the FinOps multi-agent system,
enabling agents to exchange messages, share context, and collaborate effectively.
"""

from .message import Message, MessageType, MessageStatus
from .context import ConversationContext
from .router import MessageRouter
from .registry import AgentRegistry

__all__ = [
    'Message',
    'MessageType',
    'MessageStatus',
    'ConversationContext',
    'MessageRouter',
    'AgentRegistry'
]
