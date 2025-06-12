"""Simple LLM-based Query Router"""

import json
import logging
from typing import Dict, Any
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
    
    def route_query(self, query: str) -> Dict[str, Any]:
        try:
            if not query:
                return {"agents": ["cost_forecast", "trusted_advisor", "budget_management"], "reasoning": "Empty query - comprehensive analysis"}
            
            response = str(self.routing_agent(f"Route: {query}"))
            
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                result = json.loads(response[start:end])
                if "agents" in result:
                    # Handle legacy "both" routing
                    if "both" in result["agents"]:
                        result["agents"] = ["cost_forecast", "trusted_advisor"]
                    # Handle "comprehensive" routing
                    elif "comprehensive" in result["agents"]:
                        result["agents"] = ["cost_forecast", "trusted_advisor", "budget_management"]
                    return result
            
            return {"agents": ["cost_forecast", "trusted_advisor", "budget_management"], "reasoning": "Fallback - comprehensive analysis"}
        except Exception as e:
            logger.error(f"Error in LLM routing: {str(e)}")
            return {"agents": ["cost_forecast", "trusted_advisor", "budget_management"], "reasoning": "Error - comprehensive analysis"}
    
    def get_routing_explanation(self, query: str, decision: Dict[str, Any]) -> str:
        agents = decision.get("agents", [])
        reasoning = decision.get("reasoning", "")
        
        if len(agents) == 1:
            agent_name = agents[0].replace("_", " ").title()
            return f"🎯 Routing to {agent_name} Agent - {reasoning}"
        else:
            agent_names = [agent.replace("_", " ").title() for agent in agents]
            if len(agent_names) == 2:
                return f"🎯 Routing to {agent_names[0]} and {agent_names[1]} Agents - {reasoning}"
            else:
                return f"🎯 Routing to {', '.join(agent_names[:-1])}, and {agent_names[-1]} Agents - {reasoning}"
