#!/usr/bin/env python3
"""
Test script for Budget Management Agent integration with Supervisor Agent
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_router_simple import LLMQueryRouter

def test_routing_decisions():
    """Test LLM routing decisions for various query types"""
    
    router = LLMQueryRouter()
    
    test_queries = [
        # Budget-specific queries
        "What budgets should I create for my AWS account?",
        "I need budget recommendations based on my spending",
        "How can I set up cost controls?",
        "Help me create spending limits",
        "What budget governance should I implement?",
        
        # Cost analysis queries
        "What are my current AWS costs?",
        "Show me my spending trends",
        "Analyze my monthly AWS expenses",
        
        # Optimization queries
        "How can I optimize my AWS costs?",
        "What savings opportunities do I have?",
        "Give me cost reduction recommendations",
        
        # Multi-domain queries
        "I need complete cost analysis with budget recommendations",
        "Show me costs, optimization, and budget suggestions",
        "Comprehensive FinOps analysis including budgets",
        "What are my costs and what budgets should I set?",
        
        # Edge cases
        "Help me with AWS financial management",
        "I want to control my cloud spending",
        "AWS cost management strategy"
    ]
    
    print("🧪 Testing Budget Management Agent Integration")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: \"{query}\"")
        
        try:
            routing_decision = router.route_query(query)
            agents = routing_decision.get("agents", [])
            reasoning = routing_decision.get("reasoning", "")
            
            print(f"   Agents: {agents}")
            print(f"   Reasoning: {reasoning}")
            
            # Validate routing
            if "budget" in query.lower() or "control" in query.lower() or "governance" in query.lower():
                if "budget_management" not in agents:
                    print(f"   ⚠️  WARNING: Budget query not routed to budget_management agent")
                else:
                    print(f"   ✅ Correctly routed budget query")
            
            if "cost" in query.lower() and "budget" not in query.lower():
                if "cost_forecast" not in agents:
                    print(f"   ⚠️  WARNING: Cost query not routed to cost_forecast agent")
                else:
                    print(f"   ✅ Correctly routed cost query")
            
            if "optim" in query.lower() or "saving" in query.lower():
                if "trusted_advisor" not in agents:
                    print(f"   ⚠️  WARNING: Optimization query not routed to trusted_advisor agent")
                else:
                    print(f"   ✅ Correctly routed optimization query")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Testing Complete")

if __name__ == "__main__":
    test_routing_decisions()
