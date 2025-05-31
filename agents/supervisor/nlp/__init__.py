"""
Natural Language Processing module for the FinOps Supervisor Agent.

This package provides enhanced NLP capabilities for the FinOps Supervisor Agent,
including intent recognition, entity extraction, context-aware query processing,
natural language generation, and conversation flow management.
"""

from .intent_recognition import IntentRecognizer
from .entity_extraction import EntityExtractor
from .context_processor import ContextProcessor
from .response_generator import ResponseGenerator
from .conversation_manager import ConversationManager

__all__ = [
    'IntentRecognizer',
    'EntityExtractor',
    'ContextProcessor',
    'ResponseGenerator',
    'ConversationManager'
]
