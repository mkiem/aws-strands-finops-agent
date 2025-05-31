from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    Duration,
    CfnOutput,
)
from constructs import Construct

class FinOpsLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Lambda functions
        lambda_role = iam.Role(
            self, "FinOpsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
            ]
        )
        
        # Add permissions for Cost Explorer
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ce:GetCostAndUsage",
                    "ce:GetCostForecast",
                    "ce:GetDimensionValues",
                    "ce:GetReservationUtilization",
                    "ce:GetSavingsPlansPurchaseRecommendation",
                    "ce:GetRightsizingRecommendation"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for Trusted Advisor
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "trustedadvisor:DescribeCheckItems",
                    "trustedadvisor:DescribeCheckSummaries",
                    "trustedadvisor:DescribeChecks"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for EC2 (for resource analysis)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:DescribeInstances",
                    "ec2:DescribeVolumes",
                    "ec2:DescribeSnapshots",
                    "ec2:DescribeAddresses"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for CloudWatch (for metrics)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:GetMetricData",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for Lambda invocation (for agent communication)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=["*"]
            )
        )
        
        # Create Lambda layer for Strands SDK
        strands_layer = lambda_.LayerVersion(
            self, "StrandsLayer",
            code=lambda_.Code.from_asset("layers/strands"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Strands SDK and dependencies"
        )
        
        # Create Lambda function for Supervisor Agent
        supervisor_lambda = lambda_.Function(
            self, "SupervisorAgent",
            function_name="finops-supervisor-agent",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("agents"),
            handler="supervisor.lambda_handler.handler",
            role=lambda_role,
            timeout=Duration.minutes(15),
            memory_size=256,
            environment={
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
                "COST_ANALYSIS_FUNCTION": "finops-cost-analysis-agent",
                "OPTIMIZATION_FUNCTION": "finops-optimization-agent"
            },
            layers=[strands_layer]
        )
        
        # Create Lambda function for Cost Analysis Agent
        cost_analysis_lambda = lambda_.Function(
            self, "CostAnalysisAgent",
            function_name="finops-cost-analysis-agent",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("agents"),
            handler="cost_analysis.lambda_handler.handler",
            role=lambda_role,
            timeout=Duration.minutes(15),
            memory_size=256,
            environment={
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
            },
            layers=[strands_layer]
        )
        
        # Create Lambda function for Cost Optimization Agent
        optimization_lambda = lambda_.Function(
            self, "OptimizationAgent",
            function_name="finops-optimization-agent",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("agents"),
            handler="optimization.lambda_handler.handler",
            role=lambda_role,
            timeout=Duration.minutes(15),
            memory_size=256,
            environment={
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
            },
            layers=[strands_layer]
        )
        
        # Grant permissions for agents to invoke each other
        supervisor_lambda.grant_invoke(cost_analysis_lambda)
        supervisor_lambda.grant_invoke(optimization_lambda)
        cost_analysis_lambda.grant_invoke(supervisor_lambda)
        optimization_lambda.grant_invoke(supervisor_lambda)
        
        # Configure provisioned concurrency for better cold start performance
        supervisor_version = supervisor_lambda.current_version
        supervisor_alias = lambda_.Alias(
            self, "SupervisorAlias",
            alias_name="live",
            version=supervisor_version
        )
        
        supervisor_provisioned = supervisor_alias.node.default_child.add_property_override(
            "ProvisionedConcurrencyConfig", {
                "ProvisionedConcurrentExecutions": 1
            }
        )
        
        # Output the Lambda function ARNs
        CfnOutput(
            self, "SupervisorLambdaArn",
            value=supervisor_lambda.function_arn,
            description="ARN of the Supervisor Agent Lambda function"
        )
        
        CfnOutput(
            self, "CostAnalysisLambdaArn",
            value=cost_analysis_lambda.function_arn,
            description="ARN of the Cost Analysis Agent Lambda function"
        )
        
        CfnOutput(
            self, "OptimizationLambdaArn",
            value=optimization_lambda.function_arn,
            description="ARN of the Cost Optimization Agent Lambda function"
        )
