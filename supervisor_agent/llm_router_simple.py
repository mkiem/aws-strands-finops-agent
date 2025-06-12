"""Fast Path Query Router with LLM Fallback"""

import json
import logging
import time
from typing import Dict, Any, Optional
from strands import Agent

logger = logging.getLogger(__name__)

class LLMQueryRouter:
    def __init__(self):
        self.routing_agent = Agent(
            system_prompt="""You are an intelligent AWS FinOps query router. Analyze the user's query and route to appropriate agents based on intent and content.

Available agents:
- cost_forecast: For queries about AWS costs, spending analysis, cost trends, forecasting, and historical cost data
- trusted_advisor: For queries about cost optimization, savings opportunities, efficiency improvements, and resource recommendations  
- budget_management: For queries about budgets, budget creation, budget recommendations, cost controls, spending limits, budget governance, and proactive cost management
- comprehensive: For complex queries requiring analysis from multiple agents

Routing Guidelines:
- Single agent: Route to the most relevant agent when query has clear focus
- Multiple agents: Use when query explicitly asks for comprehensive analysis or spans multiple domains
- Budget focus: Route to budget_management for budget-related governance and control questions
- Cost analysis: Route to cost_forecast for spending analysis and trends
- Optimization: Route to trusted_advisor for savings and efficiency

Respond with JSON only: {"agents": ["agent_name"], "reasoning": "brief explanation of routing decision"}

Examples:
- "What are my AWS costs?" → {"agents": ["cost_forecast"], "reasoning": "Cost analysis query"}
- "How can I optimize spending?" → {"agents": ["trusted_advisor"], "reasoning": "Optimization recommendations needed"}
- "What budgets should I create?" → {"agents": ["budget_management"], "reasoning": "Budget recommendations and governance"}
- "I need complete cost analysis with budgets" → {"agents": ["cost_forecast", "budget_management"], "reasoning": "Multi-domain query requiring cost data and budget planning"}"""
        )
    
    def fast_route_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Fast routing for common query patterns with confidence scoring"""
        if not query or len(query.strip()) < 5:
            return None  # Too short/unclear - use LLM
            
        query_lower = query.lower()
        
        # High-confidence budget routing
        budget_keywords = ['budget', 'spending limit', 'cost control', 'governance', 'budget recommendation', 'budget suggestions', 'spending controls']
        if any(word in query_lower for word in budget_keywords):
            # Check for mixed intent
            if any(word in query_lower for word in ['cost analysis', 'spending trend', 'optimize', 'savings']):
                return None  # Mixed intent - use LLM for better routing
            return {
                "agents": ["budget_management"], 
                "reasoning": "Fast route: Clear budget management query",
                "routing_method": "fast_path",
                "confidence": "high"
            }
        
        # High-confidence cost analysis routing
        cost_keywords = ['current cost', 'aws cost', 'spending', 'expense', 'bill', 'cost analysis', 'monthly cost', 'cost breakdown']
        if any(word in query_lower for word in cost_keywords) and not any(word in query_lower for word in ['optim', 'reduc', 'saving']):
            if any(word in query_lower for word in ['budget', 'control', 'limit']):
                return None  # Mixed intent - use LLM
            return {
                "agents": ["cost_forecast"], 
                "reasoning": "Fast route: Clear cost analysis query",
                "routing_method": "fast_path",
                "confidence": "high"
            }
        
        # High-confidence optimization routing
        optimization_keywords = ['optimize', 'saving', 'reduce cost', 'efficiency', 'recommendation', 'cost reduction', 'save money']
        if any(word in query_lower for word in optimization_keywords):
            if any(word in query_lower for word in ['budget', 'current cost', 'spending analysis']):
                return None  # Mixed intent - use LLM
            return {
                "agents": ["trusted_advisor"], 
                "reasoning": "Fast route: Clear optimization query",
                "routing_method": "fast_path",
                "confidence": "high"
            }
        
        # Comprehensive analysis indicators
        comprehensive_keywords = ['complete', 'comprehensive', 'full analysis', 'everything', 'all aspects', 'complete finops']
        if any(word in query_lower for word in comprehensive_keywords):
            return {
                "agents": ["cost_forecast", "trusted_advisor", "budget_management"], 
                "reasoning": "Fast route: Comprehensive analysis requested",
                "routing_method": "fast_path",
                "confidence": "high"
            }
        
        # Multi-domain patterns
        if ('cost' in query_lower and 'budget' in query_lower) or ('spending' in query_lower and 'budget' in query_lower):
            return {
                "agents": ["cost_forecast", "budget_management"], 
                "reasoning": "Fast route: Cost analysis and budget planning",
                "routing_method": "fast_path",
                "confidence": "medium"
            }
        
        if ('optim' in query_lower and 'cost' in query_lower) or ('saving' in query_lower and 'cost' in query_lower):
            return {
                "agents": ["cost_forecast", "trusted_advisor"], 
                "reasoning": "Fast route: Cost analysis and optimization",
                "routing_method": "fast_path",
                "confidence": "medium"
            }
        
        return None  # Uncertain - fallback to LLM routing
    
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """Main routing with fast path + LLM fallback"""
        start_time = time.time()
        
        try:
            # Try fast path first
            fast_result = self.fast_route_query(query)
            if fast_result:
                fast_time = time.time() - start_time
                logger.info(f"Fast path routing successful in {fast_time:.3f}s: {fast_result}")
                fast_result["routing_time"] = fast_time
                return fast_result
            
            # Fallback to LLM routing
            logger.info("Fast path uncertain, falling back to LLM routing")
            llm_start = time.time()
            
            response = str(self.routing_agent(f"Route: {query}"))
            
            # Extract JSON from LLM response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                result = json.loads(response[start:end])
                if "agents" in result:
                    # Handle legacy routing options
                    if "both" in result["agents"]:
                        result["agents"] = ["cost_forecast", "trusted_advisor"]
                    elif "comprehensive" in result["agents"]:
                        result["agents"] = ["cost_forecast", "trusted_advisor", "budget_management"]
                    
                    llm_time = time.time() - llm_start
                    total_time = time.time() - start_time
                    result["routing_method"] = "llm"
                    result["routing_time"] = total_time
                    result["llm_time"] = llm_time
                    logger.info(f"LLM routing successful in {llm_time:.3f}s (total: {total_time:.3f}s): {result}")
                    return result
            
            # Final fallback - comprehensive analysis
            fallback_time = time.time() - start_time
            logger.warning(f"Both fast path and LLM routing failed, using comprehensive fallback after {fallback_time:.3f}s")
            return {
                "agents": ["cost_forecast", "trusted_advisor", "budget_management"], 
                "reasoning": "Fallback - comprehensive analysis due to routing uncertainty",
                "routing_method": "fallback",
                "routing_time": fallback_time
            }
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"Error in routing after {error_time:.3f}s: {str(e)}")
            return {
                "agents": ["cost_forecast", "trusted_advisor", "budget_management"], 
                "reasoning": f"Error fallback - {str(e)}",
                "routing_method": "error_fallback",
                "routing_time": error_time
            }
    
    def get_routing_explanation(self, query: str, decision: Dict[str, Any]) -> str:
        """Generate routing explanation with performance metrics"""
        agents = decision.get("agents", [])
        reasoning = decision.get("reasoning", "")
        routing_method = decision.get("routing_method", "unknown")
        routing_time = decision.get("routing_time", 0)
        
        # Format agent names
        if len(agents) == 1:
            agent_name = agents[0].replace("_", " ").title()
            route_desc = f"Routing to {agent_name} Agent"
        else:
            agent_names = [agent.replace("_", " ").title() for agent in agents]
            if len(agent_names) == 2:
                route_desc = f"Routing to {agent_names[0]} and {agent_names[1]} Agents"
            else:
                route_desc = f"Routing to {', '.join(agent_names[:-1])}, and {agent_names[-1]} Agents"
        
        # Add performance indicator
        if routing_method == "fast_path":
            performance_indicator = f"⚡ Fast Path ({routing_time:.3f}s)"
        elif routing_method == "llm":
            performance_indicator = f"🧠 LLM Routing ({routing_time:.3f}s)"
        else:
            performance_indicator = f"🔄 {routing_method.replace('_', ' ').title()} ({routing_time:.3f}s)"
        
        return f"🎯 {route_desc} - {reasoning} | {performance_indicator}"
