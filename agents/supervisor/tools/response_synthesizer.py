"""
Response Synthesizer Tool for the FinOps Supervisor Agent.

This tool combines responses from multiple specialized agents into
a coherent, comprehensive response for the user.
"""

import logging
from typing import Dict, Any, List, Optional
from strands_agents.tools import Tool

# Configure logging
logger = logging.getLogger(__name__)

class ResponseSynthesizerTool(Tool):
    """
    Tool for synthesizing responses from multiple agents.
    
    This tool combines information from specialized agents into a coherent
    response, ensuring consistent formatting and presentation.
    """
    
    name = "response_synthesizer"
    description = "Combines responses from multiple agents into a coherent answer"
    
    def _run(self, agent_responses: Dict[str, Any], intent: Dict[str, Any], parameters: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synthesize a coherent response from multiple agent outputs.
        
        Args:
            agent_responses: Responses from specialized agents
            intent: Intent classification results
            parameters: Extracted parameters
            context: Optional context information
            
        Returns:
            Dict containing the synthesized response
        """
        logger.info("Synthesizing response from agent outputs")
        
        # Initialize response components
        response_parts = []
        charts = []
        recommendations = []
        errors = []
        
        # Process Cost Analysis Agent response
        if "cost_analysis" in agent_responses:
            cost_analysis = agent_responses["cost_analysis"]
            
            if "error" in cost_analysis:
                errors.append(f"Cost Analysis Error: {cost_analysis['error']}")
            else:
                # Extract relevant information from cost analysis
                if "summary" in cost_analysis:
                    response_parts.append(cost_analysis["summary"])
                
                if "charts" in cost_analysis:
                    charts.extend(cost_analysis["charts"])
                
                if "details" in cost_analysis:
                    response_parts.append(self._format_cost_details(cost_analysis["details"]))
        
        # Process Cost Optimization Agent response
        if "cost_optimization" in agent_responses:
            optimization = agent_responses["cost_optimization"]
            
            if "error" in optimization:
                errors.append(f"Cost Optimization Error: {optimization['error']}")
            else:
                # Extract relevant information from optimization
                if "summary" in optimization:
                    response_parts.append(optimization["summary"])
                
                if "recommendations" in optimization:
                    recommendations.extend(optimization["recommendations"])
                    response_parts.append(self._format_recommendations(optimization["recommendations"]))
        
        # Combine all parts into a coherent response
        synthesized_response = self._combine_response_parts(
            response_parts=response_parts,
            intent=intent,
            parameters=parameters,
            errors=errors
        )
        
        result = {
            "response": synthesized_response,
            "charts": charts,
            "recommendations": recommendations,
            "errors": errors
        }
        
        logger.info("Response synthesis complete")
        return result
    
    def _format_cost_details(self, details: Dict[str, Any]) -> str:
        """
        Format cost details into a readable string.
        
        Args:
            details: Cost details from the Cost Analysis Agent
            
        Returns:
            Formatted string with cost details
        """
        formatted_text = ""
        
        if "total_cost" in details:
            formatted_text += f"Total cost: ${details['total_cost']:.2f}\n\n"
        
        if "cost_by_service" in details and details["cost_by_service"]:
            formatted_text += "Cost breakdown by service:\n"
            for service in details["cost_by_service"]:
                formatted_text += f"- {service['service_name']}: ${service['cost']:.2f}"
                if "percentage" in service:
                    formatted_text += f" ({service['percentage']:.1f}%)"
                formatted_text += "\n"
            formatted_text += "\n"
        
        if "cost_by_region" in details and details["cost_by_region"]:
            formatted_text += "Cost breakdown by region:\n"
            for region in details["cost_by_region"]:
                formatted_text += f"- {region['region']}: ${region['cost']:.2f}"
                if "percentage" in region:
                    formatted_text += f" ({region['percentage']:.1f}%)"
                formatted_text += "\n"
            formatted_text += "\n"
        
        if "anomalies" in details and details["anomalies"]:
            formatted_text += "Cost anomalies detected:\n"
            for anomaly in details["anomalies"]:
                formatted_text += f"- {anomaly['service']}: ${anomaly['amount']:.2f} increase "
                formatted_text += f"({anomaly['percentage']:.1f}% higher than normal)\n"
            formatted_text += "\n"
        
        return formatted_text
    
    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Format optimization recommendations into a readable string.
        
        Args:
            recommendations: List of recommendations from the Cost Optimization Agent
            
        Returns:
            Formatted string with recommendations
        """
        if not recommendations:
            return "No cost optimization recommendations available at this time."
        
        formatted_text = "Cost optimization recommendations:\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            formatted_text += f"{i}. {rec['title']}\n"
            formatted_text += f"   {rec['description']}\n"
            
            if "estimated_savings" in rec:
                formatted_text += f"   Estimated monthly savings: ${rec['estimated_savings']:.2f}\n"
            
            if "difficulty" in rec:
                formatted_text += f"   Implementation difficulty: {rec['difficulty']}\n"
            
            if "resource_id" in rec and rec["resource_id"]:
                formatted_text += f"   Resource: {rec['resource_id']}\n"
            
            formatted_text += "\n"
        
        return formatted_text
    
    def _combine_response_parts(self, response_parts: List[str], intent: Dict[str, Any], parameters: Dict[str, Any], errors: List[str]) -> str:
        """
        Combine all response parts into a coherent answer.
        
        Args:
            response_parts: List of response components
            intent: Intent classification results
            parameters: Extracted parameters
            errors: List of errors encountered
            
        Returns:
            Combined response string
        """
        # Start with an appropriate introduction based on intent
        introduction = self._generate_introduction(intent, parameters)
        
        # Combine all parts
        combined_text = introduction + "\n\n"
        combined_text += "\n\n".join(response_parts)
        
        # Add error information if any
        if errors:
            combined_text += "\n\nNote: I encountered some issues while processing your request:\n"
            for error in errors:
                combined_text += f"- {error}\n"
        
        # Add a conclusion
        combined_text += "\n\n" + self._generate_conclusion(intent, parameters)
        
        return combined_text
    
    def _generate_introduction(self, intent: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """
        Generate an appropriate introduction based on intent and parameters.
        
        Args:
            intent: Intent classification results
            parameters: Extracted parameters
            
        Returns:
            Introduction string
        """
        primary_intent = intent.get("primary_intent", "GENERAL_INFORMATION")
        
        if primary_intent == "COST_ANALYSIS":
            time_range = parameters.get("time_range", {})
            period_type = time_range.get("period_type", "month")
            
            if period_type == "month":
                return "Here's the cost analysis you requested:"
            elif period_type == "year":
                return "Here's your annual cost analysis:"
            else:
                return "Here's the cost analysis for the specified time period:"
        
        elif primary_intent == "COST_OPTIMIZATION":
            return "I've analyzed your AWS resources and found the following optimization opportunities:"
        
        elif primary_intent == "RESOURCE_UTILIZATION":
            return "Here's the resource utilization analysis you requested:"
        
        elif primary_intent == "FORECASTING":
            return "Based on your historical usage, here's the cost forecast:"
        
        elif primary_intent == "COMPARISON":
            comparison = parameters.get("comparison", {})
            if comparison and comparison.get("type") == "time_period":
                return "Here's the cost comparison between the specified time periods:"
            elif comparison and comparison.get("type") == "service_comparison":
                services = comparison.get("services", [])
                if len(services) >= 2:
                    return f"Here's the comparison between {services[0]} and {services[1]}:"
                else:
                    return "Here's the service comparison you requested:"
            else:
                return "Here's the comparison you requested:"
        
        else:
            return "Here's the information you requested about your AWS costs:"
    
    def _generate_conclusion(self, intent: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """
        Generate an appropriate conclusion based on intent and parameters.
        
        Args:
            intent: Intent classification results
            parameters: Extracted parameters
            
        Returns:
            Conclusion string
        """
        primary_intent = intent.get("primary_intent", "GENERAL_INFORMATION")
        
        if primary_intent == "COST_ANALYSIS":
            return "Is there any specific aspect of this cost analysis you'd like me to explain further?"
        
        elif primary_intent == "COST_OPTIMIZATION":
            return "Would you like me to provide more details on any of these optimization recommendations?"
        
        elif primary_intent == "RESOURCE_UTILIZATION":
            return "Would you like me to suggest specific actions to improve resource utilization?"
        
        elif primary_intent == "FORECASTING":
            return "Would you like to see how changes in your usage might affect this forecast?"
        
        elif primary_intent == "COMPARISON":
            return "Is there another comparison you'd like to see, or would you like more details on this one?"
        
        else:
            return "Is there anything else you'd like to know about your AWS costs or optimization opportunities?"
