#!/usr/bin/env python3
"""
Test script for Fast Path Routing with LLM Fallback
"""

import json
import sys
import os
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_router_simple import LLMQueryRouter

def test_fast_path_routing():
    """Test fast path routing and fallback scenarios"""
    
    router = LLMQueryRouter()
    
    test_scenarios = [
        # Fast Path - Budget Management
        {
            "category": "Fast Path - Budget",
            "queries": [
                "What budgets should I create?",
                "I need budget recommendations",
                "How can I set up cost controls?",
                "Budget governance suggestions",
                "Create spending limits"
            ],
            "expected_agent": "budget_management",
            "expected_method": "fast_path"
        },
        
        # Fast Path - Cost Analysis
        {
            "category": "Fast Path - Cost",
            "queries": [
                "What are my current AWS costs?",
                "Show me my monthly expenses",
                "AWS cost breakdown",
                "Current spending analysis",
                "My AWS bill"
            ],
            "expected_agent": "cost_forecast",
            "expected_method": "fast_path"
        },
        
        # Fast Path - Optimization
        {
            "category": "Fast Path - Optimization",
            "queries": [
                "How can I optimize my costs?",
                "Cost reduction recommendations",
                "Ways to save money on AWS",
                "Efficiency improvements",
                "Cost optimization suggestions"
            ],
            "expected_agent": "trusted_advisor",
            "expected_method": "fast_path"
        },
        
        # Fast Path - Comprehensive
        {
            "category": "Fast Path - Comprehensive",
            "queries": [
                "Complete FinOps analysis",
                "Comprehensive AWS financial review",
                "Full analysis of everything",
                "Complete cost management strategy"
            ],
            "expected_agents": ["cost_forecast", "trusted_advisor", "budget_management"],
            "expected_method": "fast_path"
        },
        
        # LLM Fallback - Mixed Intent
        {
            "category": "LLM Fallback - Mixed Intent",
            "queries": [
                "What are my costs and what budgets should I set?",
                "Show me spending and optimization opportunities",
                "Cost analysis with budget recommendations",
                "I need costs, savings, and budget controls"
            ],
            "expected_method": "llm"
        },
        
        # LLM Fallback - Ambiguous
        {
            "category": "LLM Fallback - Ambiguous",
            "queries": [
                "Help me with AWS financial management",
                "I want to manage my cloud spending better",
                "AWS cost strategy",
                "Financial operations guidance"
            ],
            "expected_method": "llm"
        }
    ]
    
    print("🧪 Testing Fast Path Routing with LLM Fallback")
    print("=" * 70)
    
    total_tests = 0
    fast_path_tests = 0
    llm_fallback_tests = 0
    performance_metrics = []
    
    for scenario in test_scenarios:
        print(f"\n📋 {scenario['category']}")
        print("-" * 50)
        
        for query in scenario['queries']:
            total_tests += 1
            start_time = time.time()
            
            try:
                routing_decision = router.route_query(query)
                end_time = time.time()
                
                agents = routing_decision.get("agents", [])
                method = routing_decision.get("routing_method", "unknown")
                routing_time = routing_decision.get("routing_time", end_time - start_time)
                reasoning = routing_decision.get("reasoning", "")
                
                performance_metrics.append({
                    "query": query,
                    "method": method,
                    "time": routing_time,
                    "agents": agents
                })
                
                print(f"Query: \"{query[:50]}{'...' if len(query) > 50 else ''}\"")
                print(f"  Method: {method} ({routing_time:.3f}s)")
                print(f"  Agents: {agents}")
                print(f"  Reasoning: {reasoning}")
                
                # Validate expectations
                if scenario.get("expected_method"):
                    if method == scenario["expected_method"]:
                        print(f"  ✅ Correct routing method")
                        if method == "fast_path":
                            fast_path_tests += 1
                        elif method == "llm":
                            llm_fallback_tests += 1
                    else:
                        print(f"  ⚠️  Expected {scenario['expected_method']}, got {method}")
                
                if scenario.get("expected_agent"):
                    if scenario["expected_agent"] in agents:
                        print(f"  ✅ Correct agent routing")
                    else:
                        print(f"  ⚠️  Expected {scenario['expected_agent']}, got {agents}")
                
                if scenario.get("expected_agents"):
                    if set(scenario["expected_agents"]) == set(agents):
                        print(f"  ✅ Correct multi-agent routing")
                    else:
                        print(f"  ⚠️  Expected {scenario['expected_agents']}, got {agents}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                print()
    
    # Performance Summary
    print("=" * 70)
    print("📊 Performance Summary")
    print("=" * 70)
    
    fast_path_times = [m["time"] for m in performance_metrics if m["method"] == "fast_path"]
    llm_times = [m["time"] for m in performance_metrics if m["method"] == "llm"]
    
    print(f"Total Tests: {total_tests}")
    print(f"Fast Path Success: {fast_path_tests} ({fast_path_tests/total_tests*100:.1f}%)")
    print(f"LLM Fallback: {llm_fallback_tests} ({llm_fallback_tests/total_tests*100:.1f}%)")
    
    if fast_path_times:
        print(f"\nFast Path Performance:")
        print(f"  Average: {sum(fast_path_times)/len(fast_path_times):.3f}s")
        print(f"  Min: {min(fast_path_times):.3f}s")
        print(f"  Max: {max(fast_path_times):.3f}s")
    
    if llm_times:
        print(f"\nLLM Routing Performance:")
        print(f"  Average: {sum(llm_times)/len(llm_times):.3f}s")
        print(f"  Min: {min(llm_times):.3f}s")
        print(f"  Max: {max(llm_times):.3f}s")
    
    if fast_path_times and llm_times:
        improvement = (sum(llm_times)/len(llm_times)) / (sum(fast_path_times)/len(fast_path_times))
        print(f"\nPerformance Improvement: {improvement:.1f}x faster with fast path")
    
    print("\n🏁 Testing Complete")

if __name__ == "__main__":
    test_fast_path_routing()
