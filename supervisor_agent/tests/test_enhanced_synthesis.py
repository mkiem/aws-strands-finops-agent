#!/usr/bin/env python3
"""
Test script for the Enhanced Intelligent FinOps Supervisor
Tests latency-optimized routing and synthesis capabilities.
"""

import json
import time
from intelligent_finops_supervisor import IntelligentFinOpsSupervisor
from llm_router_enhanced import EnhancedLLMQueryRouter

def test_synthesis_decision_logic():
    """Test the synthesis decision logic with various query types."""
    print("🧪 Testing Synthesis Decision Logic")
    print("=" * 50)
    
    supervisor = IntelligentFinOpsSupervisor()
    
    test_cases = [
        # Single agent - should never synthesize
        {
            "query": "What are my current AWS costs?",
            "agents": ["cost_forecast"],
            "expected_synthesis": False,
            "reason": "Single agent"
        },
        
        # 2 agents - simple aggregation
        {
            "query": "Show me my costs and optimization recommendations",
            "agents": ["cost_forecast", "trusted_advisor"],
            "expected_synthesis": False,
            "reason": "Simple aggregation request"
        },
        
        # 2 agents - needs synthesis
        {
            "query": "Which optimization recommendations would have the biggest impact on my cost trends?",
            "agents": ["cost_forecast", "trusted_advisor"],
            "expected_synthesis": True,
            "reason": "Strategic comparison needed"
        },
        
        # 2 agents - needs synthesis (prioritization)
        {
            "query": "How should I prioritize my budget planning with these cost forecasts?",
            "agents": ["cost_forecast", "budget_management"],
            "expected_synthesis": True,
            "reason": "Prioritization and strategy needed"
        },
        
        # 3+ agents - always synthesize
        {
            "query": "Provide comprehensive FinOps analysis",
            "agents": ["cost_forecast", "trusted_advisor", "budget_management"],
            "expected_synthesis": True,
            "reason": "3+ agents always need synthesis"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        agents = test_case["agents"]
        expected = test_case["expected_synthesis"]
        reason = test_case["reason"]
        
        result = supervisor.should_synthesize(query, agents)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{i}. {status}")
        print(f"   Query: {query}")
        print(f"   Agents: {agents}")
        print(f"   Expected: {expected}, Got: {result}")
        print(f"   Reason: {reason}")
        print()

def test_enhanced_routing():
    """Test the enhanced routing with synthesis recommendations."""
    print("🧪 Testing Enhanced Routing Logic")
    print("=" * 50)
    
    router = EnhancedLLMQueryRouter()
    
    test_queries = [
        # Single agent queries
        "What are my current AWS costs?",
        "Show me optimization recommendations",
        "Create budget recommendations",
        
        # Multi-agent simple aggregation
        "Show me costs and optimization opportunities",
        "Display cost analysis and budget recommendations",
        
        # Multi-agent with synthesis
        "Which optimization recommendations would save the most money?",
        "How should I prioritize these cost optimization strategies?",
        "Create a comprehensive FinOps roadmap",
        "What's the best strategy for balancing costs and optimization?",
        
        # Complex comprehensive queries
        "Provide complete FinOps analysis with budget and optimization recommendations"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Query: {query}")
        
        start_time = time.time()
        routing_decision = router.route_query(query)
        routing_time = time.time() - start_time
        
        agents = routing_decision.get("agents", [])
        synthesis_needed = routing_decision.get("synthesis_needed", False)
        routing_method = routing_decision.get("routing_method", "unknown")
        confidence = routing_decision.get("confidence", "unknown")
        
        print(f"   Agents: {agents}")
        print(f"   Synthesis: {synthesis_needed}")
        print(f"   Method: {routing_method}")
        print(f"   Confidence: {confidence}")
        print(f"   Time: {routing_time:.3f}s")
        print()

def test_synthesis_prompt_building():
    """Test the synthesis prompt building with mock responses."""
    print("🧪 Testing Synthesis Prompt Building")
    print("=" * 50)
    
    supervisor = IntelligentFinOpsSupervisor()
    
    # Mock agent responses
    mock_responses = {
        "cost_forecast": {
            "body": json.dumps({
                "response": "Your AWS costs for 2025 are trending upward at $12,500/month. Key drivers include EC2 instances ($8,000) and RDS databases ($3,200). Forecast shows 15% increase over next quarter."
            })
        },
        "trusted_advisor": {
            "body": json.dumps({
                "response": "Identified 8 optimization opportunities: 1) Rightsize 12 underutilized EC2 instances (save $2,400/month), 2) Convert to Reserved Instances (save $1,800/month), 3) Optimize RDS storage (save $600/month)."
            })
        }
    }
    
    routing_context = {
        "reasoning": "Multi-agent analysis for strategic cost optimization",
        "scope": "Comprehensive cost analysis with optimization recommendations",
        "agents": ["cost_forecast", "trusted_advisor"]
    }
    
    query = "Which optimization recommendations would have the biggest impact on my cost trends?"
    
    # Test synthesis (this would normally call the LLM)
    print(f"Query: {query}")
    print(f"Agents: {list(mock_responses.keys())}")
    print()
    
    # Build the prompt (without actually calling the LLM)
    prompt = supervisor._build_synthesis_prompt(query, mock_responses, routing_context)
    
    print("Generated Synthesis Prompt:")
    print("-" * 30)
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    print()

def test_latency_scenarios():
    """Test different latency scenarios."""
    print("🧪 Testing Latency Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Fast Path (Single Agent)",
            "query": "What are my AWS costs?",
            "expected_path": "single_agent",
            "expected_time": "< 0.1s routing"
        },
        {
            "name": "Aggregation Path (2 Agents)",
            "query": "Show me costs and optimization recommendations",
            "expected_path": "aggregation",
            "expected_time": "< 0.1s routing"
        },
        {
            "name": "Synthesis Path (2 Agents)",
            "query": "Which recommendations would save the most money?",
            "expected_path": "synthesis",
            "expected_time": "< 0.1s routing + synthesis time"
        },
        {
            "name": "Synthesis Path (3+ Agents)",
            "query": "Comprehensive FinOps analysis with all recommendations",
            "expected_path": "synthesis",
            "expected_time": "< 0.1s routing + synthesis time"
        }
    ]
    
    router = EnhancedLLMQueryRouter()
    supervisor = IntelligentFinOpsSupervisor()
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        
        # Test routing time
        start_time = time.time()
        routing_decision = router.route_query(scenario['query'])
        routing_time = time.time() - start_time
        
        agents = routing_decision.get("agents", [])
        synthesis_needed = routing_decision.get("synthesis_needed", False)
        
        # Determine actual path
        if len(agents) == 1:
            actual_path = "single_agent"
        elif synthesis_needed:
            actual_path = "synthesis"
        else:
            actual_path = "aggregation"
        
        print(f"   Expected Path: {scenario['expected_path']}")
        print(f"   Actual Path: {actual_path}")
        print(f"   Routing Time: {routing_time:.3f}s")
        print(f"   Expected Time: {scenario['expected_time']}")
        
        status = "✅ PASS" if actual_path == scenario['expected_path'] else "❌ FAIL"
        print(f"   Status: {status}")
        print()

def main():
    """Run all tests."""
    print("🚀 Enhanced FinOps Supervisor Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_synthesis_decision_logic()
        print()
        
        test_enhanced_routing()
        print()
        
        test_synthesis_prompt_building()
        print()
        
        test_latency_scenarios()
        print()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
