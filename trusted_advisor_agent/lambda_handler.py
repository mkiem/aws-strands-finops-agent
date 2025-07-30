import json
import logging
import os
from typing import Dict, Any
from datetime import datetime

from strands import Agent, tool
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
support_client = boto3.client('support', region_name='us-east-1')
trustedadvisor_client = boto3.client('trustedadvisor', region_name='us-east-1')

# Custom JSON Encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@tool
def get_trusted_advisor_recommendations(category: str = "cost_optimizing") -> str:
    """
    Get cost optimization recommendations from AWS Trusted Advisor.
    
    Args:
        category: The category of recommendations to retrieve (default: cost_optimizing)
        
    Returns:
        JSON string containing the recommendations
    """
    try:
        logger.info(f"Getting Trusted Advisor recommendations for category: {category}")
        
        # Try new TrustedAdvisor API first
        try:
            # Get both warning and error status recommendations
            all_recommendations = []
            
            # Get warning status (Investigation recommended)
            logger.info("Fetching warning status recommendations...")
            warning_response = trustedadvisor_client.list_recommendations(
                pillar='cost_optimizing',
                status='warning',
                maxResults=100
            )
            
            # Get error status (Action recommended)  
            logger.info("Fetching error status recommendations...")
            error_response = trustedadvisor_client.list_recommendations(
                pillar='cost_optimizing',
                status='error',
                maxResults=100
            )
            
            # Combine both responses
            warning_recs = warning_response.get('recommendationSummaries', [])
            error_recs = error_response.get('recommendationSummaries', [])
            
            logger.info(f"Found {len(warning_recs)} warning recommendations and {len(error_recs)} error recommendations")
            
            for rec in warning_recs + error_recs:
                recommendation_data = {
                    'id': rec.get('id'),
                    'arn': rec.get('arn'),
                    'name': rec.get('name'),
                    'status': rec.get('status'),
                    'pillar': rec.get('pillars', []),
                    'source': rec.get('source'),
                    'aws_services': rec.get('awsServices', []),
                    'created_at': rec.get('createdAt'),
                    'last_updated_at': rec.get('lastUpdatedAt'),
                    'lifecycle_stage': rec.get('lifecycleStage'),
                    'type': rec.get('type')
                }
                
                # Add cost-specific data if available
                pillar_aggregates = rec.get('pillarSpecificAggregates', {})
                cost_data = pillar_aggregates.get('costOptimizing', {})
                if cost_data:
                    recommendation_data['estimated_monthly_savings'] = cost_data.get('estimatedMonthlySavings', 0)
                    recommendation_data['estimated_percent_monthly_savings'] = cost_data.get('estimatedPercentMonthlySavings', 0)
                
                # Add resource counts
                resource_aggregates = rec.get('resourcesAggregates', {})
                if resource_aggregates:
                    recommendation_data['resource_counts'] = {
                        'error_count': resource_aggregates.get('errorCount', 0),
                        'warning_count': resource_aggregates.get('warningCount', 0),
                        'ok_count': resource_aggregates.get('okCount', 0)
                    }
                
                all_recommendations.append(recommendation_data)
            
            return json.dumps({
                'source': 'TrustedAdvisor API',
                'recommendations': all_recommendations,
                'total_count': len(all_recommendations),
                'warning_count': len(warning_recs),
                'error_count': len(error_recs)
            }, cls=DateTimeEncoder)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.warning(f"TrustedAdvisor API error: {error_code} - {error_message}")
            
            if error_code in ['AccessDeniedException', 'UnauthorizedOperation']:
                logger.info("New TrustedAdvisor API not accessible, falling back to Support API")
                
                # Fallback to Support API
                checks_response = support_client.describe_trusted_advisor_checks(language='en')
                cost_checks = [
                    check for check in checks_response['checks'] 
                    if 'cost' in check['category'].lower() or 'Cost' in check['name']
                ]
                
                logger.info(f"Found {len(cost_checks)} cost-related checks in Support API")
                
                recommendations = []
                for check in cost_checks[:20]:  # Limit to first 20 checks
                    try:
                        result = support_client.describe_trusted_advisor_check_result(
                            checkId=check['id'],
                            language='en'
                        )
                        
                        check_result = result['result']
                        if check_result['status'] in ['warning', 'error']:
                            recommendation_data = {
                                'id': check['id'],
                                'name': check['name'],
                                'description': check['description'],
                                'status': check_result['status'],
                                'category': check['category'],
                                'flagged_resources': len(check_result.get('flaggedResources', [])),
                                'timestamp': check_result.get('timestamp')
                            }
                            
                            # Add cost-specific data if available
                            category_summary = check_result.get('categorySpecificSummary', {})
                            cost_optimizing = category_summary.get('costOptimizing', {})
                            if cost_optimizing:
                                recommendation_data['estimated_monthly_savings'] = cost_optimizing.get('estimatedMonthlySavings', 0)
                            
                            # Add resource summary
                            resources_summary = check_result.get('resourcesSummary', {})
                            if resources_summary:
                                recommendation_data['resources_summary'] = {
                                    'resources_processed': resources_summary.get('resourcesProcessed', 0),
                                    'resources_flagged': resources_summary.get('resourcesFlagged', 0),
                                    'resources_ignored': resources_summary.get('resourcesIgnored', 0),
                                    'resources_suppressed': resources_summary.get('resourcesSuppressed', 0)
                                }
                            
                            recommendations.append(recommendation_data)
                            
                    except Exception as check_error:
                        logger.warning(f"Error getting details for check {check['id']}: {str(check_error)}")
                        continue
                
                warning_count = len([r for r in recommendations if r.get('status') == 'warning'])
                error_count = len([r for r in recommendations if r.get('status') == 'error'])
                
                return json.dumps({
                    'source': 'Support API',
                    'recommendations': recommendations,
                    'total_count': len(recommendations),
                    'warning_count': warning_count,
                    'error_count': error_count
                }, cls=DateTimeEncoder)
            else:
                raise e
                
    except Exception as e:
        logger.error(f"Error getting Trusted Advisor recommendations: {str(e)}")
        return json.dumps({
            'error': f'Failed to retrieve recommendations: {str(e)}',
            'recommendations': [],
            'total_count': 0,
            'details': f'Error type: {type(e).__name__}'
        })

@tool
def get_cost_optimization_summary() -> str:
    """
    Get a summary of all cost optimization opportunities from Trusted Advisor.
    
    Returns:
        JSON string containing cost optimization summary
    """
    try:
        logger.info("Getting cost optimization summary")
        
        # Get all cost optimization recommendations
        recommendations_data = json.loads(get_trusted_advisor_recommendations("cost_optimizing"))
        recommendations = recommendations_data.get('recommendations', [])
        
        # Calculate summary statistics
        total_recommendations = len(recommendations)
        warning_count = len([r for r in recommendations if r.get('status') == 'warning'])
        error_count = len([r for r in recommendations if r.get('status') == 'error'])
        
        # Calculate potential savings (if available)
        total_savings = 0
        for rec in recommendations:
            savings = rec.get('estimated_monthly_savings', 0)
            if isinstance(savings, (int, float)):
                total_savings += savings
        
        # Group by category/type
        categories = {}
        for rec in recommendations:
            category = rec.get('category', rec.get('type', 'Unknown'))
            if category not in categories:
                categories[category] = []
            categories[category].append(rec)
        
        summary = {
            'source': recommendations_data.get('source', 'Unknown'),
            'total_recommendations': total_recommendations,
            'status_breakdown': {
                'warning': warning_count,
                'error': error_count
            },
            'estimated_monthly_savings': round(total_savings, 2),
            'categories': {cat: len(recs) for cat, recs in categories.items()},
            'top_recommendations': recommendations[:5]  # Top 5 recommendations
        }
        
        return json.dumps(summary, cls=DateTimeEncoder)
        
    except Exception as e:
        logger.error(f"Error getting cost optimization summary: {str(e)}")
        return json.dumps({
            'error': f'Failed to retrieve cost optimization summary: {str(e)}',
            'total_recommendations': 0,
            'estimated_monthly_savings': 0,
            'details': f'Error type: {type(e).__name__}'
        })

# System prompt for the Trusted Advisor Agent
TRUSTED_ADVISOR_SYSTEM_PROMPT = """
You are a specialized AWS Trusted Advisor Cost Optimization Agent. Your primary function is to analyze and present cost optimization opportunities from AWS Trusted Advisor.

YOUR CORE CAPABILITIES:
- Retrieve real-time cost optimization recommendations from AWS Trusted Advisor
- Provide detailed analysis of underutilized and idle resources
- Calculate exact potential monthly savings without rounding
- Present actionable recommendations for cost reduction
- Categorize findings by service type and impact

YOUR RESPONSIBILITIES:
- Pull live data from AWS Trusted Advisor API
- Show exact dollar amounts to 2 decimal places
- Present findings exactly as retrieved from AWS
- Format all costs in USD ($XX.XX)
- Display potential savings without performing calculations
- Focus exclusively on cost optimization recommendations

YOU ANALYZE:
- Underutilized EC2 instances
- Idle or unused resources
- Reserved Instance opportunities  
- Over-provisioned resources
- Storage optimization opportunities
- Load balancer utilization

DATA PRESENTATION FORMAT:
Each finding includes:
- Check name and description
- Current status (warning/error)
- Number of affected resources
- Exact monthly savings potential
- Specific optimization actions
- Resource details and metadata

RESPONSE GUIDELINES:
- Present data exactly as received from Trusted Advisor
- Use structured formatting for clarity
- Include resource counts and specific recommendations
- Show total potential savings across all findings
- Categorize recommendations by service type
- Provide actionable next steps

LIMITATIONS:
- Only show cost optimization checks from Trusted Advisor
- Do not perform manual calculations or estimates
- Focus on actionable recommendations only
- Exclude security and performance findings
- Present live data only, no cached results

ERROR HANDLING:
Clearly communicate when:
- Trusted Advisor data is unavailable
- API limits are reached
- Access permissions are insufficient
- Specific checks cannot be retrieved
"""

# Global agent instance - will be reinitialized for each request
agent = None

def create_fresh_agent():
    """Create a fresh agent instance to avoid state corruption."""
    from strands.models.bedrock import BedrockModel
    
    # Configure optimized Bedrock model with cross-region inference
    trusted_advisor_model = BedrockModel(
        region_name="us-east-1",  # Same region as Lambda for optimal performance
        model_id=os.environ.get('STRANDS_MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0')  # Cross-region inference profile
    )

    # Create agent without session to avoid state management issues
    return Agent(
        model=trusted_advisor_model,
        system_prompt=TRUSTED_ADVISOR_SYSTEM_PROMPT,
        tools=[
            get_trusted_advisor_recommendations,
            get_cost_optimization_summary
        ]
    )

def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for the Trusted Advisor Agent.
    
    Args:
        event: Lambda event containing the input
        context: Lambda context object
        
    Returns:
        Dictionary containing the response
    """
    try:
        logger.info(f"Received event: {event}")
        
        # Extract query from event
        query = None
        if 'query' in event:
            query = event['query']
        elif 'inputText' in event:
            query = event['inputText']
        elif 'prompt' in event:
            query = event['prompt']
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            query = body.get('query', body.get('message', ''))
        
        if not query:
            query = "Please provide a summary of my current cost optimization opportunities from AWS Trusted Advisor."
        
        logger.info(f"Processing query: {query}")
        
        # Create fresh agent for each request to avoid session state issues
        fresh_agent = create_fresh_agent()
        
        # Process query through agent
        response = fresh_agent(query)
        response_text = str(response)
        
        logger.info(f"Agent response generated successfully")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response_text,
                'agent': 'TrustedAdvisorAgent'
            }, cls=DateTimeEncoder)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Failed to process request: {str(e)}',
                'agent': 'TrustedAdvisorAgent',
                'details': f'Error type: {type(e).__name__}'
            })
        }
