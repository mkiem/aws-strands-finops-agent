"""
Configuration settings for the FinOps Agent.
"""

import os
from typing import Dict, Any

# AWS Region
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Agent Configuration
AGENT_CONFIG = {
    "model_id": "amazon.titan-text-express-v1",  # Default model
    "region": AWS_REGION,
    "temperature": 0.7,
    "max_tokens": 4096,
}

# AppSync Configuration
APPSYNC_CONFIG = {
    "region": AWS_REGION,
    "api_url": os.environ.get("APPSYNC_API_URL", ""),
}

# Lambda Configuration
LAMBDA_CONFIG = {
    "region": AWS_REGION,
    "function_timeout": 900,  # 15 minutes (maximum for Lambda)
    "memory_size": 256,  # MB
    "provisioned_concurrency": 1,
}

# Cognito Configuration
COGNITO_CONFIG = {
    "region": AWS_REGION,
    "user_pool_id": os.environ.get("COGNITO_USER_POOL_ID", ""),
    "client_id": os.environ.get("COGNITO_CLIENT_ID", ""),
}

# Cost Explorer Configuration
COST_EXPLORER_CONFIG = {
    "region": AWS_REGION,
    "granularity": "DAILY",  # DAILY, MONTHLY, or HOURLY
}

# Trusted Advisor Configuration
TRUSTED_ADVISOR_CONFIG = {
    "region": AWS_REGION,
    "language": "en",
}

# MCP Server Configuration
MCP_SERVER_CONFIG = {
    "cost_analysis_server": {
        "port": 8080,
        "host": "localhost",
    },
    "cost_optimization_server": {
        "port": 8081,
        "host": "localhost",
    },
}

def get_config(config_name: str) -> Dict[str, Any]:
    """
    Get configuration by name.
    
    Args:
        config_name: Name of the configuration to retrieve
        
    Returns:
        Configuration dictionary
    """
    configs = {
        "agent": AGENT_CONFIG,
        "appsync": APPSYNC_CONFIG,
        "lambda": LAMBDA_CONFIG,
        "cognito": COGNITO_CONFIG,
        "cost_explorer": COST_EXPLORER_CONFIG,
        "trusted_advisor": TRUSTED_ADVISOR_CONFIG,
        "mcp_server": MCP_SERVER_CONFIG,
    }
    
    return configs.get(config_name, {})
