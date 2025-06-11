from strands import Agent
import asyncio
import concurrent.futures
from typing import Dict, Any
import json

class AsyncFinOpsProcessor:
    def __init__(self):
        self.cost_forecast_agent = Agent("aws-cost-forecast-agent")
        self.trusted_advisor_agent = Agent("trusted-advisor-agent-trusted-advisor-agent")

    def is_complex_query(self, query: str) -> bool:
        """Determine if a query requires multiple agents."""
        complex_keywords = [
            "comprehensive", "complete analysis", "full review",
            "costs and optimization", "forecast and recommendations"
        ]
        return any(keyword in query.lower() for keyword in complex_keywords)

    def invoke_agent_sync(self, agent: Agent, query: str) -> Dict[str, Any]:
        """Synchronously invoke an agent."""
        try:
            return agent.invoke({"query": query})
        except Exception as e:
            return {"error": str(e), "agent": getattr(agent, 'name', 'unknown')}

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process the query using appropriate agents."""
        if self.is_complex_query(query):
            # Return initial processing message
            initial_response = {
                "status": "processing",
                "message": "Your query requires complex analysis involving multiple systems. Please allow a few minutes for complete processing.",
                "estimated_time": "2-5 minutes"
            }
            
            # Use ThreadPoolExecutor for parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both agent calls
                cost_future = executor.submit(self.invoke_agent_sync, self.cost_forecast_agent, query)
                advisor_future = executor.submit(self.invoke_agent_sync, self.trusted_advisor_agent, query)
                
                # Wait for both to complete
                cost_results = cost_future.result()
                advisor_results = advisor_future.result()
            
            return self.synthesize_responses(cost_results, advisor_results)
        else:
            # For simple queries, route to appropriate agent
            if "cost" in query.lower() or "forecast" in query.lower():
                return self.invoke_agent_sync(self.cost_forecast_agent, query)
            else:
                return self.invoke_agent_sync(self.trusted_advisor_agent, query)

    def synthesize_responses(self, cost_results: Dict[str, Any], advisor_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine responses from multiple agents."""
        return {
            "status": "completed",
            "cost_analysis": cost_results,
            "optimization_recommendations": advisor_results,
            "timestamp": "2025-06-10T16:25:00Z"
        }
