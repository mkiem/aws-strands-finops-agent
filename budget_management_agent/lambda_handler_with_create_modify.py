import json
from strands import Agent
from strands_tools import calculator, current_time
import boto3
import os
import logging
from datetime import datetime, timedelta
from strands import tool
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
budgets_client = boto3.client('budgets')
ce_client = boto3.client('ce')
ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID')

# System prompt for Budget Management Agent
BUDGET_MANAGEMENT_SYSTEM_PROMPT = """
You are an AWS Budget Management Agent specialized in proactive cost control and governance.

Your capabilities include:
- Creating new AWS budgets based on cost analysis and user requirements
- Modifying existing AWS budgets (amount, time period, service filters)
- Monitoring budget performance and generating alerts
- Providing budget recommendations based on spending patterns
- Analyzing budget performance history and trends

You have access to AWS Budgets API and Cost Explorer data to provide comprehensive budget management.

IMPORTANT Tool Usage Guidelines:
- When users ask for "recommendations", "suggestions", or "what budgets should I create", use get_budget_recommendations()
- When users ask to "create a budget" or "set up a budget", use create_budget()
- When users ask to "modify", "update", or "change a budget", use modify_budget()
- When users ask to "analyze budgets" or "check budget status", use get_budget_analysis()

Budget Creation Guidelines:
- Default to MONTHLY time unit and COST budget type unless specified
- Suggest reasonable budget amounts based on historical spending
- Include service filters when users mention specific AWS services
- Always confirm budget details before creation

Budget Modification Guidelines:
- Explain that budget name and type cannot be changed
- Clearly describe what changes will be made
- Warn that calculated spend resets after modifications

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

@tool
def create_budget(budget_name: str, budget_amount: float, budget_type: str = "COST", time_unit: str = "MONTHLY", service_filter: str = None) -> str:
    """
    Create a new AWS budget with specified parameters.
    
    Args:
        budget_name: Name for the new budget (must be unique)
        budget_amount: Budget limit amount in USD
        budget_type: Type of budget - COST, USAGE, RI_UTILIZATION, RI_COVERAGE, SAVINGS_PLANS_UTILIZATION, SAVINGS_PLANS_COVERAGE (default: COST)
        time_unit: Time period - DAILY, MONTHLY, QUARTERLY, ANNUALLY (default: MONTHLY)
        service_filter: Optional AWS service to filter budget (e.g., "Amazon Elastic Compute Cloud - Compute")
    
    Returns:
        String confirming budget creation or error message
    """
    try:
        logger.info(f"Creating budget: {budget_name} with amount ${budget_amount}")
        
        # Validate inputs
        if not budget_name or not budget_name.strip():
            return "Budget name cannot be empty. Please provide a valid budget name."
        
        if budget_amount <= 0:
            return "Budget amount must be greater than 0. Please provide a valid budget amount."
        
        valid_budget_types = ["COST", "USAGE", "RI_UTILIZATION", "RI_COVERAGE", "SAVINGS_PLANS_UTILIZATION", "SAVINGS_PLANS_COVERAGE"]
        if budget_type not in valid_budget_types:
            return f"Invalid budget type. Valid types are: {', '.join(valid_budget_types)}"
        
        valid_time_units = ["DAILY", "MONTHLY", "QUARTERLY", "ANNUALLY"]
        if time_unit not in valid_time_units:
            return f"Invalid time unit. Valid units are: {', '.join(valid_time_units)}"
        
        # Build budget object
        budget = {
            'BudgetName': budget_name.strip(),
            'BudgetType': budget_type,
            'TimeUnit': time_unit,
            'BudgetLimit': {
                'Amount': str(budget_amount),
                'Unit': 'USD'
            },
            'CostTypes': {
                'IncludeTax': True,
                'IncludeSubscription': True,
                'UseBlended': False,
                'IncludeRefund': False,
                'IncludeCredit': False,
                'IncludeUpfront': True,
                'IncludeRecurring': True,
                'IncludeOtherSubscription': True,
                'IncludeSupport': True,
                'IncludeDiscount': True,
                'UseAmortized': False
            }
        }
        
        # Add service filter if specified
        if service_filter:
            budget['CostFilters'] = {
                'Service': [service_filter]
            }
        
        # Create the budget
        response = budgets_client.create_budget(
            AccountId=ACCOUNT_ID,
            Budget=budget
        )
        
        # Build success message
        filter_info = f" filtered to {service_filter}" if service_filter else ""
        success_message = f"""✅ Successfully created budget '{budget_name}'!

**Budget Details:**
- **Name**: {budget_name}
- **Type**: {budget_type}
- **Amount**: ${budget_amount:,.2f} USD
- **Time Period**: {time_unit}
- **Scope**: {service_filter if service_filter else 'All AWS services'}{filter_info}

**Cost Types Included:**
- Taxes, subscriptions, support charges
- Recurring and upfront costs
- Discounts and other subscription costs

The budget is now active and will track your {budget_type.lower()} spending. You can view it in the AWS Budgets console or ask me to analyze your budget performance."""
        
        logger.info(f"Successfully created budget: {budget_name}")
        return success_message
        
    except budgets_client.exceptions.DuplicateRecordException:
        return f"❌ A budget named '{budget_name}' already exists. Budget names must be unique. Please choose a different name or use modify_budget() to update the existing budget."
    
    except budgets_client.exceptions.CreationLimitExceededException:
        return "❌ You have reached the maximum number of budgets allowed for your account. Please delete an existing budget before creating a new one."
    
    except budgets_client.exceptions.InvalidParameterException as e:
        return f"❌ Invalid parameter provided: {str(e)}. Please check your budget parameters and try again."
    
    except budgets_client.exceptions.AccessDeniedException:
        return "❌ Access denied. Please ensure you have the necessary permissions to create budgets (budgets:CreateBudget)."
    
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        return f"❌ I encountered an error while creating the budget: {str(e)}. Please check your AWS permissions and try again."

@tool
def modify_budget(budget_name: str, new_budget_amount: float = None, new_time_unit: str = None, add_service_filter: str = None, remove_service_filter: bool = False) -> str:
    """
    Modify an existing AWS budget. You can update the budget amount, time unit, or service filters.
    Note: Budget name and type cannot be changed.
    
    Args:
        budget_name: Name of the existing budget to modify
        new_budget_amount: New budget limit amount in USD (optional)
        new_time_unit: New time period - DAILY, MONTHLY, QUARTERLY, ANNUALLY (optional)
        add_service_filter: Add AWS service filter (e.g., "Amazon Elastic Compute Cloud - Compute") (optional)
        remove_service_filter: Remove existing service filters (optional)
    
    Returns:
        String confirming budget modification or error message
    """
    try:
        logger.info(f"Modifying budget: {budget_name}")
        
        # Validate inputs
        if not budget_name or not budget_name.strip():
            return "Budget name cannot be empty. Please provide a valid budget name."
        
        if new_budget_amount is not None and new_budget_amount <= 0:
            return "Budget amount must be greater than 0. Please provide a valid budget amount."
        
        if new_time_unit:
            valid_time_units = ["DAILY", "MONTHLY", "QUARTERLY", "ANNUALLY"]
            if new_time_unit not in valid_time_units:
                return f"Invalid time unit. Valid units are: {', '.join(valid_time_units)}"
        
        # Get existing budget
        try:
            response = budgets_client.describe_budgets(
                AccountId=ACCOUNT_ID
            )
            
            # Find the specific budget
            existing_budget = None
            for budget in response.get('Budgets', []):
                if budget['BudgetName'] == budget_name.strip():
                    existing_budget = budget
                    break
            
            if not existing_budget:
                return f"❌ Budget '{budget_name}' not found. Please check the budget name and try again."
            
        except budgets_client.exceptions.NotFoundException:
            return f"❌ Budget '{budget_name}' not found. Please check the budget name and try again."
        
        # Build updated budget object (start with existing budget)
        updated_budget = existing_budget.copy()
        
        # Track changes for response message
        changes = []
        
        # Update budget amount if provided
        if new_budget_amount is not None:
            old_amount = float(existing_budget.get('BudgetLimit', {}).get('Amount', 0))
            updated_budget['BudgetLimit'] = {
                'Amount': str(new_budget_amount),
                'Unit': 'USD'
            }
            changes.append(f"Budget amount: ${old_amount:,.2f} → ${new_budget_amount:,.2f}")
        
        # Update time unit if provided
        if new_time_unit:
            old_time_unit = existing_budget.get('TimeUnit', 'UNKNOWN')
            updated_budget['TimeUnit'] = new_time_unit
            changes.append(f"Time unit: {old_time_unit} → {new_time_unit}")
        
        # Handle service filters
        if remove_service_filter:
            if 'CostFilters' in updated_budget:
                old_filters = updated_budget.get('CostFilters', {}).get('Service', [])
                del updated_budget['CostFilters']
                changes.append(f"Removed service filters: {', '.join(old_filters) if old_filters else 'None'}")
        elif add_service_filter:
            if 'CostFilters' not in updated_budget:
                updated_budget['CostFilters'] = {}
            updated_budget['CostFilters']['Service'] = [add_service_filter]
            changes.append(f"Added service filter: {add_service_filter}")
        
        # Check if any changes were made
        if not changes:
            return f"No changes specified for budget '{budget_name}'. Please provide at least one parameter to modify (new_budget_amount, new_time_unit, add_service_filter, or remove_service_filter)."
        
        # Remove calculated spend (AWS requirement for updates)
        if 'CalculatedSpend' in updated_budget:
            del updated_budget['CalculatedSpend']
        
        # Update the budget
        response = budgets_client.update_budget(
            AccountId=ACCOUNT_ID,
            NewBudget=updated_budget
        )
        
        # Build success message
        success_message = f"""✅ Successfully modified budget '{budget_name}'!

**Changes Made:**
{chr(10).join([f"- {change}" for change in changes])}

**Updated Budget Details:**
- **Name**: {updated_budget['BudgetName']}
- **Type**: {updated_budget['BudgetType']}
- **Amount**: ${float(updated_budget.get('BudgetLimit', {}).get('Amount', 0)):,.2f} USD
- **Time Period**: {updated_budget['TimeUnit']}
- **Service Filter**: {updated_budget.get('CostFilters', {}).get('Service', ['All AWS services'])[0] if updated_budget.get('CostFilters', {}).get('Service') else 'All AWS services'}

⚠️ **Note**: The calculated spend has been reset to zero and will be recalculated as new usage data becomes available."""
        
        logger.info(f"Successfully modified budget: {budget_name}")
        return success_message
        
    except budgets_client.exceptions.NotFoundException:
        return f"❌ Budget '{budget_name}' not found. Please check the budget name and try again."
    
    except budgets_client.exceptions.InvalidParameterException as e:
        return f"❌ Invalid parameter provided: {str(e)}. Please check your budget parameters and try again."
    
    except budgets_client.exceptions.AccessDeniedException:
        return "❌ Access denied. Please ensure you have the necessary permissions to modify budgets (budgets:ModifyBudget)."
    
    except Exception as e:
        logger.error(f"Error modifying budget: {str(e)}")
        return f"❌ I encountered an error while modifying the budget: {str(e)}. Please check your AWS permissions and try again."

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
            return "I'm unable to generate budget recommendations at this time due to insufficient cost data. Please ensure you have AWS Cost Explorer enabled and some historical spending data available."
        
        # Sort services by total cost (descending)
        sorted_services = sorted(cost_data.items(), key=lambda x: x[1]['total'], reverse=True)
        
        recommendations = []
        total_recommended_budget = 0
        
        # Generate recommendations for top spending services
        for service, data in sorted_services[:10]:  # Top 10 services
            if data['total'] > 10:  # Only recommend budgets for services with >$10 total spend
                monthly_avg = data['monthly_average']
                variance = data['variance']
                
                # Calculate recommended budget with buffer
                if variance > 0.5:  # High variance
                    buffer_multiplier = 1.5
                    risk_level = "High variance"
                elif variance > 0.2:  # Medium variance
                    buffer_multiplier = 1.3
                    risk_level = "Medium variance"
                else:  # Low variance
                    buffer_multiplier = 1.2
                    risk_level = "Stable spending"
                
                recommended_amount = monthly_avg * buffer_multiplier
                total_recommended_budget += recommended_amount
                
                recommendations.append(f"""
**{service}**
- Current monthly average: ${monthly_avg:.2f}
- Recommended budget: ${recommended_amount:.2f}
- Buffer: {(buffer_multiplier-1)*100:.0f}% ({risk_level})
- Trend: {data['trend']}
""")
        
        # Generate overall budget recommendation
        overall_buffer = 1.2
        overall_recommended = total_recommended_budget * overall_buffer
        
        result = f"""# Budget Recommendations Based on Historical Spending

## Service-Specific Budget Recommendations

{''.join(recommendations)}

## Overall Budget Strategy

**Total Recommended Monthly Budget**: ${total_recommended_budget:.2f}
**Overall Account Budget**: ${overall_recommended:.2f} (with 20% buffer)

## Implementation Priority

1. **Start with top 3 services** - These represent your highest cost areas
2. **Set up account-wide budget** - ${overall_recommended:.2f} monthly limit
3. **Add service-specific budgets** - For granular control
4. **Configure alerts** - At 80%, 90%, and 100% thresholds

## Budget Types Recommended

- **Cost budgets** for spending control
- **Monthly time period** for regular monitoring
- **Email notifications** for proactive alerts

Would you like me to create any of these recommended budgets for you?"""
        
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

def lambda_handler(event, context):
    """Lambda handler function using Strands Agent framework - EXACTLY like cost-forecast agent"""
    try:
        logger.info(f"Received event: {event}")
        
        # Extract query from the event - EXACTLY like cost-forecast agent
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
                error_blocks = [
                    {"text": "# Error Processing Request\n\n"},
                    {"text": f"I encountered an error while parsing your request: {str(e)}\n\n"},
                    {"text": "Please ensure your request is properly formatted and try again."}
                ]
                
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                    },
                    'body': json.dumps({
                        'error': 'Invalid request format',
                        'response': error_blocks
                    })
                }
        
        # Direct invocation (from Lambda console or other services)
        elif 'query' in event:
            query = event['query']
        
        # Handle empty or missing query
        if not query:
            error_blocks = [
                {"text": "# No Query Provided\n\n"},
                {"text": "Please provide a query about AWS budget management.\n\n"},
                {"text": "**Examples:**\n"},
                {"text": "- What budgets should I create?\n"},
                {"text": "- Analyze my current budgets\n"},
                {"text": "- Create a budget for EC2 with $500 limit\n"},
                {"text": "- Show me budget recommendations"}
            ]
            
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
                    'response': error_blocks
                })
            }
        
        # Initialize the agent with tools - EXACTLY like cost-forecast agent
        budget_agent = Agent(
            system_prompt=BUDGET_MANAGEMENT_SYSTEM_PROMPT,
            tools=[calculator, current_time, get_budget_analysis, get_budget_recommendations, create_budget, modify_budget],
        )
        
        # Process the query - EXACTLY like cost-forecast agent
        logger.info(f"Processing query: {query}")
        agent_result = budget_agent(query)
        response_text = str(agent_result)
        logger.info(f"Agent response: {response_text}")
        
        # Format the response - EXACTLY like cost-forecast agent
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
                'response': response_text
            })
        }
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        error_blocks = [
            {"text": "# Error Processing Request\n\n"},
            {"text": f"I encountered an error while processing your budget management request: {str(e)}\n\n"},
            {"text": "Please check your request and try again. If the problem persists, please contact support."}
        ]
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'An error occurred processing your request',
                'agent': 'Budget-Management-Agent'
            })
        }
