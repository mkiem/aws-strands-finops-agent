"""
Intent Recognition module for the FinOps Supervisor Agent.

This module provides enhanced intent recognition capabilities,
including machine learning-based classification and compound intent detection.
"""

import re
import logging
import json
import os
from typing import Dict, Any, List, Tuple, Set, Optional
import boto3
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class IntentRecognizer:
    """
    Enhanced intent recognizer for the FinOps Supervisor Agent.
    
    This class provides sophisticated intent recognition capabilities,
    including machine learning-based classification and compound intent detection.
    """
    
    # Define intent categories with descriptions and examples
    INTENTS = {
        "COST_ANALYSIS": {
            "description": "Requests for cost data, analysis, or trends",
            "examples": [
                "What was my AWS cost last month?",
                "Show me the cost breakdown by service",
                "How much did I spend on EC2 instances?",
                "What's my current month-to-date spending?",
                "Show me my S3 costs for Q1"
            ],
            "keywords": [
                "cost", "spend", "bill", "invoice", "charge", "expense",
                "how much", "total cost", "monthly cost", "analyze cost",
                "cost breakdown", "spending", "budget", "expenditure"
            ]
        },
        "COST_OPTIMIZATION": {
            "description": "Requests for cost-saving recommendations or optimization",
            "examples": [
                "How can I reduce my AWS costs?",
                "Give me optimization recommendations",
                "What resources should I resize?",
                "Suggest ways to save money on AWS",
                "Help me optimize my cloud spending"
            ],
            "keywords": [
                "optimize", "save", "reduce", "lower", "decrease", "cut",
                "saving", "recommendation", "suggestion", "improve",
                "efficient", "cheaper", "cost-effective", "right-size",
                "optimization", "savings"
            ]
        },
        "RESOURCE_UTILIZATION": {
            "description": "Queries about resource usage and efficiency",
            "examples": [
                "Show me underutilized EC2 instances",
                "Which resources have low utilization?",
                "Are my RDS instances properly sized?",
                "Find idle resources in my account",
                "Show me usage patterns for my EBS volumes"
            ],
            "keywords": [
                "utilization", "usage", "efficiency", "performance",
                "underutilized", "overprovisioned", "idle", "waste",
                "capacity", "right-size", "sizing", "usage pattern",
                "resource usage", "cpu utilization", "memory usage"
            ]
        },
        "FORECASTING": {
            "description": "Requests for cost predictions or forecasts",
            "examples": [
                "What will my AWS bill be next month?",
                "Forecast my EC2 costs for Q3",
                "Predict my spending for the rest of the year",
                "How much will I spend on S3 next quarter?",
                "Project my cloud costs for the next 6 months"
            ],
            "keywords": [
                "forecast", "predict", "projection", "estimate", "future cost",
                "next month", "next quarter", "budget planning", "trend",
                "projection", "anticipated", "expected", "future spending",
                "outlook", "prediction"
            ]
        },
        "COMPARISON": {
            "description": "Requests to compare costs between periods or services",
            "examples": [
                "Compare my costs between January and February",
                "How did my EC2 costs change from last month?",
                "Compare S3 and EBS spending",
                "Show me month-over-month cost changes",
                "What's the difference in spending between Q1 and Q2?"
            ],
            "keywords": [
                "compare", "comparison", "difference", "versus", "vs",
                "month over month", "year over year", "service comparison",
                "change", "increased", "decreased", "higher", "lower",
                "more than", "less than", "compared to"
            ]
        },
        "ANOMALY_DETECTION": {
            "description": "Requests to identify unusual spending patterns",
            "examples": [
                "Are there any cost anomalies this month?",
                "Show me unusual spending patterns",
                "Did any services have unexpected cost increases?",
                "Identify cost spikes in my account",
                "Find abnormal usage in my AWS resources"
            ],
            "keywords": [
                "anomaly", "unusual", "unexpected", "spike", "surge",
                "abnormal", "outlier", "irregular", "sudden increase",
                "suspicious", "strange", "odd", "unexpected", "deviation"
            ]
        },
        "BUDGET_MANAGEMENT": {
            "description": "Queries related to budget tracking and alerts",
            "examples": [
                "Am I within budget this month?",
                "Set up a budget alert for EC2",
                "How much of my budget have I used?",
                "Create a $5000 monthly budget for RDS",
                "Send me alerts when I reach 80% of my budget"
            ],
            "keywords": [
                "budget", "alert", "threshold", "limit", "cap",
                "notification", "warning", "exceed", "within budget",
                "over budget", "budget tracking", "spending limit"
            ]
        },
        "GENERAL_INFORMATION": {
            "description": "General questions about AWS services or FinOps",
            "examples": [
                "What is Reserved Instance coverage?",
                "Explain Savings Plans",
                "How does AWS pricing work?",
                "Tell me about FinOps best practices",
                "What's the difference between on-demand and spot instances?"
            ],
            "keywords": [
                "what is", "how does", "explain", "tell me about",
                "information", "details", "help me understand",
                "definition", "describe", "overview", "summary"
            ]
        }
    }
    
    def __init__(self, bedrock_client=None):
        """
        Initialize the Intent Recognizer.
        
        Args:
            bedrock_client: Optional boto3 Bedrock client (for testing)
        """
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime')
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        self.embedding_model_id = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
        self.intent_examples = self._prepare_intent_examples()
        self.intent_keywords = self._prepare_intent_keywords()
    
    def _prepare_intent_examples(self) -> Dict[str, List[str]]:
        """
        Prepare intent examples for reference.
        
        Returns:
            Dict mapping intent names to lists of example queries
        """
        return {intent: data["examples"] for intent, data in self.INTENTS.items()}
    
    def _prepare_intent_keywords(self) -> Dict[str, List[str]]:
        """
        Prepare intent keywords for pattern matching.
        
        Returns:
            Dict mapping intent names to lists of keywords
        """
        return {intent: data["keywords"] for intent, data in self.INTENTS.items()}
    
    def recognize_intent(self, query: str, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Recognize the intent(s) in a user query.
        
        Args:
            query: User query text
            conversation_context: Optional conversation context
            
        Returns:
            Dict containing recognized intents and confidence scores
        """
        # Start with pattern-based recognition
        pattern_results = self._pattern_based_recognition(query)
        
        # If confidence is low, use ML-based recognition
        primary_confidence = pattern_results.get("primary_confidence", 0)
        if primary_confidence < 0.7:
            ml_results = self._ml_based_recognition(query, conversation_context)
            
            # Combine results, favoring ML-based if confidence is higher
            if ml_results.get("primary_confidence", 0) > primary_confidence:
                results = ml_results
            else:
                results = pattern_results
        else:
            results = pattern_results
        
        # Check for compound intents
        compound_results = self._detect_compound_intents(query, results)
        
        # Determine which agents to invoke based on intents
        agents_to_invoke = self._determine_agents(compound_results)
        compound_results["agents_to_invoke"] = agents_to_invoke
        
        logger.info(f"Intent recognition results: {json.dumps(compound_results)}")
        return compound_results
    
    def _pattern_based_recognition(self, query: str) -> Dict[str, Any]:
        """
        Perform pattern-based intent recognition.
        
        Args:
            query: User query text
            
        Returns:
            Dict containing recognized intents and confidence scores
        """
        query_lower = query.lower()
        
        # Calculate scores for each intent based on keyword matches
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    # Increase score based on keyword length (longer keywords are more specific)
                    keyword_score = len(keyword) / 3
                    score += keyword_score
                    matched_keywords.append(keyword)
            
            # Normalize score (0-1 range)
            intent_scores[intent] = {
                "score": min(score / 10, 1.0),
                "matched_keywords": matched_keywords
            }
        
        # Sort intents by score (descending)
        sorted_intents = sorted(
            [(intent, data["score"]) for intent, data in intent_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get primary and secondary intents
        primary_intent = sorted_intents[0][0] if sorted_intents[0][1] > 0 else "GENERAL_INFORMATION"
        primary_confidence = sorted_intents[0][1]
        
        secondary_intent = None
        secondary_confidence = 0
        if len(sorted_intents) > 1 and sorted_intents[1][1] > 0.3:  # Only consider secondary if confidence > 0.3
            secondary_intent = sorted_intents[1][0]
            secondary_confidence = sorted_intents[1][1]
        
        return {
            "primary_intent": primary_intent,
            "primary_confidence": primary_confidence,
            "secondary_intent": secondary_intent,
            "secondary_confidence": secondary_confidence,
            "all_intents": {intent: data["score"] for intent, data in intent_scores.items()},
            "matched_keywords": {intent: data["matched_keywords"] for intent, data in intent_scores.items() if data["matched_keywords"]},
            "method": "pattern"
        }
    
    def _ml_based_recognition(self, query: str, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform machine learning-based intent recognition using embeddings.
        
        Args:
            query: User query text
            conversation_context: Optional conversation context
            
        Returns:
            Dict containing recognized intents and confidence scores
        """
        try:
            # Get embedding for the query
            query_embedding = self._get_embedding(query)
            
            # Calculate similarity with example queries for each intent
            intent_scores = {}
            for intent, examples in self.intent_examples.items():
                # Get embeddings for examples (in a real implementation, these would be pre-computed)
                similarities = []
                for example in examples[:3]:  # Limit to first 3 examples for efficiency
                    example_embedding = self._get_embedding(example)
                    similarity = self._calculate_similarity(query_embedding, example_embedding)
                    similarities.append(similarity)
                
                # Use max similarity as the score for this intent
                intent_scores[intent] = max(similarities) if similarities else 0.0
            
            # Sort intents by score (descending)
            sorted_intents = sorted(
                intent_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get primary and secondary intents
            primary_intent = sorted_intents[0][0]
            primary_confidence = sorted_intents[0][1]
            
            secondary_intent = None
            secondary_confidence = 0
            if len(sorted_intents) > 1 and sorted_intents[1][1] > 0.7:  # Only consider secondary if confidence > 0.7
                secondary_intent = sorted_intents[1][0]
                secondary_confidence = sorted_intents[1][1]
            
            return {
                "primary_intent": primary_intent,
                "primary_confidence": primary_confidence,
                "secondary_intent": secondary_intent,
                "secondary_confidence": secondary_confidence,
                "all_intents": dict(sorted_intents),
                "method": "ml"
            }
        except Exception as e:
            logger.error(f"Error in ML-based intent recognition: {str(e)}", exc_info=True)
            # Fall back to pattern-based recognition
            return self._pattern_based_recognition(query)
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using Bedrock embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # For now, return a mock embedding
            # In a real implementation, this would call the Bedrock embedding model
            import hashlib
            import struct
            
            # Generate a deterministic pseudo-embedding based on text hash
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert hash bytes to floats (this is just a mock)
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                if i + 4 <= len(hash_bytes):
                    val = struct.unpack('f', hash_bytes[i:i+4])[0]
                    embedding.append(val)
            
            # Pad or truncate to 16 dimensions
            while len(embedding) < 16:
                embedding.append(0.0)
            
            return embedding[:16]
            
            # Real implementation would look like:
            # response = self.bedrock_client.invoke_model(
            #     modelId=self.embedding_model_id,
            #     body=json.dumps({
            #         "inputText": text
            #     })
            # )
            # result = json.loads(response["body"].read())
            # return result["embedding"]
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}", exc_info=True)
            # Return a zero vector as fallback
            return [0.0] * 16
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (0-1)
        """
        # Ensure embeddings are the same length
        min_len = min(len(embedding1), len(embedding2))
        embedding1 = embedding1[:min_len]
        embedding2 = embedding2[:min_len]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Calculate magnitudes
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        # Calculate cosine similarity
        if magnitude1 > 0 and magnitude2 > 0:
            similarity = dot_product / (magnitude1 * magnitude2)
            # Ensure result is in [0, 1] range
            return max(0.0, min(1.0, similarity))
        else:
            return 0.0
    
    def _detect_compound_intents(self, query: str, initial_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect compound intents in a query.
        
        Args:
            query: User query text
            initial_results: Initial intent recognition results
            
        Returns:
            Updated results with compound intent information
        """
        # Check for specific compound patterns
        compound_patterns = [
            # Cost analysis + optimization
            (r"(cost|spend|bill).+(optimize|save|reduce|recommendation)", ["COST_ANALYSIS", "COST_OPTIMIZATION"]),
            # Cost analysis + forecasting
            (r"(cost|spend|bill).+(forecast|predict|projection|future)", ["COST_ANALYSIS", "FORECASTING"]),
            # Cost analysis + comparison
            (r"(cost|spend|bill).+(compare|comparison|difference|versus|vs)", ["COST_ANALYSIS", "COMPARISON"]),
            # Optimization + resource utilization
            (r"(optimize|save|reduce).+(utilization|usage|efficiency)", ["COST_OPTIMIZATION", "RESOURCE_UTILIZATION"]),
            # Analysis + anomaly detection
            (r"(cost|spend|bill).+(anomaly|unusual|spike|surge)", ["COST_ANALYSIS", "ANOMALY_DETECTION"]),
        ]
        
        # Check if query matches any compound patterns
        query_lower = query.lower()
        compound_matches = []
        
        for pattern, intents in compound_patterns:
            if re.search(pattern, query_lower):
                compound_matches.append((pattern, intents))
        
        # If compound patterns found, update results
        if compound_matches:
            # Get the first match (could be enhanced to handle multiple matches)
            matched_pattern, compound_intents = compound_matches[0]
            
            # Update results
            results = initial_results.copy()
            results["is_compound"] = True
            results["compound_intents"] = compound_intents
            results["compound_pattern"] = matched_pattern
            
            # Ensure primary and secondary intents reflect the compound
            if results["primary_intent"] not in compound_intents:
                # Set primary intent to first compound intent
                results["secondary_intent"] = results["primary_intent"]
                results["secondary_confidence"] = results["primary_confidence"]
                results["primary_intent"] = compound_intents[0]
                results["primary_confidence"] = max(0.8, results["primary_confidence"])  # Boost confidence
            
            if results["secondary_intent"] not in compound_intents:
                # Find the other compound intent not already set as primary
                other_intent = next((i for i in compound_intents if i != results["primary_intent"]), None)
                if other_intent:
                    results["secondary_intent"] = other_intent
                    results["secondary_confidence"] = max(0.7, results.get("secondary_confidence", 0))  # Boost confidence
            
            return results
        else:
            # No compound intent detected
            initial_results["is_compound"] = False
            return initial_results
    
    def _determine_agents(self, intent_results: Dict[str, Any]) -> List[str]:
        """
        Determine which agents to invoke based on recognized intents.
        
        Args:
            intent_results: Intent recognition results
            
        Returns:
            List of agent IDs to invoke
        """
        agents_to_invoke = set()
        
        # Map intents to agents
        intent_to_agent = {
            "COST_ANALYSIS": "COST_ANALYSIS",
            "FORECASTING": "COST_ANALYSIS",
            "COMPARISON": "COST_ANALYSIS",
            "ANOMALY_DETECTION": "COST_ANALYSIS",
            "BUDGET_MANAGEMENT": "COST_ANALYSIS",
            "COST_OPTIMIZATION": "COST_OPTIMIZATION",
            "RESOURCE_UTILIZATION": "COST_OPTIMIZATION",
            "GENERAL_INFORMATION": "SUPERVISOR"  # Handle general info in the supervisor
        }
        
        # Add agent for primary intent
        primary_intent = intent_results.get("primary_intent")
        if primary_intent in intent_to_agent:
            agents_to_invoke.add(intent_to_agent[primary_intent])
        
        # Add agent for secondary intent if confidence is high enough
        secondary_intent = intent_results.get("secondary_intent")
        secondary_confidence = intent_results.get("secondary_confidence", 0)
        if secondary_intent and secondary_confidence > 0.5:
            if secondary_intent in intent_to_agent:
                agents_to_invoke.add(intent_to_agent[secondary_intent])
        
        # For compound intents, ensure all relevant agents are included
        if intent_results.get("is_compound", False):
            for intent in intent_results.get("compound_intents", []):
                if intent in intent_to_agent:
                    agents_to_invoke.add(intent_to_agent[intent])
        
        return list(agents_to_invoke)
