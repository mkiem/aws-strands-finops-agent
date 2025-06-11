"""
Trusted Advisor Tools for Strands Agent
Provides cost optimization recommendations from AWS Trusted Advisor
"""

import boto3
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from strands import tool
from strands.types.content import ContentBlock

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize clients - Support API is only available in us-east-1
# Try the new TrustedAdvisor service first, fall back to Support API
try:
    # New TrustedAdvisor service (available in multiple regions)
    trusted_advisor_client = boto3.client('trustedadvisor', region_name='us-east-1')
    use_new_api = True
except Exception:
    # Fall back to Support API (requires Business/Enterprise support plan)
    trusted_advisor_client = boto3.client('support', region_name='us-east-1')
    use_new_api = False


@tool
def get_trusted_advisor_recommendations() -> ContentBlock:
    """
    Get all cost optimization recommendations from AWS Trusted Advisor.
    
    This tool retrieves comprehensive cost optimization findings including:
    - Underutilized resources
    - Idle or unused resources  
    - Reserved Instance opportunities
    - Over-provisioned resources
    
    Returns:
        ContentBlock with structured cost optimization data including total potential 
        monthly savings, detailed recommendations, and affected resources.
    """
    try:
        findings = []
        
        if use_new_api:
            # Use new TrustedAdvisor API
            input_params = {
                'maxResults': 200,
                'pillar': 'cost_optimizing',
                'status': 'warning'
            }
            
            has_more_results = True
            next_token = None
            
            while has_more_results:
                if next_token:
                    input_params['nextToken'] = next_token
                    
                command = trusted_advisor_client.list_recommendations(**input_params)
                response = command
                
                logger.info(f"Retrieved {len(response.get('recommendationSummaries', []))} recommendations")
                
                for recommendation in response.get('recommendationSummaries', []):
                    try:
                        # Get detailed recommendation data
                        detail_response = trusted_advisor_client.get_recommendation(
                            recommendationIdentifier=recommendation['arn']
                        )
                        
                        cost_aggregates = recommendation.get('pillarSpecificAggregates', {}).get('costOptimizing', {})
                        resource_aggregates = recommendation.get('resourcesAggregates', {})
                        
                        finding = {
                            'recommendationIdentifier': recommendation['arn'],
                            'checkName': recommendation['name'],
                            'checkId': recommendation['id'],
                            'status': recommendation['status'],
                            'description': detail_response.get('recommendation', {}).get('description', ''),
                            'recommendedAction': (detail_response.get('recommendation', {})
                                               .get('recommendedActions', [{}])[0]
                                               .get('description', '')),
                            'resourceCount': (resource_aggregates.get('errorCount', 0) + 
                                           resource_aggregates.get('warningCount', 0)),
                            'estimatedMonthlySavings': cost_aggregates.get('estimatedMonthlySavings', 0),
                            'resources': [
                                {
                                    'resourceId': resource.get('resourceId', ''),
                                    'region': resource.get('metadata', {}).get('region', ''),
                                    'status': resource.get('status', ''),
                                    'metadata': resource.get('metadata', {})
                                }
                                for resource in detail_response.get('recommendation', {}).get('resources', [])[:10]
                            ]
                        }
                        
                        findings.append(finding)
                        
                    except Exception as e:
                        logger.error(f"Error processing recommendation {recommendation['name']}: {str(e)}")
                        continue
                
                next_token = response.get('nextToken')
                has_more_results = bool(next_token)
                
        else:
            # Fall back to Support API
            checks_response = trusted_advisor_client.describe_trusted_advisor_checks(language='en')
            cost_optimization_checks = [
                check for check in checks_response['checks'] 
                if 'cost' in check['category'].lower() or 'optimization' in check['category'].lower()
            ]
            
            logger.info(f"Found {len(cost_optimization_checks)} cost optimization checks")
            
            for check in cost_optimization_checks:
                try:
                    check_result = trusted_advisor_client.describe_trusted_advisor_check_result(
                        checkId=check['id'],
                        language='en'
                    )
                    
                    result = check_result['result']
                    
                    if result['status'] in ['warning', 'error']:
                        estimated_savings = 0.0
                        resource_count = len(result.get('flaggedResources', []))
                        
                        # Extract savings from metadata
                        if 'metadata' in result and result['metadata']:
                            for metadata in result['metadata']:
                                if any(keyword in metadata.lower() for keyword in ['cost', 'saving', 'dollar', '$']):
                                    numbers = re.findall(r'\$?(\d+(?:\.\d{2})?)', metadata)
                                    if numbers:
                                        try:
                                            estimated_savings = max(estimated_savings, float(numbers[0]))
                                        except ValueError:
                                            pass
                        
                        resources = []
                        for resource in result.get('flaggedResources', [])[:10]:
                            resource_data = {
                                'resourceId': resource.get('resourceId', ''),
                                'region': resource.get('region', ''),
                                'status': resource.get('status', 'warning'),
                                'metadata': {}
                            }
                            
                            if 'metadata' in resource and resource['metadata']:
                                for i, metadata_value in enumerate(resource['metadata']):
                                    if i < len(check.get('metadata', [])):
                                        field_name = check['metadata'][i]
                                        resource_data['metadata'][field_name] = metadata_value
                            
                            resources.append(resource_data)
                        
                        finding = {
                            'recommendationIdentifier': check['id'],
                            'checkName': check['name'],
                            'checkId': check['id'],
                            'status': result['status'],
                            'description': check['description'],
                            'recommendedAction': f"Review and address the {resource_count} flagged resources for {check['name']}",
                            'resourceCount': resource_count,
                            'estimatedMonthlySavings': round(estimated_savings, 2),
                            'resources': resources
                        }
                        
                        findings.append(finding)
                        logger.info(f"Processed check: {check['name']} with {resource_count} resources")
                        
                except Exception as e:
                    logger.error(f"Error processing check {check['name']}: {str(e)}")
                    continue
        
        # Sort findings by estimated savings (highest first)
        findings.sort(key=lambda x: x.get('estimatedMonthlySavings', 0), reverse=True)
        
        # Calculate total savings
        total_savings = sum(finding.get('estimatedMonthlySavings', 0) for finding in findings)
        
        # Prepare the response
        response_data = {
            'summary': {
                'totalFindings': len(findings),
                'totalPotentialSavings': round(total_savings, 2),
                'lastUpdated': datetime.now().isoformat().replace('T', ' ')[:19]
            },
            'findings': findings
        }
        
        logger.info(f"Retrieved {len(findings)} cost optimization recommendations with total potential savings of ${total_savings:.2f}")
        
        return ContentBlock(
            type="text",
            text=json.dumps(response_data, indent=2)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving Trusted Advisor recommendations: {str(e)}")
        error_response = {
            'error': f"Failed to retrieve Trusted Advisor recommendations: {str(e)}",
            'summary': {
                'totalFindings': 0,
                'totalPotentialSavings': 0.0,
                'lastUpdated': datetime.now().isoformat().replace('T', ' ')[:19]
            },
            'findings': []
        }
        
        return ContentBlock(
            type="text", 
            text=json.dumps(error_response, indent=2)
        )


@tool
def get_recommendation_details(recommendation_identifier: str) -> ContentBlock:
    """
    Get detailed information for a specific Trusted Advisor recommendation.
    
    Args:
        recommendation_identifier: The check ID or ARN of the recommendation
        
    Returns:
        ContentBlock with detailed recommendation data including all affected resources
        and specific optimization actions.
    """
    try:
        # Get detailed check result
        check_result = trusted_advisor_client.describe_trusted_advisor_check_result(
            checkId=recommendation_identifier,
            language='en'
        )
        
        result = check_result['result']
        
        # Get check metadata for context
        checks_response = trusted_advisor_client.describe_trusted_advisor_checks(language='en')
        check_info = next((check for check in checks_response['checks'] if check['id'] == recommendation_identifier), None)
        
        if not check_info:
            raise ValueError(f"Check with ID {recommendation_identifier} not found")
        
        # Process all flagged resources
        resources = []
        for resource in result.get('flaggedResources', []):
            resource_data = {
                'resourceId': resource.get('resourceId', ''),
                'region': resource.get('region', ''),
                'status': resource.get('status', 'warning'),
                'metadata': {}
            }
            
            # Map metadata fields to meaningful names
            if 'metadata' in resource and resource['metadata']:
                for i, metadata_value in enumerate(resource['metadata']):
                    if i < len(check_info.get('metadata', [])):
                        field_name = check_info['metadata'][i]
                        resource_data['metadata'][field_name] = metadata_value
            
            resources.append(resource_data)
        
        response_data = {
            'recommendationIdentifier': recommendation_identifier,
            'checkName': check_info['name'],
            'description': check_info['description'],
            'category': check_info['category'],
            'status': result['status'],
            'resourceCount': len(resources),
            'resources': resources,
            'lastUpdated': datetime.now().isoformat().replace('T', ' ')[:19]
        }
        
        logger.info(f"Retrieved details for recommendation {recommendation_identifier} with {len(resources)} resources")
        
        return ContentBlock(
            type="text",
            text=json.dumps(response_data, indent=2)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recommendation details for {recommendation_identifier}: {str(e)}")
        error_response = {
            'error': f"Failed to retrieve recommendation details: {str(e)}",
            'recommendationIdentifier': recommendation_identifier
        }
        
        return ContentBlock(
            type="text",
            text=json.dumps(error_response, indent=2)
        )


@tool
def get_cost_optimization_summary() -> ContentBlock:
    """
    Get a high-level summary of cost optimization opportunities from Trusted Advisor.
    
    Returns:
        ContentBlock with aggregated cost optimization metrics including total potential
        savings, number of recommendations by category, and top optimization opportunities.
    """
    try:
        # Get all recommendations first
        recommendations_result = get_trusted_advisor_recommendations()
        recommendations_data = json.loads(recommendations_result.text)
        
        if 'error' in recommendations_data:
            return recommendations_result
        
        findings = recommendations_data.get('findings', [])
        
        # Categorize findings by type
        categories = {}
        top_savings_opportunities = []
        
        for finding in findings:
            check_name = finding.get('checkName', 'Unknown')
            savings = finding.get('estimatedMonthlySavings', 0)
            
            # Categorize by keywords in check name
            category = 'Other'
            if any(keyword in check_name.lower() for keyword in ['ec2', 'instance', 'compute']):
                category = 'Compute'
            elif any(keyword in check_name.lower() for keyword in ['rds', 'database']):
                category = 'Database'
            elif any(keyword in check_name.lower() for keyword in ['ebs', 'volume', 'storage']):
                category = 'Storage'
            elif any(keyword in check_name.lower() for keyword in ['reserved', 'ri']):
                category = 'Reserved Instances'
            elif any(keyword in check_name.lower() for keyword in ['load balancer', 'elb']):
                category = 'Load Balancing'
            
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'totalSavings': 0.0,
                    'checks': []
                }
            
            categories[category]['count'] += 1
            categories[category]['totalSavings'] += savings
            categories[category]['checks'].append({
                'name': check_name,
                'savings': savings,
                'resourceCount': finding.get('resourceCount', 0)
            })
            
            # Track top savings opportunities
            if savings > 0:
                top_savings_opportunities.append({
                    'checkName': check_name,
                    'estimatedMonthlySavings': savings,
                    'resourceCount': finding.get('resourceCount', 0)
                })
        
        # Sort categories by total savings
        sorted_categories = sorted(categories.items(), key=lambda x: x[1]['totalSavings'], reverse=True)
        
        # Sort top opportunities by savings
        top_savings_opportunities.sort(key=lambda x: x['estimatedMonthlySavings'], reverse=True)
        
        summary_data = {
            'overview': {
                'totalRecommendations': len(findings),
                'totalPotentialMonthlySavings': recommendations_data['summary']['totalPotentialSavings'],
                'categoriesWithFindings': len(categories),
                'lastUpdated': datetime.now().isoformat().replace('T', ' ')[:19]
            },
            'categorySummary': {
                category: {
                    'recommendationCount': data['count'],
                    'totalPotentialSavings': round(data['totalSavings'], 2),
                    'topChecks': sorted(data['checks'], key=lambda x: x['savings'], reverse=True)[:3]
                }
                for category, data in sorted_categories
            },
            'topSavingsOpportunities': top_savings_opportunities[:5]
        }
        
        logger.info(f"Generated cost optimization summary with {len(findings)} recommendations across {len(categories)} categories")
        
        return ContentBlock(
            type="text",
            text=json.dumps(summary_data, indent=2)
        )
        
    except Exception as e:
        logger.error(f"Error generating cost optimization summary: {str(e)}")
        error_response = {
            'error': f"Failed to generate cost optimization summary: {str(e)}",
            'overview': {
                'totalRecommendations': 0,
                'totalPotentialMonthlySavings': 0.0,
                'categoriesWithFindings': 0,
                'lastUpdated': datetime.now().isoformat().replace('T', ' ')[:19]
            }
        }
        
        return ContentBlock(
            type="text",
            text=json.dumps(error_response, indent=2)
        )
