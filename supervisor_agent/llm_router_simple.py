"""Fixed Enhanced LLM Router with Proper Comprehensive Query Handling"""

import json
import logging
import time
from typing import Dict, Any, Optional
from strands import Agent

logger = logging.getLogger(__name__)

class EnhancedLLMQueryRouter:
    """Enhanced router that includes synthesis recommendations for latency optimization."""
    
    def __init__(self):
        self.routing_agent = Agent(
            system_prompt="""You are an intelligent AWS FinOps query router with synthesis optimization capabilities. 

Analyze the user's query and route to appropriate agents based on intent and content, while also determining if intelligent synthesis is needed.

Available agents:
- cost_forecast: For queries about AWS costs, spending analysis, cost trends, forecasting, and historical cost data
- trusted_advisor: For queries about cost optimization, savings opportunities, efficiency improvements, and resource recommendations  
- budget_management: For queries about budgets, budget creation, budget recommendations, cost controls, spending limits, budget governance, and proactive cost management

Routing Guidelines:
- Single agent: Route to the most relevant agent when query has clear focus
- Multiple agents: Use when query explicitly asks for comprehensive analysis or spans multiple domains
- Budget focus: Route to budget_management for budget-related governance and control questions
- Cost analysis: Route to cost_forecast for spending analysis and trends
- Optimization: Route to trusted_advisor for savings and efficiency

Synthesis Guidelines:
- synthesis_needed = false: Simple queries that just need information aggregation
- synthesis_needed = true: Strategic queries requiring analysis, prioritization, or cross-domain insights

Examples of synthesis_needed = true:
- "Which optimization recommendations would have the biggest impact on my cost trends?"
- "How should I prioritize these recommendations?"
- "What's the best strategy for balancing costs and optimization?"
- "Create a roadmap for cost optimization"
- "Compare and recommend the most important actions"

Examples of synthesis_needed = false:
- "Show me my costs and optimization recommendations"
- "What are my costs? Also show me optimization opportunities"
- "Display cost analysis and trusted advisor recommendations"

Respond with JSON only: {
    "agents": ["agent_name"], 
    "reasoning": "brief explanation of routing decision",
    "synthesis_needed": true/false,
    "confidence": "high/medium/low"
}"""
        )
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """Route query with enhanced synthesis recommendations."""
        if not query or len(query.strip()) < 5:
            return {
                "agents": ["cost_forecast"],
                "reasoning": "Default routing to cost analysis for unclear query",
                "synthesis_needed": False,
                "confidence": "low",
                "routing_method": "default"
            }
        
        # Try fast routing first
        fast_result = self.fast_route_query(query)
        if fast_result:
            return fast_result
        
        # Fall back to LLM routing
        return self.llm_route_query(query)
    
    def fast_route_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Enhanced fast routing with synthesis recommendations."""
        query_lower = query.lower()
        
        # COMPREHENSIVE ANALYSIS DETECTION (HIGHEST PRIORITY)
        comprehensive_patterns = [
            'comprehensive finops', 'complete finops', 'full finops',
            'comprehensive analysis', 'complete analysis', 'full analysis',
            'comprehensive aws', 'complete aws financial',
            'all recommendations', 'everything', 'full review'
        ]
        
        if any(pattern in query_lower for pattern in comprehensive_patterns):
            return {
                "agents": ["cost_forecast", "trusted_advisor", "budget_management"],
                "reasoning": "Fast route: Comprehensive FinOps analysis requested",
                "synthesis_needed": True,  # Always synthesize comprehensive queries
                "confidence": "high",
                "routing_method": "fast_path_comprehensive"
            }
        
        # STRATEGIC SYNTHESIS PATTERNS (HIGH PRIORITY)
        strategic_synthesis_patterns = [
            ('which', 'save', 'most'), ('which', 'biggest', 'impact'),
            ('which', 'highest', 'priority'), ('which', 'most', 'important'),
            ('what', 'best', 'strategy'), ('how', 'prioritize'),
            ('compare', 'recommend'), ('most', 'cost', 'effective')
        ]
        
        # Check for strategic patterns that need multiple agents
        for pattern_tuple in strategic_synthesis_patterns:
            if all(word in query_lower for word in pattern_tuple):
                # These queries need both cost context and optimization data
                return {
                    "agents": ["cost_forecast", "trusted_advisor"],
                    "reasoning": "Fast route: Strategic analysis requiring cost context and optimization data",
                    "synthesis_needed": True,
                    "confidence": "high",
                    "routing_method": "fast_path_strategic"
                }
        
        # Single agent patterns (no synthesis needed)
        single_agent_patterns = {
            'cost_forecast': [
                'what are my costs', 'show me costs', 'cost analysis', 'spending analysis',
                'cost trends', 'cost forecast', 'how much am i spending', 'cost breakdown',
                'what are my aws costs', 'current costs'
            ],
            'trusted_advisor': [
                'optimization recommendations', 'cost optimization', 'savings opportunities',
                'efficiency recommendations', 'reduce costs', 'optimize spending',
                'show me optimization', 'optimization opportunities'
            ],
            'budget_management': [
                'budget recommendations', 'create budget', 'budget planning',
                'spending limits', 'cost controls', 'budget governance'
            ]
        }
        
        # Check for single agent patterns (but not if strategic patterns already matched)
        for agent, patterns in single_agent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                # Check if it's ONLY asking for this agent's info (no other agent terms)
                other_agents = [a for a in single_agent_patterns.keys() if a != agent]
                has_other_agent_terms = any(
                    any(pattern in query_lower for pattern in single_agent_patterns[other_agent])
                    for other_agent in other_agents
                )
                
                # Also check if it has strategic language that would need synthesis
                has_strategic_language = any(
                    all(word in query_lower for word in pattern_tuple)
                    for pattern_tuple in strategic_synthesis_patterns
                )
                
                if not has_other_agent_terms and not has_strategic_language:
                    return {
                        "agents": [agent],
                        "reasoning": f"Fast route: Single {agent.replace('_', ' ')} query",
                        "synthesis_needed": False,
                        "confidence": "high",
                        "routing_method": "fast_path_single"
                    }
        
        # Multi-agent detection patterns
        cost_terms = ['cost', 'spending', 'forecast', 'trend']
        optimization_terms = ['optim', 'saving', 'reduc', 'efficiency', 'recommend']
        budget_terms = ['budget', 'planning', 'control', 'limit']
        
        has_cost = any(term in query_lower for term in cost_terms)
        has_optimization = any(term in query_lower for term in optimization_terms)
        has_budget = any(term in query_lower for term in budget_terms)
        
        # Count how many domains are mentioned
        domain_count = sum([has_cost, has_optimization, has_budget])
        
        # Synthesis vs aggregation patterns (FIXED LOGIC)
        strong_synthesis_patterns = [
            'which should i', 'what\'s the best', 'most important',
            'biggest impact', 'highest priority', 'prioritize',
            'strategy', 'roadmap', 'plan', 'balance'
        ]
        
        # FIXED: Move comprehensive to strong synthesis
        comprehensive_synthesis_patterns = [
            'comprehensive', 'complete', 'full', 'holistic',
            'integrate', 'combine', 'unified'
        ]
        
        simple_aggregation_patterns = [
            'show me', 'display', 'list', 'what are', 'give me',
            'provide', 'tell me about', 'information about'
        ]
        
        # Determine synthesis need (FIXED LOGIC)
        has_strong_synthesis = any(pattern in query_lower for pattern in strong_synthesis_patterns)
        has_comprehensive_request = any(pattern in query_lower for pattern in comprehensive_synthesis_patterns)
        has_simple_aggregation = any(pattern in query_lower for pattern in simple_aggregation_patterns)
        
        # FIXED: Synthesis decision logic
        if has_strong_synthesis or has_comprehensive_request:
            needs_synthesis = True
        elif has_simple_aggregation and not has_comprehensive_request:
            needs_synthesis = False
        else:
            needs_synthesis = domain_count >= 2  # Default for multi-domain
        
        # Route based on domain combinations
        if domain_count >= 3:
            # 3+ domains = comprehensive analysis
            return {
                "agents": ["cost_forecast", "trusted_advisor", "budget_management"],
                "reasoning": "Fast route: Multi-domain comprehensive analysis",
                "synthesis_needed": True,  # Always synthesize for 3+ agents
                "confidence": "high",
                "routing_method": "fast_path_comprehensive"
            }
        
        elif has_cost and has_optimization:
            return {
                "agents": ["cost_forecast", "trusted_advisor"],
                "reasoning": "Fast route: Cost analysis and optimization query",
                "synthesis_needed": needs_synthesis,
                "confidence": "high",
                "routing_method": "fast_path_multi"
            }
        
        elif has_cost and has_budget:
            return {
                "agents": ["cost_forecast", "budget_management"],
                "reasoning": "Fast route: Cost forecast and budget planning query",
                "synthesis_needed": needs_synthesis,
                "confidence": "high",
                "routing_method": "fast_path_multi"
            }
        
        elif has_optimization and has_budget:
            return {
                "agents": ["budget_management", "trusted_advisor"],
                "reasoning": "Fast route: Budget optimization query",
                "synthesis_needed": needs_synthesis,
                "confidence": "high",
                "routing_method": "fast_path_multi"
            }
        
        return None  # Fall back to LLM routing
    
    def llm_route_query(self, query: str) -> Dict[str, Any]:
        """Use LLM for complex routing decisions."""
        try:
            logger.info("Using LLM routing for complex query")
            start_time = time.time()
            
            routing_response = self.routing_agent(f"Route this query: {query}")
            
            routing_time = time.time() - start_time
            logger.info(f"LLM routing completed in {routing_time:.2f}s")
            
            # Extract JSON from LLM response
            if isinstance(routing_response, dict):
                response_text = routing_response.get('response', str(routing_response))
            else:
                response_text = str(routing_response)
            
            # Try to parse JSON from response
            try:
                # Look for JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    routing_decision = json.loads(json_str)
                    
                    # Add metadata
                    routing_decision["routing_method"] = "llm"
                    routing_decision["routing_time"] = routing_time
                    
                    # Ensure synthesis_needed is present
                    if "synthesis_needed" not in routing_decision:
                        routing_decision["synthesis_needed"] = len(routing_decision.get("agents", [])) > 2
                    
                    # Ensure confidence is present
                    if "confidence" not in routing_decision:
                        routing_decision["confidence"] = "medium"
                    
                    logger.info(f"LLM routing decision: {routing_decision}")
                    return routing_decision
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM routing response: {e}")
            
            # Fallback if JSON parsing fails
            return self._fallback_routing(query)
            
        except Exception as e:
            logger.error(f"LLM routing error: {str(e)}")
            return self._fallback_routing(query)
    
    def _fallback_routing(self, query: str) -> Dict[str, Any]:
        """Fallback routing when LLM fails."""
        query_lower = query.lower()
        
        if 'cost' in query_lower or 'spending' in query_lower:
            return {
                "agents": ["cost_forecast"],
                "reasoning": "Fallback routing to cost analysis",
                "synthesis_needed": False,
                "confidence": "low",
                "routing_method": "fallback"
            }
        elif 'optim' in query_lower or 'saving' in query_lower:
            return {
                "agents": ["trusted_advisor"],
                "reasoning": "Fallback routing to optimization recommendations",
                "synthesis_needed": False,
                "confidence": "low",
                "routing_method": "fallback"
            }
        elif 'budget' in query_lower:
            return {
                "agents": ["budget_management"],
                "reasoning": "Fallback routing to budget management",
                "synthesis_needed": False,
                "confidence": "low",
                "routing_method": "fallback"
            }
        else:
            return {
                "agents": ["cost_forecast", "trusted_advisor"],
                "reasoning": "Fallback routing to comprehensive analysis",
                "synthesis_needed": False,
                "confidence": "low",
                "routing_method": "fallback"
            }
    
    def get_routing_explanation(self, query: str, routing_decision: Dict[str, Any]) -> str:
        """Generate human-readable routing explanation."""
        agents = routing_decision.get("agents", [])
        reasoning = routing_decision.get("reasoning", "")
        synthesis_needed = routing_decision.get("synthesis_needed", False)
        routing_method = routing_decision.get("routing_method", "unknown")
        
        explanation = f"**Query Analysis**: {reasoning}\n\n"
        
        if len(agents) == 1:
            agent_name = agents[0].replace('_', ' ').title()
            explanation += f"**Routing Decision**: Directed to {agent_name} for focused analysis.\n\n"
            explanation += f"**Processing Mode**: Fast path - direct routing for optimal response time.\n\n"
        else:
            agent_names = [agent.replace('_', ' ').title() for agent in agents]
            explanation += f"**Routing Decision**: Multi-agent analysis involving {', '.join(agent_names)}.\n\n"
            
            if synthesis_needed:
                explanation += f"**Processing Mode**: Intelligent synthesis - combining insights for strategic recommendations.\n\n"
            else:
                explanation += f"**Processing Mode**: Parallel aggregation - fast combination of specialized analyses.\n\n"
        
        explanation += f"*Routing method: {routing_method}*"
        
        return explanation
