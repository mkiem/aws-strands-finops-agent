#!/usr/bin/env python3

"""
AWS CDK application for deploying the FinOps Agent Lambda functions.
"""

import os
from aws_cdk import (
    App,
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct

class FinOpsAgentStack(Stack):
    """CDK Stack for the FinOps Agent Lambda functions."""
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Define common Lambda configuration
        lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "timeout": Duration.minutes(15),
            "memory_size": 256,
            "log_retention": logs.RetentionDays.ONE_WEEK,
            "environment": {
                "MODEL_ID": "amazon.titan-text-express-v1",
                "TEMPERATURE": "0.7",
                "MAX_TOKENS": "4096",
            }
        }
        
        # Create IAM role for the Lambda functions with basic execution permissions
        lambda_role = iam.Role(
            self, "FinOpsAgentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add permissions for Cost Explorer
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ce:GetCostAndUsage",
                    "ce:GetCostForecast"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for Trusted Advisor
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "support:DescribeTrustedAdvisorChecks",
                    "support:DescribeTrustedAdvisorCheckResult"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for EC2 and CloudWatch (for resource utilization)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:DescribeInstances",
                    "cloudwatch:GetMetricStatistics"
                ],
                resources=["*"]
            )
        )
        
        # Create Lambda function for the Supervisor Agent
        supervisor_lambda = lambda_.Function(
            self, "SupervisorAgentFunction",
            function_name="finops-supervisor-agent",
            description="FinOps Supervisor Agent Lambda function",
            code=lambda_.Code.from_asset("../src/lambda/supervisor_agent"),
            handler="handler.handler",
            role=lambda_role,
            **lambda_config
        )
        
        # Create Lambda function for the Cost Analysis Agent
        cost_analysis_lambda = lambda_.Function(
            self, "CostAnalysisAgentFunction",
            function_name="finops-cost-analysis-agent",
            description="FinOps Cost Analysis Agent Lambda function",
            code=lambda_.Code.from_asset("../src/lambda/cost_analysis_agent"),
            handler="handler.handler",
            role=lambda_role,
            **lambda_config
        )
        
        # Create Lambda function for the Cost Optimization Agent
        cost_optimization_lambda = lambda_.Function(
            self, "CostOptimizationAgentFunction",
            function_name="finops-cost-optimization-agent",
            description="FinOps Cost Optimization Agent Lambda function",
            code=lambda_.Code.from_asset("../src/lambda/cost_optimization_agent"),
            handler="handler.handler",
            role=lambda_role,
            **lambda_config
        )
        
        # Configure provisioned concurrency for reduced cold starts
        supervisor_version = supervisor_lambda.current_version
        supervisor_alias = lambda_.Alias(
            self, "SupervisorAgentAlias",
            alias_name="production",
            version=supervisor_version,
            provisioned_concurrent_executions=1
        )
        
        cost_analysis_version = cost_analysis_lambda.current_version
        cost_analysis_alias = lambda_.Alias(
            self, "CostAnalysisAgentAlias",
            alias_name="production",
            version=cost_analysis_version,
            provisioned_concurrent_executions=1
        )
        
        cost_optimization_version = cost_optimization_lambda.current_version
        cost_optimization_alias = lambda_.Alias(
            self, "CostOptimizationAgentAlias",
            alias_name="production",
            version=cost_optimization_version,
            provisioned_concurrent_executions=1
        )
        
        # Output the Lambda function ARNs
        CfnOutput(
            self, "SupervisorAgentFunctionArn",
            value=supervisor_lambda.function_arn,
            description="ARN of the Supervisor Agent Lambda function"
        )
        
        CfnOutput(
            self, "CostAnalysisAgentFunctionArn",
            value=cost_analysis_lambda.function_arn,
            description="ARN of the Cost Analysis Agent Lambda function"
        )
        
        CfnOutput(
            self, "CostOptimizationAgentFunctionArn",
            value=cost_optimization_lambda.function_arn,
            description="ARN of the Cost Optimization Agent Lambda function"
        )
        
        # Output the Lambda function aliases
        CfnOutput(
            self, "SupervisorAgentAliasArn",
            value=supervisor_alias.alias_arn,
            description="ARN of the Supervisor Agent Lambda alias"
        )
        
        CfnOutput(
            self, "CostAnalysisAgentAliasArn",
            value=cost_analysis_alias.alias_arn,
            description="ARN of the Cost Analysis Agent Lambda alias"
        )
        
        CfnOutput(
            self, "CostOptimizationAgentAliasArn",
            value=cost_optimization_alias.alias_arn,
            description="ARN of the Cost Optimization Agent Lambda alias"
        )


app = App()
FinOpsAgentStack(app, "FinOpsAgentStack")
app.synth()
