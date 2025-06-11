"""
AWS Budget Management Agent - FIXED VERSION
Built with Strands SDK for comprehensive budget management and cost control
Uses Claude 3.5 Haiku via Strands framework - CORRECTLY IMPLEMENTED
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from strands import Agent, tool
from strands_tools import calculator, current_time

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
budgets_client = boto3.client('budgets')
ce_client = boto3.client('ce')

# Environment variables
ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID')

# System prompt for the Budget Management Agent
BUDGET_MANAGEMENT_SYSTEM_PROMPT = """
You are an AWS Budget Management Agent specialized in proactive cost control and governance.

Your capabilities include:
- Creating and managing AWS budgets based on cost analysis
- Monitoring budget performance and generating alerts
- Providing budget recommendations based on spending patterns
- Setting up automated budget actions for cost control
- Analyzing budget performance history and trends

You have access to AWS Budgets API and Cost Explorer data to provide comprehensive budget management.

IMPORTANT: When users ask for "recommendations", "suggestions", or "what budgets should I create", you MUST use the get_budget_recommendations() tool.

When responding:
- Always provide natural language responses based on tool results
- Provide clear, actionable budget recommendations
- Include specific dollar amounts and percentages
- Explain the rationale behind budget suggestions
- Highlight potential cost savings and risk mitigation
- Format responses with clear headings and bullet points
- Always include relevant timeframes and thresholds

Focus on proactive cost management and governance to help users maintain control over their AWS spending.
"""

@tool
def get_budget_recommendations() -> str:
    """
    Generate intelligent budget recommendations based on historical AWS spending patterns and cost analysis.
    Use this when users ask for budget suggestions, recommendations, or want to know what budgets to create.
    
    Returns:
        String containing budget recommendations with specific dollar amounts and rationales
    """
    try:
        logger.info("Generating budget recommendations")
        
        # Get cost data for recommendations
        cost_data = get_cost_data_for_recommendations()
        
        if not cost_data:
            return "I don't have sufficient cost data to provide budget recommendations. Please ensure you have some AWS usage history for meaningful recommendations."
        
        recommendations = []
        
        # Analyze spending patterns by service
        for service, data in cost_data.items():
            if data['monthly_average'] > 10:  # Only recommend budgets for services with significant spend
                
                # Calculate recommended budget amount (110% of average with seasonal adjustment)
                recommended_amount = data['monthly_average'] * 1.1
                if data['variance'] > 0.3:  # High variance suggests seasonal patterns
                    recommended_amount *= 1.2
                
                recommendations.append(f"""
**{service}**
- Recommended Monthly Budget: ${recommended_amount:.2f}
- Rationale: Based on ${data['monthly_average']:.2f} average monthly spend with {data['variance']:.1%} variance
- Trend: {data['trend']}
- Suggested Thresholds: 80% notification, 95% warning, 100% alert
""")
        
        if not recommendations:
            return "Based on your current AWS usage, I recommend starting with small budgets for your main services. Consider creating a $100 monthly budget for EC2 and a $50 monthly budget for S3 as starting points."
        
        # Generate organization-level budget recommendations
        total_monthly_spend = sum([data['monthly_average'] for data in cost_data.values()])
        org_budget = total_monthly_spend * 1.1
        
        result = f"""# Budget Recommendations Based on Your AWS Spending Patterns

## Service-Level Budget Recommendations

{''.join(recommendations)}

## Organization-Wide Budget
- **Recommended Monthly Budget**: ${org_budget:.2f}
- **Rationale**: Organization-wide spending control with 10% buffer
- **Priority**: HIGH - This provides overall cost governance

## Implementation Priority
1. Start with your highest spending services first
2. Set up email notifications at 80% threshold
3. Consider automated actions at 95% threshold
4. Review and adjust monthly based on actual usage

## Estimated Benefits
- **Proactive Cost Control**: Prevent unexpected charges
- **Budget Discipline**: Encourage cost-conscious decisions
- **Early Warning System**: Get alerts before overspending
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating budget recommendations: {str(e)}")
        return f"I encountered an error while generating budget recommendations: {str(e)}. Please check your AWS permissions and try again."

@tool
def get_budget_analysis() -> str:
    """
    Analyze existing AWS budgets and their current performance status.
    Use this when users ask to analyze current budgets, check budget status, or review existing budget performance.
    
    Returns:
        String containing analysis of existing budgets and their utilization
    """
    try:
        logger.info("Analyzing existing budgets")
        
        # Get all budgets for the account
        response = budgets_client.describe_budgets(AccountId=ACCOUNT_ID)
        budgets = response.get('Budgets', [])
        
        if not budgets:
            return "You currently have no budgets configured in your AWS account. I recommend setting up budgets to monitor and control your AWS spending. Would you like me to provide budget recommendations based on your spending patterns?"
        
        budget_analysis = []
        total_budgeted = 0
        total_actual = 0
        total_forecasted = 0
        
        for budget in budgets:
            budget_name = budget['BudgetName']
            budget_type = budget['BudgetType']
            
            # Calculate budget metrics
            budget_limit = float(budget.get('BudgetLimit', {}).get('Amount', 0))
            actual_spend = float(budget.get('CalculatedSpend', {}).get('ActualSpend', {}).get('Amount', 0))
            forecasted_spend = float(budget.get('CalculatedSpend', {}).get('ForecastedSpend', {}).get('Amount', 0))
            
            utilization = (actual_spend / budget_limit * 100) if budget_limit > 0 else 0
            forecast_utilization = (forecasted_spend / budget_limit * 100) if budget_limit > 0 else 0
            
            status = determine_budget_status(utilization, forecast_utilization)
            
            budget_analysis.append(f"""
**{budget_name}** ({budget_type})
- Budget Limit: ${budget_limit:.2f}
- Actual Spend: ${actual_spend:.2f} ({utilization:.1f}% utilized)
- Forecasted Spend: ${forecasted_spend:.2f} ({forecast_utilization:.1f}% of budget)
- Status: {status}
- Remaining Budget: ${budget_limit - actual_spend:.2f}
""")
            
            total_budgeted += budget_limit
            total_actual += actual_spend
            total_forecasted += forecasted_spend

        # Generate summary insights
        overall_utilization = (total_actual / total_budgeted * 100) if total_budgeted > 0 else 0
        forecast_utilization = (total_forecasted / total_budgeted * 100) if total_budgeted > 0 else 0
        
        insights = []
        exceeded_budgets = len([b for b in budgets if (float(b.get('CalculatedSpend', {}).get('ActualSpend', {}).get('Amount', 0)) / float(b.get('BudgetLimit', {}).get('Amount', 1))) >= 1.0])
        if exceeded_budgets > 0:
            insights.append(f"⚠️ {exceeded_budgets} budget(s) have exceeded their limits")
        
        critical_budgets = len([b for b in budgets if (float(b.get('CalculatedSpend', {}).get('ActualSpend', {}).get('Amount', 0)) / float(b.get('BudgetLimit', {}).get('Amount', 1))) >= 0.9])
        if critical_budgets > 0:
            insights.append(f"🔴 {critical_budgets} budget(s) are in critical status (>90% utilized)")
        
        result = f"""# Budget Analysis Summary

## Overall Budget Status
- **Total Budgets**: {len(budgets)}
- **Total Budgeted Amount**: ${total_budgeted:.2f}
- **Total Actual Spend**: ${total_actual:.2f}
- **Overall Utilization**: {overall_utilization:.1f}%
- **Forecasted Utilization**: {forecast_utilization:.1f}%

## Individual Budget Performance

{''.join(budget_analysis)}

## Key Insights
{''.join([f"- {insight}" for insight in insights]) if insights else "- All budgets are performing within normal parameters"}

## Recommendations
- Monitor budgets approaching 80% utilization closely
- Consider adjusting budgets that consistently exceed forecasts
- Set up automated actions for budgets frequently exceeding limits
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing budgets: {str(e)}")
        return f"I encountered an error while analyzing your budgets: {str(e)}. Please check your AWS permissions and try again."

# Helper functions
def determine_budget_status(utilization: float, forecast_utilization: float) -> str:
    """Determine budget status based on utilization"""
    if utilization >= 100:
        return 'EXCEEDED'
    elif utilization >= 90:
        return 'CRITICAL'
    elif utilization >= 80 or forecast_utilization >= 100:
        return 'WARNING'
    elif utilization >= 60:
        return 'HEALTHY'
    else:
        return 'UNDER_UTILIZED'

def get_cost_data_for_recommendations() -> Dict[str, Dict]:
    """Get cost data for generating budget recommendations"""
    try:
        # Get cost data by service for the last 6 months
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        cost_data = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                amount = float(group['Metrics']['BlendedCost']['Amount'])
                
                if service not in cost_data:
                    cost_data[service] = {'monthly_costs': [], 'total': 0}
                
                cost_data[service]['monthly_costs'].append(amount)
                cost_data[service]['total'] += amount
        
        # Calculate statistics for each service
        for service, data in cost_data.items():
            costs = data['monthly_costs']
            if costs:
                data['monthly_average'] = sum(costs) / len(costs)
                data['variance'] = (max(costs) - min(costs)) / data['monthly_average'] if data['monthly_average'] > 0 else 0
                data['trend'] = 'increasing' if costs[-1] > costs[0] else 'decreasing' if len(costs) > 1 else 'stable'
            else:
                data['monthly_average'] = 0
                data['variance'] = 0
                data['trend'] = 'stable'
        
        return cost_data
        
    except Exception as e:
        logger.error(f"Error getting cost data: {e}")
        return {}

def lambda_handler(event, context):
    """Lambda handler function using Strands Agent framework - CORRECTLY IMPLEMENTED"""
    try:
        logger.info(f"Budget Management Agent invoked with event: {json.dumps(event)}")
        
        # Extract query from the event
        query = None
        
        # Check if the event is from API Gateway
        if 'body' in event:
            try:
                # If body is a string (from API Gateway), parse it
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
                
                query = body.get('query', '')
            except Exception as e:
                logger.error(f"Error parsing request body: {str(e)}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                    },
                    'body': json.dumps({
                        'error': f"Invalid request format: {str(e)}",
                        'agent': 'BudgetManagementAgent'
                    })
                }
        # Direct Lambda invocation
        elif 'query' in event:
            query = event['query']
        # Supervisor agent invocation
        elif 'action' in event:
            query = event.get('parameters', {}).get('query', 'Analyze current budget status')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({
                    'error': 'No query provided in the request',
                    'agent': 'BudgetManagementAgent'
                })
            }
        
        # Initialize the Strands agent with tools - CORRECT IMPLEMENTATION
        budget_agent = Agent(
            system_prompt=BUDGET_MANAGEMENT_SYSTEM_PROMPT,
            tools=[
                calculator, 
                current_time, 
                get_budget_analysis,
                get_budget_recommendations
            ],
        )
        
        # Process the query using Claude 3.5 Haiku via Strands - LET STRANDS HANDLE THE RESPONSE
        logger.info(f"Processing budget query: {query}")
        agent_result = budget_agent(query)
        response_text = str(agent_result)  # This is the natural language response from Claude
        logger.info(f"Budget Agent response generated")
        
        # Return the natural language response from Claude, not raw JSON
        formatted_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'query': query,
                'response': response_text,  # Natural language response from Claude
                'agent': 'BudgetManagementAgent',
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
        logger.info("Budget Management Agent completed successfully")
        return formatted_response
        
    except Exception as e:
        logger.error(f"Budget Management Agent error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'error': str(e),
                'agent': 'BudgetManagementAgent',
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
