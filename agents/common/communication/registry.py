"""
Agent Registry module for agent communication.

This module provides a registry of available agents and their capabilities,
enabling dynamic agent discovery and selection.
"""

import json
import time
import logging
import boto3
from typing import Dict, Any, List, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Registry of available agents and their capabilities.
    
    This class maintains a registry of available agents, their capabilities,
    and status information, enabling dynamic agent discovery and selection.
    """
    
    def __init__(self, dynamodb_client=None, table_name: str = "FinOpsAgentRegistry"):
        """
        Initialize the Agent Registry.
        
        Args:
            dynamodb_client: Optional boto3 DynamoDB client (for testing)
            table_name: Name of the DynamoDB table for agent registry
        """
        self.dynamodb_client = dynamodb_client or boto3.client('dynamodb')
        self.table_name = table_name
        self.local_registry = {}
        self.use_dynamodb = False  # Flag to control whether to use DynamoDB
    
    def enable_dynamodb(self) -> None:
        """Enable DynamoDB for persistent registry storage."""
        self.use_dynamodb = True
    
    def disable_dynamodb(self) -> None:
        """Disable DynamoDB and use only local registry."""
        self.use_dynamodb = False
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent_id: ID of the agent
            agent_info: Information about the agent
        """
        # Add timestamp
        agent_info["registered_at"] = time.time()
        agent_info["last_heartbeat"] = time.time()
        
        # Store locally
        self.local_registry[agent_id] = agent_info
        logger.info(f"Registered agent: {agent_id}")
        
        # Store in DynamoDB if enabled
        if self.use_dynamodb:
            try:
                self.dynamodb_client.put_item(
                    TableName=self.table_name,
                    Item={
                        "agent_id": {"S": agent_id},
                        "agent_info": {"S": json.dumps(agent_info)},
                        "registered_at": {"N": str(agent_info["registered_at"])},
                        "last_heartbeat": {"N": str(agent_info["last_heartbeat"])}
                    }
                )
            except Exception as e:
                logger.error(f"Error storing agent in DynamoDB: {str(e)}", exc_info=True)
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an agent's information.
        
        Args:
            agent_id: ID of the agent
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.local_registry:
            logger.warning(f"Attempted to update unknown agent: {agent_id}")
            return False
        
        # Update locally
        self.local_registry[agent_id].update(updates)
        logger.info(f"Updated agent: {agent_id}")
        
        # Update in DynamoDB if enabled
        if self.use_dynamodb:
            try:
                # Get current agent info
                response = self.dynamodb_client.get_item(
                    TableName=self.table_name,
                    Key={"agent_id": {"S": agent_id}}
                )
                
                if "Item" in response:
                    agent_info = json.loads(response["Item"]["agent_info"]["S"])
                    agent_info.update(updates)
                    
                    self.dynamodb_client.update_item(
                        TableName=self.table_name,
                        Key={"agent_id": {"S": agent_id}},
                        UpdateExpression="SET agent_info = :info",
                        ExpressionAttributeValues={
                            ":info": {"S": json.dumps(agent_info)}
                        }
                    )
            except Exception as e:
                logger.error(f"Error updating agent in DynamoDB: {str(e)}", exc_info=True)
        
        return True
    
    def deregister_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.local_registry:
            logger.warning(f"Attempted to deregister unknown agent: {agent_id}")
            return False
        
        # Remove locally
        del self.local_registry[agent_id]
        logger.info(f"Deregistered agent: {agent_id}")
        
        # Remove from DynamoDB if enabled
        if self.use_dynamodb:
            try:
                self.dynamodb_client.delete_item(
                    TableName=self.table_name,
                    Key={"agent_id": {"S": agent_id}}
                )
            except Exception as e:
                logger.error(f"Error removing agent from DynamoDB: {str(e)}", exc_info=True)
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent information if found, None otherwise
        """
        # Check local registry first
        if agent_id in self.local_registry:
            return self.local_registry[agent_id]
        
        # Check DynamoDB if enabled and not in local registry
        if self.use_dynamodb:
            try:
                response = self.dynamodb_client.get_item(
                    TableName=self.table_name,
                    Key={"agent_id": {"S": agent_id}}
                )
                
                if "Item" in response:
                    agent_info = json.loads(response["Item"]["agent_info"]["S"])
                    # Cache in local registry
                    self.local_registry[agent_id] = agent_info
                    return agent_info
            except Exception as e:
                logger.error(f"Error retrieving agent from DynamoDB: {str(e)}", exc_info=True)
        
        return None
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered agents.
        
        Returns:
            Dictionary of agent IDs to agent information
        """
        # Start with local registry
        agents = self.local_registry.copy()
        
        # Add from DynamoDB if enabled
        if self.use_dynamodb:
            try:
                response = self.dynamodb_client.scan(TableName=self.table_name)
                
                for item in response.get("Items", []):
                    agent_id = item["agent_id"]["S"]
                    if agent_id not in agents:  # Don't overwrite local registry
                        agent_info = json.loads(item["agent_info"]["S"])
                        agents[agent_id] = agent_info
            except Exception as e:
                logger.error(f"Error listing agents from DynamoDB: {str(e)}", exc_info=True)
        
        return agents
    
    def find_agents_by_capability(self, capability: str) -> Dict[str, Dict[str, Any]]:
        """
        Find agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            Dictionary of agent IDs to agent information
        """
        matching_agents = {}
        
        for agent_id, agent_info in self.list_agents().items():
            capabilities = agent_info.get("capabilities", [])
            if capability in capabilities:
                matching_agents[agent_id] = agent_info
        
        return matching_agents
    
    def update_heartbeat(self, agent_id: str) -> bool:
        """
        Update the heartbeat timestamp for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_agent(agent_id, {"last_heartbeat": time.time()})
    
    def get_active_agents(self, max_age_seconds: float = 300) -> Dict[str, Dict[str, Any]]:
        """
        Get agents that have sent a heartbeat recently.
        
        Args:
            max_age_seconds: Maximum age of heartbeat
            
        Returns:
            Dictionary of active agent IDs to agent information
        """
        current_time = time.time()
        active_agents = {}
        
        for agent_id, agent_info in self.list_agents().items():
            last_heartbeat = agent_info.get("last_heartbeat", 0)
            if current_time - last_heartbeat <= max_age_seconds:
                active_agents[agent_id] = agent_info
        
        return active_agents
    
    def create_dynamodb_table(self) -> bool:
        """
        Create the DynamoDB table for agent registry.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.dynamodb_client.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {"AttributeName": "agent_id", "KeyType": "HASH"}
                ],
                AttributeDefinitions=[
                    {"AttributeName": "agent_id", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST"
            )
            logger.info(f"Created DynamoDB table: {self.table_name}")
            return True
        except self.dynamodb_client.exceptions.ResourceInUseException:
            logger.info(f"DynamoDB table already exists: {self.table_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating DynamoDB table: {str(e)}", exc_info=True)
            return False
