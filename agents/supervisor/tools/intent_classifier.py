"""
Intent Classifier Tool for the FinOps Supervisor Agent.

This tool analyzes user messages to determine the intent and categorize
the request for appropriate handling.
"""

import logging
from typing import Dict, Any, List
from strands_agents.tools import Tool

# Configure logging
logger = logging.getLogger(__name__)

class IntentClassifierTool(Tool):
    """
    Tool for classifying the intent of user messages.
    
    This tool analyzes the user's message to determine what type of request
    it is (cost analysis, optimization, etc.) and which specialized agent(s)
    should handle it.
    """
    
    name = "intent_classifier"
    description = "Analyzes user messages to determine the intent and categorize the request"
    
    # Define intent categories
    INTENTS = {
        "COST_ANALYSIS": {
            "description": "Requests for cost data, analysis, or trends",
            "keywords": [
                "cost", "spend", "bill", "invoice", "charge", "expense",
                "how much", "total cost", "monthly cost", "analyze cost",
                "cost breakdown", "spending", "budget"
            ]
        },
        "COST_OPTIMIZATION": {
            "description": "Requests for cost-saving recommendations or optimization",
            "keywords": [
                "optimize", "save", "reduce", "lower", "decrease", "cut",
                "saving", "recommendation", "suggestion", "improve",
                "efficient", "cheaper", "cost-effective", "right-size"
            ]
        },
        "RESOURCE_UTILIZATION": {
            "description": "Queries about resource usage and efficiency",
            "keywords": [
                "utilization", "usage", "efficiency", "performance",
                "underutilized", "overprovisioned", "idle", "waste",
                "capacity", "right-size", "sizing"
            ]
        },
        "FORECASTING": {
            "description": "Requests for cost predictions or forecasts",
            "keywords": [
                "forecast", "predict", "projection", "estimate", "future cost",
                "next month", "next quarter", "budget planning", "trend"
            ]
        },
        "COMPARISON": {
            "description": "Requests to compare costs between periods or services",
            "keywords": [
                "compare", "comparison", "difference", "versus", "vs",
                "month over month", "year over year", "service comparison"
            ]
        },
        "GENERAL_INFORMATION": {
            "description": "General questions about AWS services or FinOps",
            "keywords": [
                "what is", "how does", "explain", "tell me about",
                "information", "details", "help me understand"
            ]
        }
    }
    
    def _run(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze the message to determine the user's intent.
        
        Args:
            message: The user's message
            context: Optional context information
            
        Returns:
            Dict containing the classified intent(s) and confidence scores
        """
        logger.info(f"Classifying intent for message: {message[:50]}...")
        
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Calculate scores for each intent based on keyword matches
        intent_scores = {}
        for intent, data in self.INTENTS.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword.lower() in message_lower:
                    # Increase score based on keyword length (longer keywords are more specific)
                    score += len(keyword) / 3
            intent_scores[intent] = score
        
        # Sort intents by score (descending)
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get primary and secondary intents (if they have non-zero scores)
        primary_intent = sorted_intents[0][0] if sorted_intents[0][1] > 0 else "GENERAL_INFORMATION"
        primary_score = sorted_intents[0][1]
        
        secondary_intent = None
        secondary_score = 0
        if len(sorted_intents) > 1 and sorted_intents[1][1] > 0:
            secondary_intent = sorted_intents[1][0]
            secondary_score = sorted_intents[1][1]
        
        # Determine which agents to involve
        agents_to_invoke = []
        if primary_intent in ["COST_ANALYSIS", "FORECASTING", "COMPARISON"]:
            agents_to_invoke.append("COST_ANALYSIS")
        
        if primary_intent in ["COST_OPTIMIZATION", "RESOURCE_UTILIZATION"]:
            agents_to_invoke.append("COST_OPTIMIZATION")
        
        # For some intents, we might need both agents
        if primary_intent == "GENERAL_INFORMATION" or (secondary_intent and secondary_score > primary_score * 0.7):
            if "COST_ANALYSIS" not in agents_to_invoke:
                agents_to_invoke.append("COST_ANALYSIS")
            if "COST_OPTIMIZATION" not in agents_to_invoke:
                agents_to_invoke.append("COST_OPTIMIZATION")
        
        result = {
            "primary_intent": primary_intent,
            "primary_score": primary_score,
            "secondary_intent": secondary_intent,
            "secondary_score": secondary_score,
            "agents_to_invoke": agents_to_invoke,
            "intent_scores": intent_scores
        }
        
        logger.info(f"Intent classification result: {result}")
        return result
