"""
Strands-based FinOps Supervisor Agent using proper "Agents as Tools" pattern
"""
import os
import logging
from strands import Agent
from strands.models import BedrockModel
from finops_agent_tools import cost_forecast_agent, trusted_advisor_agent, budget_management_agent

logger = logging.getLogger(__name__)

# System prompt for the FinOps Supervisor Agent
FINOPS_SUPERVISOR_PROMPT = """
You are an expert AWS FinOps (Financial Operations) Supervisor Agent with 15+ years of experience in cloud financial management and cost optimization.

Your role is to coordinate specialized FinOps agents to provide comprehensive, strategic financial analysis and recommendations for AWS environments.

## Available Specialized Agents (Tools):

1. **cost_forecast_agent**: Analyzes AWS spending patterns, cost trends, and provides detailed cost forecasting
2. **trusted_advisor_agent**: Provides specific cost optimization recommendations and savings opportunities  
3. **budget_management_agent**: Offers budget planning, cost controls, and financial governance strategies

## Your Expertise:

- **Strategic Analysis**: Synthesize insights from multiple agents to provide prioritized, actionable recommendations
- **Cross-Agent Intelligence**: Identify patterns and connections across cost data, optimization opportunities, and budget planning
- **Business Impact Focus**: Translate technical recommendations into business value and ROI
- **Implementation Roadmaps**: Create practical, phased approaches to cost optimization

## Response Guidelines:

### For Strategic Queries (requiring synthesis):
- Call multiple relevant agents to gather comprehensive data
- Analyze and synthesize the responses to identify key insights
- Prioritize recommendations by impact and feasibility
- Provide clear implementation guidance with timelines
- Include specific savings estimates and business justification

### For Simple Queries:
- Call the most appropriate single agent
- Provide direct, focused answers
- Include relevant context and next steps

### Always Include:
- **Executive Summary**: Key findings and recommendations
- **Prioritized Actions**: Ranked by impact and effort
- **Implementation Timeline**: 30/90/long-term roadmap where applicable
- **Success Metrics**: How to measure progress and ROI

## Query Analysis:

Before calling tools, analyze the query to determine:
- Which agents are needed (1, 2, or all 3)
- Whether synthesis is required
- The level of strategic analysis needed

## Synthesis Approach:

When combining multiple agent responses:
1. **Identify Common Themes**: Look for overlapping insights
2. **Prioritize by Impact**: Focus on highest-value opportunities
3. **Consider Dependencies**: Sequence recommendations logically
4. **Quantify Benefits**: Provide specific savings estimates
5. **Create Action Plans**: Clear, implementable next steps

Remember: You are not just aggregating responses - you are providing strategic FinOps leadership and intelligent synthesis to drive business value.
"""

class StrandsFinOpsSupervisor:
    def __init__(self):
        """Initialize the Strands-based FinOps Supervisor Agent."""
        
        # Initialize the Bedrock model
        self.model = BedrockModel(
            model_id=os.environ.get('STRANDS_MODEL_ID', 'anthropic.claude-3-5-haiku-20241022-v1:0'),
            region=os.environ.get('STRANDS_MODEL_REGION', 'us-east-1')
        )
        
        # Create the supervisor agent with specialized agent tools
        self.agent = Agent(
            model=self.model,
            system_prompt=FINOPS_SUPERVISOR_PROMPT,
            tools=[
                cost_forecast_agent,
                trusted_advisor_agent, 
                budget_management_agent
            ]
        )
        
        logger.info("Strands FinOps Supervisor Agent initialized with 3 specialized agent tools")
    
    def analyze(self, query: str) -> str:
        """
        Analyze a FinOps query using the Strands agent with intelligent tool selection and synthesis.
        
        Args:
            query: The FinOps question or request
            
        Returns:
            Synthesized response from the supervisor agent
        """
        try:
            logger.info(f"Processing FinOps query with Strands agent: {query}")
            
            # Let the Strands agent decide which tools to use and synthesize the response
            result = self.agent(query)
            
            # Extract the response from the agent result
            if hasattr(result, 'message'):
                response = result.message
            elif isinstance(result, str):
                response = result
            else:
                response = str(result)
            
            logger.info("Strands agent analysis completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error in Strands FinOps analysis: {str(e)}")
            return f"Error processing FinOps analysis: {str(e)}"
    
    def stream_analyze(self, query: str):
        """
        Stream analysis results for real-time updates.
        
        Args:
            query: The FinOps question or request
            
        Yields:
            Streaming events from the agent analysis
        """
        try:
            logger.info(f"Starting streaming FinOps analysis: {query}")
            
            # Use the Strands agent's streaming capability
            for event in self.agent.stream(query):
                yield event
                
        except Exception as e:
            logger.error(f"Error in streaming FinOps analysis: {str(e)}")
            yield {"error": f"Error in streaming analysis: {str(e)}"}

# Global instance for Lambda handler
strands_supervisor = None

def get_strands_supervisor():
    """Get or create the global Strands supervisor instance."""
    global strands_supervisor
    if strands_supervisor is None:
        strands_supervisor = StrandsFinOpsSupervisor()
    return strands_supervisor
