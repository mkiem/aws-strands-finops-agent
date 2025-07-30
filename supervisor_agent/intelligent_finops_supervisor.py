"""
Fixed Intelligent FinOps Supervisor with Working LLM Synthesis
Addresses the invoke method issue and ensures proper synthesis.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from strands import Agent

logger = logging.getLogger(__name__)

class IntelligentFinOpsSupervisor:
    """
    Enhanced FinOps Supervisor that provides intelligent synthesis with latency optimization.
    
    Routing Strategy:
    - Single agent: Direct routing (fast path)
    - 2 agents: Smart decision between aggregation vs synthesis
    - 3+ agents: Always use synthesis (complex scenarios)
    """
    
    def __init__(self):
        """Initialize the intelligent supervisor with FinOps advisor persona."""
        self.synthesis_agent = Agent(
            system_prompt="""You are a Senior AWS FinOps Advisor with 15+ years of experience in cloud financial operations, cost optimization, and strategic financial planning.

Your role is to synthesize insights from multiple specialized FinOps analysis agents to provide unified, actionable strategic advice.

SYNTHESIS PRINCIPLES:
1. **Holistic Analysis**: Look for connections and patterns across all agent responses
2. **Prioritization**: Rank recommendations by business impact, cost savings potential, and implementation complexity
3. **Strategic Integration**: Combine insights into coherent, actionable strategies
4. **Risk Assessment**: Identify potential risks and dependencies between recommendations
5. **Implementation Roadmap**: Provide clear next steps and sequencing

RESPONSE STRUCTURE:
- Executive Summary (key findings and recommendations)
- Strategic Insights (cross-agent analysis and patterns)
- Prioritized Action Plan (ranked by impact and feasibility)
- Risk Considerations (dependencies and potential issues)
- Implementation Timeline (suggested sequencing)

Always maintain a strategic, advisory tone focused on business outcomes and practical implementation.

Format responses in clear markdown with actionable sections."""
        )
    
    def should_synthesize(self, query: str, agents: List[str]) -> bool:
        """
        Determine if a query requires intelligent synthesis or simple aggregation.
        
        UPDATED LOGIC: More aggressive synthesis for better user experience
        
        Args:
            query: The user's query
            agents: List of agents to be invoked
            
        Returns:
            True if synthesis is needed, False for simple aggregation
        """
        if len(agents) == 1:
            return False  # Single agent never needs synthesis
        
        if len(agents) >= 3:
            return True   # 3+ agents always need synthesis
        
        # For 2 agents, DEFAULT TO SYNTHESIS unless explicitly simple aggregation
        return self._requires_synthesis_for_two_agents(query, agents)
    
    def _requires_synthesis_for_two_agents(self, query: str, agents: List[str]) -> bool:
        """
        Determine if 2-agent response needs synthesis or simple aggregation.
        
        UPDATED: Default to synthesis unless explicitly simple aggregation requested.
        """
        
        query_lower = query.lower()
        
        # ONLY these patterns should skip synthesis (simple aggregation)
        simple_aggregation_only_patterns = [
            "show me both", "display both", "list both", "give me both",
            "show me the", "display the", "list the", "just show",
            "just display", "just list", "just give me"
        ]
        
        # Check if user explicitly wants simple aggregation
        wants_simple_aggregation = any(pattern in query_lower for pattern in simple_aggregation_only_patterns)
        
        if wants_simple_aggregation:
            logger.info(f"Simple aggregation requested for 2 agents: {agents}")
            return False
        
        # DEFAULT TO SYNTHESIS for better user experience
        logger.info(f"Defaulting to synthesis for 2 agents: {agents}")
        return True
    
    def synthesize_responses(self, query: str, agent_responses: Dict[str, Any], 
                           routing_context: Dict[str, Any]) -> str:
        """
        Intelligently synthesize responses from multiple agents.
        
        IMPROVED: Better error handling and fallback mechanisms
        
        Args:
            query: Original user query
            agent_responses: Dictionary of agent responses
            routing_context: Context from routing decision
            
        Returns:
            Synthesized strategic response
        """
        logger.info(f"Performing intelligent synthesis for {len(agent_responses)} agents")
        
        try:
            synthesis_prompt = self._build_synthesis_prompt(query, agent_responses, routing_context)
            
            logger.info("Invoking synthesis agent with LLM...")
            synthesis_response = self.synthesis_agent(synthesis_prompt)
            
            # Extract response content
            if isinstance(synthesis_response, dict):
                result = synthesis_response.get('response', str(synthesis_response))
            else:
                result = str(synthesis_response)
            
            logger.info(f"Synthesis completed successfully. Response length: {len(result)} characters")
            return result
                
        except Exception as e:
            logger.error(f"Synthesis failed with error: {str(e)}")
            logger.info("Falling back to enhanced aggregation...")
            # Fallback to enhanced aggregation if synthesis fails
            return self._fallback_aggregation(query, agent_responses, routing_context)
    
    def _build_synthesis_prompt(self, query: str, agent_responses: Dict[str, Any], 
                              routing_context: Dict[str, Any]) -> str:
        """Build a dynamic synthesis prompt that adapts to any agent combination."""
        
        prompt = f"""
FINOPS SYNTHESIS REQUEST

Original Query: "{query}"

Routing Context:
- Agents Consulted: {', '.join(agent_responses.keys())}
- Routing Reasoning: {routing_context.get('reasoning', 'Multi-agent analysis required')}
- Analysis Scope: {routing_context.get('scope', 'Comprehensive FinOps review')}

AGENT ANALYSIS RESULTS:
"""
        
        # Dynamically add each agent's response
        for agent_name, response in agent_responses.items():
            agent_display_name = self._get_agent_display_name(agent_name)
            agent_content = self._extract_agent_content(response)
            
            prompt += f"""
--- {agent_display_name.upper()} ANALYSIS ---
{agent_content}

"""
        
        prompt += """
SYNTHESIS REQUIREMENTS:

As a Senior FinOps Advisor, provide a comprehensive synthesis that:

1. **EXECUTIVE SUMMARY**: What are the 3 most critical findings across all analyses?

2. **STRATEGIC INSIGHTS**: 
   - What patterns emerge when combining these analyses?
   - Which recommendations have the highest business impact?
   - What interdependencies exist between different recommendations?

3. **PRIORITIZED ACTION PLAN**:
   - Rank all recommendations by: Impact (High/Medium/Low) + Effort (High/Medium/Low)
   - Identify quick wins vs. strategic initiatives
   - Suggest implementation sequence

4. **RISK & DEPENDENCY ANALYSIS**:
   - What risks should be considered?
   - Which actions depend on others?
   - What could go wrong and how to mitigate?

5. **IMPLEMENTATION ROADMAP**:
   - 30-day immediate actions
   - 90-day strategic initiatives  
   - Long-term optimization goals

Focus on actionable, business-oriented advice that a CFO or engineering leader can immediately act upon.
Provide specific dollar amounts, percentages, and timelines where possible.
"""
        
        return prompt
    
    def _get_agent_display_name(self, agent_name: str) -> str:
        """Convert agent function names to human-readable display names."""
        name_mapping = {
            'cost_forecast': 'Cost Analysis & Forecasting',
            'aws-cost-forecast-agent': 'Cost Analysis & Forecasting',
            'trusted_advisor': 'Optimization & Efficiency',
            'trusted-advisor-agent-trusted-advisor-agent': 'Optimization & Efficiency',
            'budget_management': 'Budget Planning & Controls',
            'budget-management-agent': 'Budget Planning & Controls',
            'security_cost': 'Security Cost Analysis',
            'rightsizing': 'Resource Rightsizing',
            'reserved_instances': 'Reserved Instance Optimization',
            'spot_instances': 'Spot Instance Strategy',
            'storage_optimization': 'Storage Cost Optimization',
            'network_optimization': 'Network Cost Analysis',
            'compliance_cost': 'Compliance Cost Management'
        }
        
        return name_mapping.get(agent_name, agent_name.replace('_', ' ').replace('-', ' ').title())
    
    def _extract_agent_content(self, response: Any) -> str:
        """Extract meaningful content from agent response regardless of format."""
        try:
            if isinstance(response, dict):
                # Handle different response formats
                if 'body' in response:
                    body = response['body']
                    if isinstance(body, str):
                        try:
                            body = json.loads(body)
                            return body.get('response', str(body))
                        except json.JSONDecodeError:
                            return body
                    return body.get('response', str(body))
                elif 'response' in response:
                    return response['response']
                elif 'error' in response:
                    return f"⚠️ Analysis Error: {response['error']}"
                else:
                    return str(response)
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Error extracting agent content: {str(e)}")
            return f"⚠️ Error processing response: {str(e)}"
    
    def _fallback_aggregation(self, query: str, agent_responses: Dict[str, Any], 
                            routing_context: Dict[str, Any]) -> str:
        """Fallback to simple aggregation if synthesis fails."""
        logger.info("Using fallback aggregation due to synthesis failure")
        
        combined_response = f"# 🏦 AWS FinOps Analysis\n\n{routing_context.get('reasoning', '')}\n\n"
        
        for agent_name, response in agent_responses.items():
            agent_display_name = self._get_agent_display_name(agent_name)
            agent_content = self._extract_agent_content(response)
            
            combined_response += f"## {agent_display_name}\n\n{agent_content}\n\n"
        
        if len(agent_responses) > 1:
            combined_response += f"## Summary\n\n"
            combined_response += f"This analysis combines insights from {len(agent_responses)} specialized agents. "
            combined_response += f"Review each section above for detailed recommendations and next steps.\n\n"
            combined_response += f"*⚡ Analysis completed using parallel processing.*"
        
        return combined_response

    def format_single_agent_response(self, agent: str, response: Any, 
                                   routing_explanation: str) -> str:
        """Format single agent response with minimal overhead."""
        agent_display_name = self._get_agent_display_name(agent)
        agent_content = self._extract_agent_content(response)
        
        # Determine appropriate emoji and title based on agent type
        if 'cost' in agent.lower() or 'forecast' in agent.lower():
            icon = "📊"
            title = "AWS Cost Analysis"
        elif 'trusted' in agent.lower() or 'advisor' in agent.lower():
            icon = "💡"
            title = "AWS Optimization Recommendations"
        elif 'budget' in agent.lower():
            icon = "🎯"
            title = "AWS Budget Management"
        else:
            icon = "📋"
            title = "AWS FinOps Analysis"
        
        return f"# {icon} {title}\n\n{routing_explanation}\n\n{agent_content}"
