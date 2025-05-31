from aws_cdk import (
    Stack,
    aws_appsync as appsync,
    aws_cognito as cognito,
    aws_lambda as lambda_,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class FinOpsAppSyncStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self, "FinOpsUserPool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerify(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            removal_policy=RemovalPolicy.DESTROY,  # For development only
        )

        # Create User Pool Client
        user_pool_client = user_pool.add_client(
            "FinOpsAppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["http://localhost:3000/"],
                logout_urls=["http://localhost:3000/"],
            ),
        )

        # Create AppSync API
        api = appsync.GraphqlApi(
            self, "FinOpsAPI",
            name="finops-agent-api",
            schema=appsync.SchemaFile.from_asset("infrastructure/schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.USER_POOL,
                    user_pool_config=appsync.UserPoolConfig(
                        user_pool=user_pool,
                    ),
                ),
                additional_authorization_modes=[
                    appsync.AuthorizationMode(
                        authorization_type=appsync.AuthorizationType.IAM,
                    ),
                ],
            ),
            xray_enabled=True,
        )

        # Import Lambda functions (assuming they are already created)
        supervisor_lambda = lambda_.Function.from_function_name(
            self, "SupervisorLambda", "finops-supervisor-agent"
        )
        
        cost_analysis_lambda = lambda_.Function.from_function_name(
            self, "CostAnalysisLambda", "finops-cost-analysis-agent"
        )
        
        optimization_lambda = lambda_.Function.from_function_name(
            self, "OptimizationLambda", "finops-optimization-agent"
        )

        # Grant AppSync permissions to invoke Lambda functions
        supervisor_lambda.grant_invoke(api)
        cost_analysis_lambda.grant_invoke(api)
        optimization_lambda.grant_invoke(api)

        # Create Lambda data sources
        supervisor_ds = api.add_lambda_data_source(
            "SupervisorDataSource",
            supervisor_lambda,
        )
        
        cost_analysis_ds = api.add_lambda_data_source(
            "CostAnalysisDataSource",
            cost_analysis_lambda,
        )
        
        optimization_ds = api.add_lambda_data_source(
            "OptimizationDataSource",
            optimization_lambda,
        )

        # Create resolvers for Query operations
        supervisor_ds.create_resolver(
            "GetAgentStatusResolver",
            type_name="Query",
            field_name="getAgentStatus",
        )
        
        cost_analysis_ds.create_resolver(
            "GetCostAnalysisResolver",
            type_name="Query",
            field_name="getCostAnalysis",
        )
        
        optimization_ds.create_resolver(
            "GetOptimizationRecommendationsResolver",
            type_name="Query",
            field_name="getOptimizationRecommendations",
        )
        
        supervisor_ds.create_resolver(
            "GetConversationHistoryResolver",
            type_name="Query",
            field_name="getConversationHistory",
        )

        # Create resolvers for Mutation operations
        supervisor_ds.create_resolver(
            "SendMessageResolver",
            type_name="Mutation",
            field_name="sendMessage",
        )
        
        cost_analysis_ds.create_resolver(
            "RequestCostAnalysisResolver",
            type_name="Mutation",
            field_name="requestCostAnalysis",
        )
        
        optimization_ds.create_resolver(
            "ApplyOptimizationResolver",
            type_name="Mutation",
            field_name="applyOptimization",
        )

        # Output the API URL and other important information
        CfnOutput(
            self, "GraphQLAPIURL",
            value=api.graphql_url,
            description="URL of the GraphQL API",
        )
        
        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="ID of the Cognito User Pool",
        )
        
        CfnOutput(
            self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="ID of the Cognito User Pool Client",
        )
