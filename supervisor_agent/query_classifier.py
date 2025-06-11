"""
Query Classification Module for AWS FinOps Supervisor Agent

This module provides intelligent query classification to route queries
to the appropriate FinOps agents based on query intent and content.
"""

import re
from typing import Literal, List
from enum import Enum

class QueryType(Enum):
    """Enumeration of query types for routing decisions."""
    COST_ANALYSIS = "cost_analysis"
    OPTIMIZATION = "optimization"
    COMPREHENSIVE = "comprehensive"
    BUDGET_FORECAST = "budget_forecast"
    SAVINGS = "savings"

class QueryClassifier:
    """Intelligent query classifier for FinOps agent routing."""
    
    def __init__(self):
        """Initialize the query classifier with keyword patterns."""
        self.cost_keywords = [
            'cost', 'costs', 'spending', 'spend', 'bill', 'billing', 'expense', 'expenses',
            'price', 'pricing', 'charge', 'charges', 'fee', 'fees', 'usage', 'current',
            'total', 'breakdown', 'analysis', 'trend', 'trends', 'history', 'historical'
        ]
        
        self.optimization_keywords = [
            'optimize', 'optimization', 'recommend', 'recommendations', 'improve', 'improvement',
            'reduce', 'reduction', 'save', 'saving', 'efficiency', 'efficient', 'best practice',
            'best practices', 'advisor', 'advice', 'suggestion', 'suggestions', 'opportunity',
            'opportunities', 'waste', 'wasteful', 'unused', 'underutilized'
        ]
        
        self.budget_keywords = [
            'budget', 'budgets', 'forecast', 'forecasting', 'predict', 'prediction',
            'future', 'next month', 'next quarter', 'next year', 'projection', 'projections',
            'estimate', 'estimates', 'planning', 'plan'
        ]
        
        self.savings_keywords = [
            'save', 'saving', 'savings', 'discount', 'discounts', 'reserved', 'reservation',
            'spot', 'instance', 'instances', 'rightsizing', 'right-sizing', 'downsize',
            'resize', 'terminate', 'stop', 'shutdown'
        ]
        
        self.comprehensive_keywords = [
            'comprehensive', 'complete', 'full', 'overall', 'everything', 'all',
            'summary', 'overview', 'report', 'analysis', 'both', 'entire', 'whole'
        ]
    
    def classify_query(self, query: str) -> QueryType:
        """
        Classify a query to determine the appropriate routing.
        
        Args:
            query (str): The user's query string
            
        Returns:
            QueryType: The classified query type for routing
        """
        if not query:
            return QueryType.COMPREHENSIVE
        
        query_lower = query.lower()
        
        # Check for comprehensive analysis indicators first
        if self._contains_keywords(query_lower, self.comprehensive_keywords):
            return QueryType.COMPREHENSIVE
        
        # Count keyword matches for each category
        cost_score = self._count_keyword_matches(query_lower, self.cost_keywords)
        optimization_score = self._count_keyword_matches(query_lower, self.optimization_keywords)
        budget_score = self._count_keyword_matches(query_lower, self.budget_keywords)
        savings_score = self._count_keyword_matches(query_lower, self.savings_keywords)
        
        # Determine primary intent based on highest score
        scores = {
            QueryType.COST_ANALYSIS: cost_score,
            QueryType.OPTIMIZATION: optimization_score,
            QueryType.BUDGET_FORECAST: budget_score,
            QueryType.SAVINGS: savings_score
        }
        
        # Get the maximum score
        max_score = max(scores.values())
        
        # If no keywords match, default to comprehensive
        if max_score == 0:
            return QueryType.COMPREHENSIVE
        
        # Get all categories with the maximum score
        max_categories = [category for category, score in scores.items() if score == max_score]
        
        # If multiple categories tie, check for specific patterns
        if len(max_categories) > 1:
            # If both cost and optimization have high scores, it might be comprehensive
            if (QueryType.COST_ANALYSIS in max_categories and 
                QueryType.OPTIMIZATION in max_categories):
                return QueryType.COMPREHENSIVE
            # Otherwise, return the first one (arbitrary but consistent)
            return max_categories[0]
        
        # Return the single category with the highest score
        return max_categories[0]
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the specified keywords."""
        return any(keyword in text for keyword in keywords)
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count the number of keyword matches in the text."""
        return sum(1 for keyword in keywords if keyword in text)
    
    def get_routing_decision(self, query: str) -> dict:
        """
        Get detailed routing decision for a query.
        
        Args:
            query (str): The user's query string
            
        Returns:
            dict: Routing decision with agent selection and reasoning
        """
        query_type = self.classify_query(query)
        
        routing_map = {
            QueryType.COST_ANALYSIS: {
                "agents": ["cost_forecast"],
                "reasoning": "Query focuses on cost analysis and spending patterns"
            },
            QueryType.OPTIMIZATION: {
                "agents": ["trusted_advisor"],
                "reasoning": "Query seeks optimization recommendations and cost reduction advice"
            },
            QueryType.BUDGET_FORECAST: {
                "agents": ["cost_forecast"],
                "reasoning": "Query involves budget planning and cost forecasting"
            },
            QueryType.SAVINGS: {
                "agents": ["trusted_advisor"],
                "reasoning": "Query focuses on savings opportunities and cost efficiency"
            },
            QueryType.COMPREHENSIVE: {
                "agents": ["cost_forecast", "trusted_advisor"],
                "reasoning": "Query requires comprehensive analysis from both cost and optimization perspectives"
            }
        }
        
        decision = routing_map[query_type]
        decision["query_type"] = query_type.value
        decision["query"] = query
        
        return decision
