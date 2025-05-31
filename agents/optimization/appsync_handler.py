import json
import boto3
import os
import logging
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
appsync_client = boto3.client('appsync')
ta_client = boto3.client('trustedadvisor')  # AWS Trusted Advisor client
ec2_client = boto3.client('ec2')  # AWS EC2 client

# Environment variables
API_ID = os.environ.get('APPSYNC_API_ID')

def handler(event, context):
    """
    Main handler for the Cost Optimization Agent's AppSync interactions.
    This function processes GraphQL operations from AppSync.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract operation type and field name
    operation_type = event.get('info', {}).get('parentTypeName')
    field_name = event.get('info', {}).get('fieldName')
    
    # Process based on operation type and field
    if operation_type == 'Query':
        return handle_query(field_name, event)
    elif operation_type == 'Mutation':
        return handle_mutation(field_name, event)
    else:
        logger.error(f"Unsupported operation type: {operation_type}")
        return {
            'error': f"Unsupported operation type: {operation_type}"
        }

def handle_query(field_name, event):
    """Handle GraphQL query operations"""
    if field_name == 'getOptimizationRecommendations':
        return get_optimization_recommendations()
    else:
        logger.error(f"Unsupported query field: {field_name}")
        return {
            'error': f"Unsupported query field: {field_name}"
        }

def handle_mutation(field_name, event):
    """Handle GraphQL mutation operations"""
    arguments = event.get('arguments', {})
    
    if field_name == 'applyOptimization':
        return apply_optimization(arguments.get('recommendationId'))
    else:
        logger.error(f"Unsupported mutation field: {field_name}")
        return {
            'error': f"Unsupported mutation field: {field_name}"
        }

def get_optimization_recommendations():
    """Get cost optimization recommendations"""
    try:
        # In a real implementation, you would:
        # 1. Query Trusted Advisor for cost optimization checks
        # 2. Analyze EC2 instance usage patterns
        # 3. Check for unused resources
        # 4. Format and return recommendations
        
        # For now, return mock data
        return [
            {
                'id': 'rec-1',
                'title': 'Right-size underutilized EC2 instances',
                'description': 'Several EC2 instances have consistently low CPU utilization. Consider downsizing these instances to save costs.',
                'resourceId': 'i-0123456789abcdef0',
                'resourceType': 'EC2',
                'estimatedSavings': 45.67,
                'confidence': 0.85,
                'difficulty': 'EASY',
                'status': 'RECOMMENDED',
                'createdAt': datetime.utcnow().isoformat()
            },
            {
                'id': 'rec-2',
                'title': 'Delete unused EBS volumes',
                'description': 'Multiple EBS volumes are not attached to any instances. Consider deleting these volumes to reduce costs.',
                'resourceId': 'vol-0123456789abcdef0',
                'resourceType': 'EBS',
                'estimatedSavings': 12.34,
                'confidence': 0.95,
                'difficulty': 'EASY',
                'status': 'RECOMMENDED',
                'createdAt': datetime.utcnow().isoformat()
            },
            {
                'id': 'rec-3',
                'title': 'Use Reserved Instances for stable workloads',
                'description': 'Several EC2 instances have been running continuously for months. Consider purchasing Reserved Instances to reduce costs.',
                'resourceType': 'EC2',
                'estimatedSavings': 123.45,
                'confidence': 0.75,
                'difficulty': 'MEDIUM',
                'status': 'RECOMMENDED',
                'createdAt': datetime.utcnow().isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}")
        return {
            'error': f"Failed to get optimization recommendations: {str(e)}"
        }

def apply_optimization(recommendation_id):
    """Apply a specific optimization recommendation"""
    try:
        # In a real implementation, you would:
        # 1. Retrieve the recommendation details
        # 2. Apply the appropriate action based on the recommendation type
        # 3. Update the recommendation status
        # 4. Return the result
        
        # For now, return a mock result
        result = {
            'recommendationId': recommendation_id,
            'status': 'APPLIED',
            'message': f'Successfully applied recommendation {recommendation_id}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Publish to subscription to notify clients
        publish_to_subscription('onNewOptimizationRecommendation', {
            'id': str(uuid.uuid4()),
            'title': 'New optimization opportunity identified',
            'description': 'A new cost-saving opportunity has been identified based on your recent usage patterns.',
            'resourceType': 'S3',
            'estimatedSavings': 8.76,
            'confidence': 0.8,
            'difficulty': 'EASY',
            'status': 'RECOMMENDED',
            'createdAt': datetime.utcnow().isoformat()
        })
        
        return result
    except Exception as e:
        logger.error(f"Error applying optimization: {str(e)}")
        return {
            'recommendationId': recommendation_id,
            'status': 'FAILED',
            'message': f"Failed to apply optimization: {str(e)}",
            'timestamp': datetime.utcnow().isoformat()
        }

def publish_to_subscription(subscription_name, data):
    """Publish data to an AppSync subscription"""
    if not API_ID:
        logger.warning("AppSync API ID not configured, skipping subscription publish")
        return
    
    try:
        response = appsync_client.create_graphql_api(
            apiId=API_ID,
            payload=json.dumps({
                'data': data,
                'extensions': {
                    'subscription': {
                        'mqttTopic': subscription_name
                    }
                }
            })
        )
        logger.info(f"Published to subscription {subscription_name}: {response}")
    except Exception as e:
        logger.error(f"Error publishing to subscription: {str(e)}")
