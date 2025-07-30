#!/usr/bin/env python3
"""
Test script for enhanced multi-part query routing.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_router_simple import LLMQueryRouter

def test_multi_part_queries():
    """Test the enhanced routing with multi-part queries."""
    
    router = LLMQueryRouter()
    
    # Test cases that were problematic before
    test_cases = [
        {
            "query": "What are my AWS forecast for next 3 months and what budgets should I set?",
            "expected_agents": ["cost_forecast", "budget_management"],
            "description": "Original problem query - forecast + budget"
        },
        {
            "query": "Show me cost predictions and budget recommendations",
            "expected_agents": ["cost_forecast", "budget_management"],
            "description": "Prediction + budget recommendations"
        },
        {
            "query": "What will my future costs be and how should I set spending limits?",
            "expected_agents": ["cost_forecast", "budget_management"],
            "description": "Future costs + spending limits"
        },
        {
            "query": "I need cost optimization and budget planning",
            "expected_agents": ["cost_forecast", "trusted_advisor", "budget_management"],
            "description": "Cost optimization + budget planning (should use LLM)"
        },
        {
            "query": "What are my current AWS costs?",
            "expected_agents": ["cost_forecast"],
            "description": "Simple cost query - should stay single agent"
        },
        {
            "query": "How can I optimize my spending?",
            "expected_agents": ["trusted_advisor"],
            "description": "Simple optimization query - should stay single agent"
        },
        {
            "query": "What budgets should I create?",
            "expected_agents": ["budget_management"],
            "description": "Simple budget query - should stay single agent"
        },
        {
            "query": "Give me comprehensive analysis of everything",
            "expected_agents": ["cost_forecast", "trusted_advisor", "budget_management"],
            "description": "Comprehensive query"
        },
        {
            "query": "What are my costs and how can I optimize them and what budgets should I set?",
            "expected_routing": "llm",
            "description": "Complex multi-part query - should force LLM routing"
        }
    ]
    
    print("🧪 Testing Enhanced Multi-Part Query Routing\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "llm_routed": 0
    }
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_agents = test_case.get("expected_agents", [])
        expected_routing = test_case.get("expected_routing", "fast_path")
        description = test_case["description"]
        
        print(f"Test {i}: {description}")
        print(f"Query: '{query}'")
        
        # Test fast routing first
        fast_result = router.fast_route_query(query)
        
        if fast_result is None:
            print(f"✅ Routed to LLM (as expected)" if expected_routing == "llm" else f"⚠️  Routed to LLM (unexpected)")
            if expected_routing == "llm":
                results["passed"] += 1
            else:
                results["failed"] += 1
            results["llm_routed"] += 1
        else:
            actual_agents = fast_result.get("agents", [])
            routing_method = fast_result.get("routing_method", "unknown")
            reasoning = fast_result.get("reasoning", "")
            
            print(f"Fast route result: {actual_agents}")
            print(f"Routing method: {routing_method}")
            print(f"Reasoning: {reasoning}")
            
            if expected_routing == "llm":
                print(f"❌ Expected LLM routing but got fast path")
                results["failed"] += 1
            elif set(actual_agents) == set(expected_agents):
                print(f"✅ Correct routing!")
                results["passed"] += 1
            else:
                print(f"❌ Expected {expected_agents}, got {actual_agents}")
                results["failed"] += 1
        
        print("-" * 60)
    
    print(f"\n📊 Test Results:")
    print(f"   • Passed: {results['passed']}")
    print(f"   • Failed: {results['failed']}")
    print(f"   • LLM Routed: {results['llm_routed']}")
    print(f"   • Success Rate: {(results['passed'] / len(test_cases)) * 100:.1f}%")
    
    return results

def test_specific_patterns():
    """Test specific pattern matching."""
    
    router = LLMQueryRouter()
    
    print("\n🎯 Testing Specific Pattern Matching\n")
    
    pattern_tests = [
        ("forecast and budget", ["cost_forecast", "budget_management"]),
        ("prediction and budget", ["cost_forecast", "budget_management"]),
        ("next month and budget", ["cost_forecast", "budget_management"]),
        ("cost optimization", ["cost_forecast", "trusted_advisor"]),
        ("budget optimization", ["budget_management", "trusted_advisor"]),
        ("spending reduction", ["cost_forecast", "trusted_advisor"]),
    ]
    
    for pattern, expected in pattern_tests:
        result = router.fast_route_query(f"What about {pattern}?")
        if result:
            actual = result.get("agents", [])
            status = "✅" if set(actual) == set(expected) else "❌"
            print(f"{status} '{pattern}' → {actual} (expected: {expected})")
        else:
            print(f"⚠️  '{pattern}' → LLM routing")

if __name__ == "__main__":
    # Test multi-part queries
    results = test_multi_part_queries()
    
    # Test specific patterns
    test_specific_patterns()
    
    print(f"\n🎉 Enhanced routing implementation: {'✅ READY' if results['passed'] >= 7 else '⚠️ NEEDS WORK'}")
