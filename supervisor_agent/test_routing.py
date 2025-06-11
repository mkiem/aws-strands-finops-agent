#!/usr/bin/env python3
"""
Test script for supervisor agent query routing logic.
"""

from query_classifier import QueryClassifier, QueryType

def test_query_routing():
    """Test various queries to verify routing logic."""
    classifier = QueryClassifier()
    
    test_queries = [
        # Cost Analysis queries (should route to cost_forecast only)
        ("What are my current AWS costs?", QueryType.COST_ANALYSIS),
        ("Show me my spending breakdown for this month", QueryType.COST_ANALYSIS),
        ("What's my total bill for EC2 services?", QueryType.COST_ANALYSIS),
        ("Analyze my cost trends over the past 6 months", QueryType.COST_ANALYSIS),
        
        # Optimization queries (should route to trusted_advisor only)
        ("How can I optimize my AWS spending?", QueryType.OPTIMIZATION),
        ("Give me cost optimization recommendations", QueryType.OPTIMIZATION),
        ("What are the best practices to reduce my costs?", QueryType.OPTIMIZATION),
        ("Show me opportunities to save money", QueryType.SAVINGS),
        ("How can I improve my cost efficiency?", QueryType.OPTIMIZATION),
        
        # Budget/Forecast queries (should route to cost_forecast only)
        ("What will my costs be next month?", QueryType.BUDGET_FORECAST),
        ("Create a budget forecast for Q2", QueryType.BUDGET_FORECAST),
        ("Predict my future AWS spending", QueryType.BUDGET_FORECAST),
        
        # Comprehensive queries (should route to both agents)
        ("Give me a comprehensive FinOps analysis", QueryType.COMPREHENSIVE),
        ("I need a complete overview of my AWS costs and optimization opportunities", QueryType.COMPREHENSIVE),
        ("Provide both cost analysis and recommendations", QueryType.COMPREHENSIVE),
        ("Show me everything about my AWS financial situation", QueryType.COMPREHENSIVE),
        
        # Edge cases
        ("Hello", QueryType.COMPREHENSIVE),  # Should default to comprehensive
        ("", QueryType.COMPREHENSIVE),  # Empty query
    ]
    
    print("🧪 Testing Query Routing Logic\n")
    print("=" * 80)
    
    for query, expected_type in test_queries:
        routing_decision = classifier.get_routing_decision(query)
        actual_type = QueryType(routing_decision["query_type"])
        agents = routing_decision["agents"]
        reasoning = routing_decision["reasoning"]
        
        status = "✅ PASS" if actual_type == expected_type else "❌ FAIL"
        
        print(f"\nQuery: \"{query}\"")
        print(f"Expected: {expected_type.value}")
        print(f"Actual: {actual_type.value}")
        print(f"Agents: {', '.join(agents)}")
        print(f"Reasoning: {reasoning}")
        print(f"Status: {status}")
        print("-" * 80)

if __name__ == "__main__":
    test_query_routing()
