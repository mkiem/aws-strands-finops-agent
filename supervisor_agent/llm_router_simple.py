"""Simple LLM-based Query Router"""

import json
import logging
from typing import Dict, Any
from strands import Agent

logger = logging.getLogger(__name__)

class LLMQueryRouter:
    def __init__(self):
        self.routing_agent = Agent(
            system_prompt="""Route AWS FinOps queries to agents:
- cost_forecast: costs, spending, analysis, forecasts
- trusted_advisor: optimization, savings, recommendations
- both: comprehensive analysis

Respond JSON only: {"agents": ["cost_forecast"], "reasoning": "explanation"}"""
        )
    
    def route_query(self, query: str) -> Dict[str, Any]:
        try:
            if not query:
                return {"agents": ["cost_forecast", "trusted_advisor"], "reasoning": "Empty query"}
            
            response = str(self.routing_agent(f"Route: {query}"))
            
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                result = json.loads(response[start:end])
                if "agents" in result:
                    return result
            
            return {"agents": ["cost_forecast", "trusted_advisor"], "reasoning": "Fallback"}
        except:
            return {"agents": ["cost_forecast", "trusted_advisor"], "reasoning": "Error"}
    
    def get_routing_explanation(self, query: str, decision: Dict[str, Any]) -> str:
        agents = decision.get("agents", [])
        reasoning = decision.get("reasoning", "")
        
        if len(agents) == 1:
            return f"🎯 Routing to {agents[0]} - {reasoning}"
        else:
            return f"🎯 Routing to both agents - {reasoning}"
