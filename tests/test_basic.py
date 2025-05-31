"""
Basic tests for the FinOps Agent.
"""

import pytest
from src.config import get_config


def test_config_loading():
    """Test that configuration can be loaded."""
    agent_config = get_config("agent")
    assert isinstance(agent_config, dict)
    assert "model_id" in agent_config
    assert "region" in agent_config


def test_aws_region_config():
    """Test that AWS region is properly configured."""
    agent_config = get_config("agent")
    lambda_config = get_config("lambda")
    appsync_config = get_config("appsync")
    
    assert agent_config["region"] == lambda_config["region"]
    assert agent_config["region"] == appsync_config["region"]
