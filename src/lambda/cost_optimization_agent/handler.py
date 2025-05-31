"""
Lambda handler for the Cost Optimization Agent.
"""

import json
import logging
import os
import traceback
from typing import Dict, Any, List

import boto3
from strands import Agent, tool

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define custom tools for the Cost Optimization Agent
@tool
def get_trusted_advisor_recommendations() -> Dict[str, Any]:
    """
    Get AWS Trusted Advisor cost optimization recommendations.
    
    Returns:
        Cost optimization recommendations from Trusted Advisor
    """
    try:
        support_client = boto3.client('support', region_name=os.environ.get("AWS_REGION", "us-east-1"))
        
        # Get all Trusted Advisor checks
        checks_response = support_client.describe_trusted_advisor_checks(
            language='en'
        )
        
        # Filter for cost optimization checks
        cost_checks = [check for check in checks_response['checks'] if check['category'] == 'cost_optimizing']
        
        # Get results for cost optimization checks
        results = {}
        for check in cost_checks:
            check_id = check['id']
            check_name = check['name']
            
            try:
                check_result = support_client.describe_trusted_advisor_check_result(
                    checkId=check_id,
                    language='en'
                )
                
                results[check_name] = check_result['result']
            except Exception as e:
                logger.warning(f"Error getting results for check {check_name}: {str(e)}")
                results[check_name] = {"error": str(e)}
        
        return results
    except Exception as e:
        logger.error(f"Error getting Trusted Advisor recommendations: {str(e)}")
        return {"error": str(e)}

@tool
def get_underutilized_resources() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get underutilized AWS resources that could be optimized for cost.
    
    Returns:
        Dictionary of underutilized resources by type
    """
    try:
        ec2_client = boto3.client('ec2', region_name=os.environ.get("AWS_REGION", "us-east-1"))
        
        # Get all EC2 instances
        instances_response = ec2_client.describe_instances()
        
        # Filter for running instances
        running_instances = []
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                if instance.get('State', {}).get('Name') == 'running':
                    running_instances.append(instance)
        
        # Get CloudWatch client for metrics
        cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get("AWS_REGION", "us-east-1"))
        
        # Check CPU utilization for each instance
        underutilized_instances = []
        for instance in running_instances:
            instance_id = instance['InstanceId']
            
            try:
                # Get average CPU utilization for the past 14 days
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        },
                    ],
                    StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=14),
                    EndTime=datetime.datetime.utcnow(),
                    Period=86400,  # 1 day in seconds
                    Statistics=['Average']
                )
                
                # Calculate the overall average
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    avg_cpu = sum(point['Average'] for point in datapoints) / len(datapoints)
                    
                    # If average CPU utilization is less than 10%, consider it underutilized
                    if avg_cpu < 10.0:
                        underutilized_instances.append({
                            'InstanceId': instance_id,
                            'InstanceType': instance.get('InstanceType'),
                            'AverageCPU': avg_cpu,
                            'LaunchTime': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None
                        })
            except Exception as e:
                logger.warning(f"Error getting metrics for instance {instance_id}: {str(e)}")
        
        return {
            'UnderutilizedEC2Instances': underutilized_instances
        }
    except Exception as e:
        logger.error(f"Error getting underutilized resources: {str(e)}")
        return {"error": str(e)}

# Initialize the agent outside the handler for better cold start performance
def initialize_agent():
    """Initialize the Strands Agent with appropriate configuration."""
    try:
        # Import tools that will be used by the agent
        from strands_tools import current_time
        
        # Initialize the agent with cost optimization tools
        agent = Agent(
            model_id=os.environ.get("MODEL_ID", "amazon.titan-text-express-v1"),
            region=os.environ.get("AWS_REGION", "us-east-1"),
            temperature=float(os.environ.get("TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("MAX_TOKENS", "4096")),
            tools=[current_time, get_trusted_advisor_recommendations]
        )
        
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Initialize the agent
try:
    cost_optimization_agent = initialize_agent()
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    cost_optimization_agent = None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for the Cost Optimization Agent.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        Response object
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if agent was initialized successfully
        if cost_optimization_agent is None:
            raise Exception("Agent failed to initialize")
        
        # Extract the user message from the event
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        user_message = body.get('message', '')
        session_id = body.get('session_id', '')
        
        if not user_message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No message provided'})
            }
        
        logger.info(f"Processing message: {user_message}")
        
        # Process the message with the agent
        response = cost_optimization_agent(user_message)
        
        # Return the response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': response,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error processing request: {str(e)}"
            })
        }
