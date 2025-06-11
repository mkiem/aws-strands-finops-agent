#!/usr/bin/env python3
"""
Test script for LLM-based supervisor agent query routing.
"""

import sys
import os
sys.path.append('/home/ec2-user/projects/finopsAgent')

from llm_router import LLMQueryRouter

def test_llm_routing():
    """Test various queries with LLM-based routing."""
    router = LLMQueryRouter()
    
    test_queries = [
        # Cost Analysis queries (should route to cost_forecast only)
        "What are my current AWS costs?",
        "Show me my spending breakdown for this month",
        "What's my total bill for EC2 services?",
        "Analyze my cost trends over the past 6 months",
        "What will my costs be next month?",
        "Create a budget forecast for Q2",
        
        # Optimization queries (should route to trusted_advisor only)
        "How can I optimize my AWS spending?",
        "Give me cost optimization recommendations",
        "What are the best practices to reduce my costs?",
        "Show me opportunities to save money",
        "How can I improve my cost efficiency?",
        "What idle resources do I have?",
        
        # Comprehensive queries (should route to both agents)
        "Give me a comprehensive FinOps analysis",
        "I need a complete overview of my AWS costs and optimization opportunities",
        "Provide both cost analysis and recommendations",
        "Show me everything about my AWS financial situation",
        "What's my spending situation and how can I optimize it?",
        
        # Edge cases
        "Hello",
        "",
        "AWS costs and savings opportunities",
    ]
    
    print("🤖 Testing LLM-Based Query Routing\n")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        
        try:
            routing_decision = router.route_query(query)
            agents = routing_decision.get("agents", [])
            reasoning = routing_decision.get("reasoning", "No reasoning provided")
            confidence = routing_decision.get("confidence", 0.0)
            
            # Determine expected behavior
            if len(agents) == 1:
                if "cost_forecast" in agents:
                    agent_type = "📊 Cost Analysis Only"
                elif "trusted_advisor" in agents:
                    agent_type = "💡 Optimization Only"
                else:
                    agent_type = "❓ Unknown Single Agent"
            else:
                agent_type = "🏦 Comprehensive Analysis"
            
            print(f"🎯 Routing: {agent_type}")
            print(f"🤖 Agents: {', '.join(agents)}")
            print(f"💭 Reasoning: {reasoning}")
            print(f"📊 Confidence: {confidence:.0%}")
            
            # Get routing explanation
            explanation = router.get_routing_explanation(query, routing_decision)
            print(f"📝 Explanation: {explanation}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_llm_routing()
