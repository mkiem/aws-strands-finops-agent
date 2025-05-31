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
ce_client = boto3.client('ce')  # AWS Cost Explorer client

# Environment variables
API_ID = os.environ.get('APPSYNC_API_ID')

def handler(event, context):
    """
    Main handler for the Cost Analysis Agent's AppSync interactions.
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
    arguments = event.get('arguments', {})
    
    if field_name == 'getCostAnalysis':
        return get_cost_analysis(arguments.get('timeRange', {}))
    else:
        logger.error(f"Unsupported query field: {field_name}")
        return {
            'error': f"Unsupported query field: {field_name}"
        }

def handle_mutation(field_name, event):
    """Handle GraphQL mutation operations"""
    arguments = event.get('arguments', {})
    
    if field_name == 'requestCostAnalysis':
        return request_cost_analysis(arguments.get('input', {}))
    else:
        logger.error(f"Unsupported mutation field: {field_name}")
        return {
            'error': f"Unsupported mutation field: {field_name}"
        }

def get_cost_analysis(time_range):
    """Get cost analysis results for a specific time range"""
    try:
        # In a real implementation, you would:
        # 1. Query Cost Explorer API
        # 2. Process and format the results
        # 3. Return the formatted data
        
        # For now, return mock data
        return {
            'id': str(uuid.uuid4()),
            'requestId': 'req-123',
            'status': 'COMPLETED',
            'timeRange': {
                'startDate': time_range.get('startDate'),
                'endDate': time_range.get('endDate')
            },
            'totalCost': 1234.56,
            'costByService': [
                {
                    'serviceName': 'Amazon EC2',
                    'cost': 567.89,
                    'usageQuantity': 720,
                    'unit': 'Hours'
                },
                {
                    'serviceName': 'Amazon S3',
                    'cost': 123.45,
                    'usageQuantity': 500,
                    'unit': 'GB-Month'
                }
            ],
            'costByTime': [
                {
                    'startTime': '2025-05-01T00:00:00Z',
                    'endTime': '2025-05-08T00:00:00Z',
                    'cost': 456.78
                },
                {
                    'startTime': '2025-05-08T00:00:00Z',
                    'endTime': '2025-05-15T00:00:00Z',
                    'cost': 345.67
                }
            ],
            'anomalies': [
                {
                    'id': 'anomaly-1',
                    'serviceName': 'Amazon EC2',
                    'amount': 123.45,
                    'percent': 25.5,
                    'reason': 'Unexpected increase in instance usage',
                    'detectedAt': datetime.utcnow().isoformat()
                }
            ],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cost analysis: {str(e)}")
        return {
            'error': f"Failed to get cost analysis: {str(e)}"
        }

def request_cost_analysis(input_data):
    """Request a new cost analysis"""
    request_id = str(uuid.uuid4())
    
    # Extract input parameters
    time_range = input_data.get('timeRange', {})
    granularity = input_data.get('granularity', 'DAILY')
    filters = input_data.get('filters', [])
    group_by = input_data.get('groupBy', [])
    
    # Log the request
    logger.info(f"New cost analysis request: {request_id}")
    
    # In a real implementation, you would:
    # 1. Store the request in a database
    # 2. Start an asynchronous process to perform the analysis
    # 3. Update the status as the analysis progresses
    
    # For now, return a request object with REQUESTED status
    request = {
        'id': request_id,
        'status': 'REQUESTED',
        'timeRange': {
            'startDate': time_range.get('startDate'),
            'endDate': time_range.get('endDate')
        },
        'granularity': granularity,
        'filters': [
            {
                'dimension': f.get('dimension'),
                'values': f.get('values', []),
                'operator': f.get('operator', 'EQUALS')
            } for f in filters
        ],
        'groupBy': group_by,
        'createdAt': datetime.utcnow().isoformat()
    }
    
    # Publish to subscription to notify clients
    publish_to_subscription('onCostAnalysisUpdate', {
        'id': request_id,
        'status': 'IN_PROGRESS',
        'timeRange': request['timeRange'],
        'createdAt': request['createdAt'],
        'updatedAt': datetime.utcnow().isoformat()
    })
    
    return request

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
