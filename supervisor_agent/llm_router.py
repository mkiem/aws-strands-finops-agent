"""
LLM-based Query Router for AWS FinOps Supervisor Agent
"""

import json
import logging
from typing import Dict, Any
from strands import Agent

logger = logging.getLogger(__name__)

class LLMQueryRouter:
    """LLM-powered intelligent query router for FinOps agents."""
    
    def __init__(self):
        """Initialize the LLM router."""
        self.routing_instructions = """You are a routing system for AWS FinOps queries.

Available Agents:
- cost_forecast: Cost analysis, spending, historical data, forecasting
- trusted_advisor: Optimization recommendations, savings opportunities

Route to cost_forecast for: costs, spending, bills, analysis, trends, forecasts
Route to trusted_advisor for: optimization, savings, recommendations, efficiency
Route to both for: comprehensive analysis, complete overview

Respond with JSON only:
{"agents": ["cost_forecast"], "reasoning": "explanation", "confidence": 0.9}"""
        
        self.routing_agent = Agent(system_prompt=self.routing_instructions)
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """Route a query using LLM."""
        try:
            if not query or not query.strip():
                return {
                    "agents": ["cost_forecast", "trusted_advisor"],
                    "reasoning": "Empty query defaults to comprehensive analysis",
                    "confidence": 1.0
                }
            
            prompt = f"Route this query: \"{query}\""
            response = self.routing_agent(prompt)
            response_text = str(response)
            
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                routing_decision = json.loads(json_str)
                
                # Validate agents
                valid_agents = {"cost_forecast", "trusted_advisor"}
                agents = routing_decision.get("agents", [])
                
                if isinstance(agents, list) and all(agent in valid_agents for agent in agents):
                    routing_decision.setdefault("reasoning", "LLM routing decision")
                    routing_decision.setdefault("confidence", 0.8)
                    return routing_decision
            
            # Fallback
            return {
                "agents": ["cost_forecast", "trusted_advisor"],
                "reasoning": "Parsing failed, using comprehensive analysis",
                "confidence": 0.5
            }
                
        except Exception as e:
            logger.error(f"Error in LLM routing: {str(e)}")
            return {
                "agents": ["cost_forecast", "trusted_advisor"],
                "reasoning": f"Error: {str(e)}, using comprehensive analysis",
                "confidence": 0.3
            }
    
    def get_routing_explanation(self, query: str, routing_decision: Dict[str, Any]) -> str:
        """Generate routing explanation."""
        agents = routing_decision.get("agents", [])
        reasoning = routing_decision.get("reasoning", "No reasoning provided")
        confidence = routing_decision.get("confidence", 0.0)
        
        agent_names = {
            "cost_forecast": "Cost Forecast Agent",
            "trusted_advisor": "Trusted Advisor Agent"
        }
        
        if len(agents) == 1:
            agent_name = agent_names.get(agents[0], agents[0])
            return f"🎯 Routing to {agent_name} (confidence: {confidence:.0%})\n💭 {reasoning}"
        else:
            agent_list = [agent_names.get(agent, agent) for agent in agents]
            return f"🎯 Routing to {' + '.join(agent_list)} (confidence: {confidence:.0%})\n💭 {reasoning}"
