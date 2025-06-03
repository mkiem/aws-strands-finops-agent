import json
from strands import Agent
from strands_tools import calculator, current_time
import boto3
import os
import logging
from datetime import datetime, timedelta
from strands import tool

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

@tool
def get_aws_cost_summary(time_period="MONTH_TO_DATE"):
    """
    Get a summary of AWS costs for the specified time period.
    
    Args:
        time_period: The time period for the cost data (e.g., MONTH_TO_DATE, LAST_MONTH)
        
    Returns:
        A summary of AWS costs
    """
    # Use the region from environment variable
    region = os.environ.get('REGION', 'us-east-1')
    ce = boto3.client('ce', region_name=region)
    
    # Define time period
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    if time_period == "MONTH_TO_DATE":
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    elif time_period == "LAST_MONTH":
        first_of_month = datetime.now().replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        start_date = last_month_end.replace(day=1).strftime('%Y-%m-%d')
        end_date = last_month_end.strftime('%Y-%m-%d')
    else:
        # Default to last 30 days
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        return {
            'time_period': f"{start_date} to {end_date}",
            'results': response['ResultsByTime']
        }
        
    except Exception as e:
        logger.error(f"Error getting cost data: {str(e)}")
        return {"error": str(e)}

# Define the FinOps system prompt
FINOPS_SYSTEM_PROMPT = """You are a FinOps assistant for AWS. You can:

1. Analyze AWS cost data
2. Provide cost optimization recommendations
3. Explain AWS pricing models
4. Help with cost allocation and tagging strategies

When analyzing costs:
1. Focus on the most expensive services first
2. Look for unusual spending patterns
3. Identify resources that might be underutilized
4. Suggest appropriate instance sizing and purchasing options

Always provide clear, actionable recommendations and explain the potential cost savings.
"""

def handler(event, context):
    """
    AWS Lambda handler function for the FinOps Agent
    """
    try:
        logger.info(f"Received event: {event}")
        
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
                    'body': json.dumps({'error': f"Invalid request format: {str(e)}"})
                }
        # Direct Lambda invocation
        elif 'query' in event:
            query = event['query']
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({'error': 'No query provided in the request'})
            }
        
        # Initialize the agent with tools
        finops_agent = Agent(
            system_prompt=FINOPS_SYSTEM_PROMPT,
            tools=[calculator, current_time, get_aws_cost_summary],
        )
        
        # Process the query
        logger.info(f"Processing query: {query}")
        response = finops_agent(query)
        logger.info(f"Agent response: {response}")
        
        # Return the response in the format expected by API Gateway
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'query': query,
                'response': str(response)
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({'error': str(e)})
        }
