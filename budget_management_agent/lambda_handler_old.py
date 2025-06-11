"""
AWS Budget Management Agent
Built with Strands SDK for comprehensive budget management and cost control
Uses Claude 3.5 Haiku via Strands framework
"""

import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

from strands import Agent, tool
from strands_tools import calculator, current_time
from strands.types.content import ContentBlock

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
budgets_client = boto3.client('budgets')
ce_client = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BUDGET_STATE_TABLE = os.environ.get('BUDGET_STATE_TABLE', 'budget-management-state')
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

IMPORTANT: When users ask for "recommendations", "suggestions", or "what budgets should I create", you MUST use the get_budget_recommendations() tool, NOT get_budget_analysis().

TOOL SELECTION GUIDANCE:
- For "recommend", "suggestions", "what budgets should I create" → ALWAYS use get_budget_recommendations()
- For "analyze", "current budget status", "existing budgets" → use get_budget_analysis()
- For "create budget" → use create_budget()
- For "monitor", "alerts", "check budgets" → use monitor_budget_alerts()
- For "performance", "history" → use get_budget_performance_history()

When responding:
- Always provide natural language responses, not raw JSON
- Provide clear, actionable budget recommendations
- Include specific dollar amounts and percentages
- Explain the rationale behind budget suggestions
- Highlight potential cost savings and risk mitigation
- Format responses with clear headings and bullet points
- Always include relevant timeframes and thresholds

Focus on proactive cost management and governance to help users maintain control over their AWS spending.
"""

@tool
def get_budget_analysis() -> str:
    """
    Analyze existing AWS budgets and their current performance status.
    Use this when users ask to analyze current budgets, check budget status, or review existing budget performance.
    
    Returns:
        JSON string containing analysis of existing budgets and their utilization
    """
    try:
        logger.info("Analyzing existing budgets")
        
        # Get all budgets for the account
        response = budgets_client.describe_budgets(AccountId=ACCOUNT_ID)
        budgets = response.get('Budgets', [])
        
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
            
            budget_info = {
                'budget_name': budget_name,
                'budget_type': budget_type,
                'budget_limit': budget_limit,
                'actual_spend': actual_spend,
                'forecasted_spend': forecasted_spend,
                'utilization_percent': round(utilization, 2),
                'forecast_utilization_percent': round(forecast_utilization, 2),
                'status': status,
                'time_unit': budget.get('TimeUnit', 'MONTHLY')
            }
            
            budget_analysis.append(budget_info)
            total_budgeted += budget_limit
            total_actual += actual_spend
            total_forecasted += forecasted_spend

        # Generate summary
        summary = {
            'total_budgets': len(budgets),
            'total_budgeted_amount': total_budgeted,
            'total_actual_spend': total_actual,
            'total_forecasted_spend': total_forecasted,
            'overall_utilization': round((total_actual / total_budgeted * 100) if total_budgeted > 0 else 0, 2),
            'forecast_utilization': round((total_forecasted / total_budgeted * 100) if total_budgeted > 0 else 0, 2)
        }
        
        result = {
            'summary': summary,
            'budgets': budget_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error analyzing budgets: {str(e)}")
        return json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})

@tool
def get_budget_recommendations() -> str:
    """
    Generate intelligent budget recommendations based on historical AWS spending patterns and cost analysis.
    Use this when users ask for budget suggestions, recommendations, or want to know what budgets to create.
    
    Returns:
        JSON string containing budget recommendations with specific dollar amounts and rationales
    """
    try:
        logger.info("Generating budget recommendations")
        
        # Get cost data for recommendations
        cost_data = get_cost_data_for_recommendations()
        
        recommendations = []
        
        # Analyze spending patterns by service
        for service, data in cost_data.items():
            if data['monthly_average'] > 10:  # Only recommend budgets for services with significant spend
                
                # Calculate recommended budget amount (110% of average with seasonal adjustment)
                recommended_amount = data['monthly_average'] * 1.1
                if data['variance'] > 0.3:  # High variance suggests seasonal patterns
                    recommended_amount *= 1.2
                
                recommendation = {
                    'service': service,
                    'recommended_budget_type': 'COST',
                    'recommended_amount': round(recommended_amount, 2),
                    'time_unit': 'MONTHLY',
                    'rationale': generate_budget_rationale(data),
                    'suggested_thresholds': [
                        {'threshold': 80, 'action': 'notification'},
                        {'threshold': 95, 'action': 'warning'},
                        {'threshold': 100, 'action': 'alert'}
                    ],
                    'historical_data': {
                        'monthly_average': data['monthly_average'],
                        'monthly_variance': data['variance'],
                        'trend': data['trend']
                    }
                }
                
                recommendations.append(recommendation)
        
        # Generate organization-level budget recommendations
        total_monthly_spend = sum([data['monthly_average'] for data in cost_data.values()])
        org_recommendation = {
            'budget_type': 'COST',
            'scope': 'ORGANIZATION',
            'recommended_amount': round(total_monthly_spend * 1.1, 2),
            'time_unit': 'MONTHLY',
            'rationale': 'Organization-wide spending control with 10% buffer',
            'priority': 'HIGH'
        }
        
        result = {
            'service_budgets': recommendations,
            'organization_budget': org_recommendation,
            'implementation_priority': [rec['service'] for rec in sorted(recommendations, key=lambda x: x['historical_data']['monthly_average'], reverse=True)[:5]],
            'estimated_savings': calculate_budget_savings(recommendations),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error generating budget recommendations: {str(e)}")
        return json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})

@tool
def create_budget(budget_name: str, amount: float, budget_type: str = "COST", time_unit: str = "MONTHLY", service_filter: str = None) -> str:
    """
    Create a new AWS budget with specified parameters.
    
    Args:
        budget_name: Name for the new budget
        amount: Budget amount in USD
        budget_type: Type of budget (COST, USAGE, RI_UTILIZATION, etc.)
        time_unit: Time unit for the budget (MONTHLY, QUARTERLY, ANNUALLY)
        service_filter: Optional AWS service to filter by
        
    Returns:
        JSON string with creation result
    """
    try:
        logger.info(f"Creating budget: {budget_name}")
        
        # Build budget definition
        budget = {
            'BudgetName': budget_name,
            'BudgetType': budget_type,
            'TimeUnit': time_unit,
            'BudgetLimit': {
                'Amount': str(amount),
                'Unit': 'USD'
            }
        }
        
        # Add service filter if specified
        if service_filter:
            budget['FilterExpression'] = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service_filter]
                }
            }
        
        # Add default notifications
        notifications = [
            {
                'Notification': {
                    'NotificationType': 'ACTUAL',
                    'ComparisonOperator': 'GREATER_THAN',
                    'Threshold': 80,
                    'ThresholdType': 'PERCENTAGE'
                },
                'Subscribers': [
                    {
                        'SubscriptionType': 'EMAIL',
                        'Address': 'admin@example.com'  # This should be configurable
                    }
                ]
            }
        ]
        
        # Create the budget
        response = budgets_client.create_budget(
            AccountId=ACCOUNT_ID,
            Budget=budget,
            NotificationsWithSubscribers=notifications
        )
        
        result = {
            'status': 'success',
            'budget_name': budget_name,
            'budget_type': budget_type,
            'amount': amount,
            'time_unit': time_unit,
            'service_filter': service_filter,
            'message': f'Budget "{budget_name}" created successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        return json.dumps({'error': str(e), 'status': 'failed', 'timestamp': datetime.utcnow().isoformat()})

@tool
def monitor_budget_alerts() -> str:
    """
    Monitor all budgets and generate alerts for those exceeding thresholds.
    
    Returns:
        JSON string containing budget monitoring results and alerts
    """
    try:
        logger.info("Monitoring budget performance")
        
        # Get all budgets
        response = budgets_client.describe_budgets(AccountId=ACCOUNT_ID)
        budgets = response.get('Budgets', [])
        
        alerts = []
        budget_status = []
        
        for budget in budgets:
            budget_name = budget['BudgetName']
            budget_limit = float(budget.get('BudgetLimit', {}).get('Amount', 0))
            actual_spend = float(budget.get('CalculatedSpend', {}).get('ActualSpend', {}).get('Amount', 0))
            forecasted_spend = float(budget.get('CalculatedSpend', {}).get('ForecastedSpend', {}).get('Amount', 0))
            
            utilization = (actual_spend / budget_limit * 100) if budget_limit > 0 else 0
            forecast_utilization = (forecasted_spend / budget_limit * 100) if budget_limit > 0 else 0
            
            status = {
                'budget_name': budget_name,
                'utilization': round(utilization, 2),
                'forecast_utilization': round(forecast_utilization, 2),
                'status': determine_budget_status(utilization, forecast_utilization),
                'actual_spend': actual_spend,
                'budget_limit': budget_limit,
                'remaining_budget': budget_limit - actual_spend
            }
            
            budget_status.append(status)
            
            # Generate alerts for budgets exceeding thresholds
            if utilization >= 90:
                alerts.append({
                    'severity': 'HIGH',
                    'budget_name': budget_name,
                    'message': f'Budget "{budget_name}" is at {utilization:.1f}% utilization',
                    'recommended_action': 'Review spending and consider budget adjustment'
                })
            elif forecast_utilization >= 100:
                alerts.append({
                    'severity': 'MEDIUM',
                    'budget_name': budget_name,
                    'message': f'Budget "{budget_name}" is forecasted to exceed limit ({forecast_utilization:.1f}%)',
                    'recommended_action': 'Monitor closely and prepare cost control measures'
                })
        
        result = {
            'budget_status': budget_status,
            'alerts': alerts,
            'summary': {
                'total_budgets': len(budgets),
                'budgets_over_80_percent': len([b for b in budget_status if b['utilization'] >= 80]),
                'budgets_forecasted_to_exceed': len([b for b in budget_status if b['forecast_utilization'] >= 100]),
                'high_priority_alerts': len([a for a in alerts if a['severity'] == 'HIGH'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error monitoring budgets: {str(e)}")
        return json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})

@tool
def get_budget_performance_history(budget_name: str) -> str:
    """
    Get detailed performance history for a specific budget.
    
    Args:
        budget_name: Name of the budget to analyze
        
    Returns:
        JSON string containing budget performance history
    """
    try:
        logger.info(f"Getting budget performance for: {budget_name}")
        
        # Get budget performance history
        response = budgets_client.describe_budget_performance_history(
            AccountId=ACCOUNT_ID,
            BudgetName=budget_name,
            TimePeriod={
                'Start': datetime.now() - timedelta(days=90),
                'End': datetime.now()
            }
        )
        
        performance_history = response.get('BudgetPerformanceHistory', {})
        budget_data = performance_history.get('BudgetedAndActualAmountsList', [])
        
        # Process performance data
        performance_analysis = []
        for period in budget_data:
            budgeted = float(period.get('BudgetedAmount', {}).get('Amount', 0))
            actual = float(period.get('ActualAmount', {}).get('Amount', 0))
            variance = actual - budgeted
            variance_percent = (variance / budgeted * 100) if budgeted > 0 else 0
            
            performance_analysis.append({
                'time_period': period.get('TimePeriod', {}),
                'budgeted_amount': budgeted,
                'actual_amount': actual,
                'variance': variance,
                'variance_percent': round(variance_percent, 2),
                'status': 'over_budget' if variance > 0 else 'under_budget'
            })
        
        # Calculate summary statistics
        total_periods = len(performance_analysis)
        over_budget_periods = len([p for p in performance_analysis if p['variance'] > 0])
        avg_variance = sum([p['variance_percent'] for p in performance_analysis]) / total_periods if total_periods > 0 else 0
        
        result = {
            'budget_name': budget_name,
            'performance_history': performance_analysis,
            'summary': {
                'total_periods': total_periods,
                'over_budget_periods': over_budget_periods,
                'over_budget_rate': round((over_budget_periods / total_periods * 100) if total_periods > 0 else 0, 2),
                'average_variance_percent': round(avg_variance, 2)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Error getting budget performance: {str(e)}")
        return json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
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

def generate_budget_rationale(data: Dict) -> str:
    """Generate rationale for budget recommendation"""
    rationale = f"Based on ${data['monthly_average']:.2f} average monthly spend"
    
    if data['variance'] > 0.3:
        rationale += " with high variance suggesting seasonal patterns"
    
    if data['trend'] == 'increasing':
        rationale += " and increasing trend"
    elif data['trend'] == 'decreasing':
        rationale += " and decreasing trend"
    
    return rationale

def calculate_budget_savings(recommendations: List[Dict]) -> Dict[str, float]:
    """Estimate potential savings from budget implementation"""
    total_recommended = sum([rec['recommended_amount'] for rec in recommendations])
    total_current = sum([rec['historical_data']['monthly_average'] for rec in recommendations])
    
    return {
        'monthly_budget_total': total_recommended,
        'current_monthly_average': total_current,
        'potential_monthly_savings': max(0, total_current - total_recommended),
        'annual_savings_estimate': max(0, (total_current - total_recommended) * 12)
    }


def lambda_handler(event, context):
    """Lambda handler function using Strands Agent framework"""
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
        
        # Initialize the Strands agent with tools
        budget_agent = Agent(
            system_prompt=BUDGET_MANAGEMENT_SYSTEM_PROMPT,
            tools=[
                calculator, 
                current_time, 
                get_budget_analysis,
                get_budget_recommendations,
                create_budget,
                monitor_budget_alerts,
                get_budget_performance_history
            ],
        )
        
        # Process the query using Claude 3.5 Haiku via Strands
        logger.info(f"Processing budget query: {query}")
        agent_result = budget_agent(query)
        response_text = str(agent_result)
        logger.info(f"Budget Agent response generated")
        
        # Format the response as natural language, not raw JSON
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
