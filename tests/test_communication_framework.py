"""
Unit tests for the Agent Communication Framework.
"""

import unittest
import json
import os
import sys
import time
from unittest.mock import patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import communication framework components
from agents.common.communication import (
    Message, MessageType, MessageStatus,
    ConversationContext, MessageRouter, AgentRegistry
)

class TestMessage(unittest.TestCase):
    """Test the Message class"""
    
    def test_message_creation(self):
        """Test creating a message"""
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "What was my AWS cost last month?"},
            sender_id="user-123",
            recipient_id="supervisor-agent"
        )
        
        self.assertEqual(message.message_type, MessageType.QUERY)
        self.assertEqual(message.content["query"], "What was my AWS cost last month?")
        self.assertEqual(message.sender_id, "user-123")
        self.assertEqual(message.recipient_id, "supervisor-agent")
        self.assertEqual(message.status, MessageStatus.CREATED)
    
    def test_message_serialization(self):
        """Test serializing and deserializing a message"""
        original_message = Message(
            message_type=MessageType.QUERY,
            content={"query": "What was my AWS cost last month?"},
            sender_id="user-123",
            recipient_id="supervisor-agent"
        )
        
        # Convert to dict and back
        message_dict = original_message.to_dict()
        deserialized_message = Message.from_dict(message_dict)
        
        self.assertEqual(deserialized_message.message_type, original_message.message_type)
        self.assertEqual(deserialized_message.content, original_message.content)
        self.assertEqual(deserialized_message.sender_id, original_message.sender_id)
        self.assertEqual(deserialized_message.recipient_id, original_message.recipient_id)
        self.assertEqual(deserialized_message.message_id, original_message.message_id)
        
        # Convert to JSON and back
        json_str = original_message.to_json()
        deserialized_message = Message.from_json(json_str)
        
        self.assertEqual(deserialized_message.message_type, original_message.message_type)
        self.assertEqual(deserialized_message.content, original_message.content)
    
    def test_create_response(self):
        """Test creating a response message"""
        original_message = Message(
            message_type=MessageType.QUERY,
            content={"query": "What was my AWS cost last month?"},
            sender_id="user-123",
            recipient_id="supervisor-agent"
        )
        
        response = original_message.create_response(
            content={"result": "Your AWS cost last month was $1,234.56"}
        )
        
        self.assertEqual(response.message_type, MessageType.RESULT)
        self.assertEqual(response.content["result"], "Your AWS cost last month was $1,234.56")
        self.assertEqual(response.sender_id, "supervisor-agent")
        self.assertEqual(response.recipient_id, "user-123")
        self.assertEqual(response.conversation_id, original_message.conversation_id)
        self.assertEqual(response.parent_id, original_message.message_id)
    
    def test_create_error_response(self):
        """Test creating an error response message"""
        original_message = Message(
            message_type=MessageType.QUERY,
            content={"query": "What was my AWS cost last month?"},
            sender_id="user-123",
            recipient_id="supervisor-agent"
        )
        
        error_response = original_message.create_error_response(
            error_message="Failed to retrieve cost data",
            error_code="DATA_RETRIEVAL_ERROR"
        )
        
        self.assertEqual(error_response.message_type, MessageType.ERROR)
        self.assertEqual(error_response.content["error_message"], "Failed to retrieve cost data")
        self.assertEqual(error_response.content["error_code"], "DATA_RETRIEVAL_ERROR")
        self.assertEqual(error_response.sender_id, "supervisor-agent")
        self.assertEqual(error_response.recipient_id, "user-123")
    
    def test_update_status(self):
        """Test updating message status"""
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "What was my AWS cost last month?"}
        )
        
        message.update_status(MessageStatus.SENT)
        self.assertEqual(message.status, MessageStatus.SENT)
        
        message.update_status(MessageStatus.DELIVERED)
        self.assertEqual(message.status, MessageStatus.DELIVERED)
        
        # Check status history in metadata
        self.assertIn("status_history", message.metadata)
        self.assertEqual(len(message.metadata["status_history"]), 2)
        self.assertEqual(message.metadata["status_history"][0]["status"], "sent")
        self.assertEqual(message.metadata["status_history"][1]["status"], "delivered")

class TestConversationContext(unittest.TestCase):
    """Test the ConversationContext class"""
    
    def test_context_creation(self):
        """Test creating a conversation context"""
        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456"
        )
        
        self.assertEqual(context.conversation_id, "conv-123")
        self.assertEqual(context.user_id, "user-456")
        self.assertEqual(len(context.messages), 0)
        self.assertEqual(len(context.parameters), 0)
    
    def test_add_message(self):
        """Test adding messages to the context"""
        context = ConversationContext(conversation_id="conv-123")
        
        context.add_message("user", "What was my AWS cost last month?")
        context.add_message("assistant", "Your AWS cost last month was $1,234.56")
        
        self.assertEqual(len(context.messages), 2)
        self.assertEqual(context.messages[0]["role"], "user")
        self.assertEqual(context.messages[0]["content"], "What was my AWS cost last month?")
        self.assertEqual(context.messages[1]["role"], "assistant")
        self.assertEqual(context.messages[1]["content"], "Your AWS cost last month was $1,234.56")
    
    def test_update_parameters(self):
        """Test updating parameters in the context"""
        context = ConversationContext(conversation_id="conv-123")
        
        context.update_parameters({
            "time_range": {
                "start_date": "2025-04-01",
                "end_date": "2025-04-30"
            }
        })
        
        self.assertIn("time_range", context.parameters)
        self.assertEqual(context.parameters["time_range"]["start_date"], "2025-04-01")
        
        # Update with additional parameters
        context.update_parameters({
            "services": ["EC2", "S3"]
        })
        
        self.assertIn("services", context.parameters)
        self.assertEqual(len(context.parameters["services"]), 2)
        
        # Update existing parameter
        context.update_parameters({
            "time_range": {
                "start_date": "2025-04-01",
                "end_date": "2025-05-01",
                "period_type": "month"
            }
        })
        
        self.assertEqual(context.parameters["time_range"]["end_date"], "2025-05-01")
        self.assertEqual(context.parameters["time_range"]["period_type"], "month")
    
    def test_agent_state(self):
        """Test agent state management in the context"""
        context = ConversationContext(conversation_id="conv-123")
        
        # Get initial state (should be empty)
        state = context.get_agent_state("supervisor-agent")
        self.assertEqual(len(state), 0)
        
        # Update state
        context.update_agent_state("supervisor-agent", {
            "last_query_time": time.time(),
            "query_count": 1
        })
        
        # Get updated state
        state = context.get_agent_state("supervisor-agent")
        self.assertIn("last_query_time", state)
        self.assertEqual(state["query_count"], 1)
        
        # Update state again
        context.update_agent_state("supervisor-agent", {
            "query_count": 2,
            "last_response_time": time.time()
        })
        
        # Get updated state
        state = context.get_agent_state("supervisor-agent")
        self.assertEqual(state["query_count"], 2)
        self.assertIn("last_response_time", state)
        self.assertIn("last_query_time", state)  # Original field should still be there
    
    def test_context_serialization(self):
        """Test serializing and deserializing a context"""
        original_context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456"
        )
        
        original_context.add_message("user", "What was my AWS cost last month?")
        original_context.update_parameters({"time_range": {"period_type": "month"}})
        original_context.update_agent_state("supervisor-agent", {"query_count": 1})
        
        # Convert to dict and back
        context_dict = original_context.to_dict()
        deserialized_context = ConversationContext.from_dict(context_dict)
        
        self.assertEqual(deserialized_context.conversation_id, original_context.conversation_id)
        self.assertEqual(deserialized_context.user_id, original_context.user_id)
        self.assertEqual(len(deserialized_context.messages), 1)
        self.assertEqual(deserialized_context.parameters["time_range"]["period_type"], "month")
        self.assertEqual(deserialized_context.agent_state["supervisor-agent"]["query_count"], 1)
        
        # Convert to JSON and back
        json_str = original_context.to_json()
        deserialized_context = ConversationContext.from_json(json_str)
        
        self.assertEqual(deserialized_context.conversation_id, original_context.conversation_id)
        self.assertEqual(len(deserialized_context.messages), 1)
    
    def test_prune_history(self):
        """Test pruning conversation history"""
        context = ConversationContext(conversation_id="conv-123")
        
        # Add 60 messages
        for i in range(60):
            context.add_message("user" if i % 2 == 0 else "assistant", f"Message {i}")
        
        self.assertEqual(len(context.messages), 60)
        
        # Prune to 50 messages
        context.prune_history(max_messages=50)
        
        self.assertEqual(len(context.messages), 50)
        self.assertEqual(context.messages[0]["content"], "Message 10")
        self.assertEqual(context.messages[-1]["content"], "Message 59")
        self.assertIn("pruned_at", context.metadata)
        self.assertEqual(context.metadata["pruned_count"], 1)

class TestAgentRegistry(unittest.TestCase):
    """Test the AgentRegistry class"""
    
    def setUp(self):
        """Set up the test environment"""
        self.mock_dynamodb_client = MagicMock()
        self.registry = AgentRegistry(dynamodb_client=self.mock_dynamodb_client)
    
    def test_register_agent(self):
        """Test registering an agent"""
        self.registry.register_agent(
            agent_id="supervisor-agent",
            agent_info={
                "name": "Supervisor Agent",
                "type": "lambda",
                "function_name": "finops-supervisor-agent",
                "capabilities": ["orchestration", "nlp"]
            }
        )
        
        # Check local registry
        self.assertIn("supervisor-agent", self.registry.local_registry)
        self.assertEqual(self.registry.local_registry["supervisor-agent"]["name"], "Supervisor Agent")
        self.assertEqual(len(self.registry.local_registry["supervisor-agent"]["capabilities"]), 2)
        
        # DynamoDB should not be called (disabled by default)
        self.mock_dynamodb_client.put_item.assert_not_called()
    
    def test_get_agent(self):
        """Test getting agent information"""
        # Register an agent
        self.registry.register_agent(
            agent_id="cost-analysis-agent",
            agent_info={
                "name": "Cost Analysis Agent",
                "type": "lambda",
                "function_name": "finops-cost-analysis-agent"
            }
        )
        
        # Get the agent
        agent_info = self.registry.get_agent("cost-analysis-agent")
        
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info["name"], "Cost Analysis Agent")
        self.assertEqual(agent_info["type"], "lambda")
        
        # Get a non-existent agent
        agent_info = self.registry.get_agent("non-existent-agent")
        self.assertIsNone(agent_info)
    
    def test_update_agent(self):
        """Test updating agent information"""
        # Register an agent
        self.registry.register_agent(
            agent_id="optimization-agent",
            agent_info={
                "name": "Optimization Agent",
                "type": "lambda",
                "function_name": "finops-optimization-agent",
                "status": "idle"
            }
        )
        
        # Update the agent
        result = self.registry.update_agent(
            agent_id="optimization-agent",
            updates={
                "status": "busy",
                "current_task": "analyzing EC2 instances"
            }
        )
        
        self.assertTrue(result)
        
        # Check updated information
        agent_info = self.registry.get_agent("optimization-agent")
        self.assertEqual(agent_info["status"], "busy")
        self.assertEqual(agent_info["current_task"], "analyzing EC2 instances")
        self.assertEqual(agent_info["name"], "Optimization Agent")  # Original field should still be there
    
    def test_find_agents_by_capability(self):
        """Test finding agents by capability"""
        # Register agents with different capabilities
        self.registry.register_agent(
            agent_id="agent1",
            agent_info={
                "name": "Agent 1",
                "capabilities": ["cost_analysis", "forecasting"]
            }
        )
        
        self.registry.register_agent(
            agent_id="agent2",
            agent_info={
                "name": "Agent 2",
                "capabilities": ["optimization", "resource_utilization"]
            }
        )
        
        self.registry.register_agent(
            agent_id="agent3",
            agent_info={
                "name": "Agent 3",
                "capabilities": ["cost_analysis", "comparison"]
            }
        )
        
        # Find agents with cost_analysis capability
        cost_analysis_agents = self.registry.find_agents_by_capability("cost_analysis")
        self.assertEqual(len(cost_analysis_agents), 2)
        self.assertIn("agent1", cost_analysis_agents)
        self.assertIn("agent3", cost_analysis_agents)
        
        # Find agents with optimization capability
        optimization_agents = self.registry.find_agents_by_capability("optimization")
        self.assertEqual(len(optimization_agents), 1)
        self.assertIn("agent2", optimization_agents)
        
        # Find agents with non-existent capability
        no_agents = self.registry.find_agents_by_capability("non_existent")
        self.assertEqual(len(no_agents), 0)
    
    def test_deregister_agent(self):
        """Test deregistering an agent"""
        # Register an agent
        self.registry.register_agent(
            agent_id="temp-agent",
            agent_info={
                "name": "Temporary Agent"
            }
        )
        
        # Verify it's registered
        self.assertIn("temp-agent", self.registry.local_registry)
        
        # Deregister the agent
        result = self.registry.deregister_agent("temp-agent")
        
        self.assertTrue(result)
        self.assertNotIn("temp-agent", self.registry.local_registry)
        
        # Try to deregister a non-existent agent
        result = self.registry.deregister_agent("non-existent-agent")
        self.assertFalse(result)

class TestMessageRouter(unittest.TestCase):
    """Test the MessageRouter class"""
    
    def setUp(self):
        """Set up the test environment"""
        self.mock_lambda_client = MagicMock()
        self.mock_dynamodb_client = MagicMock()
        
        # Set up mock Lambda response
        mock_response = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_response['Payload'].read.return_value = json.dumps({
            'message': {
                'message_type': 'result',
                'content': {'result': 'Success'},
                'message_id': '123',
                'conversation_id': 'conv-123',
                'sender_id': 'agent1',
                'recipient_id': 'agent2',
                'status': 'completed'
            }
        }).encode('utf-8')
        self.mock_lambda_client.invoke.return_value = mock_response
        
        # Set up agent registry
        self.agent_registry = AgentRegistry(dynamodb_client=self.mock_dynamodb_client)
        self.agent_registry.register_agent(
            agent_id="agent1",
            agent_info={
                "name": "Agent 1",
                "type": "lambda",
                "function_name": "lambda-function-1"
            }
        )
        
        # Set up message router
        self.router = MessageRouter(
            agent_registry=self.agent_registry,
            lambda_client=self.mock_lambda_client,
            dynamodb_client=self.mock_dynamodb_client
        )
    
    def test_send_message_to_lambda(self):
        """Test sending a message to a Lambda function"""
        # Create a message
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "Test query"},
            sender_id="sender",
            recipient_id="agent1"
        )
        
        # Send the message
        response = self.router.send_message(message, synchronous=True)
        
        # Check that Lambda was invoked
        self.mock_lambda_client.invoke.assert_called_once()
        args, kwargs = self.mock_lambda_client.invoke.call_args
        self.assertEqual(kwargs['FunctionName'], 'lambda-function-1')
        self.assertEqual(kwargs['InvocationType'], 'RequestResponse')
        
        # Check response
        self.assertIsNotNone(response)
        self.assertEqual(response.message_type, MessageType.RESULT)
        self.assertEqual(response.content['result'], 'Success')
    
    def test_local_handler(self):
        """Test handling a message locally"""
        # Register a local handler
        def test_handler(message):
            return message.create_response(
                content={"handled": True, "original_content": message.content}
            )
        
        self.router.register_handler(MessageType.QUERY, test_handler)
        
        # Create a message with no recipient (will be handled locally)
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "Local test"},
            sender_id="sender"
        )
        
        # Send the message
        response = self.router.send_message(message)
        
        # Check response
        self.assertIsNotNone(response)
        self.assertEqual(response.content['handled'], True)
        self.assertEqual(response.content['original_content']['query'], "Local test")
        
        # Lambda should not be invoked
        self.mock_lambda_client.invoke.assert_not_called()
    
    def test_error_handling(self):
        """Test error handling in the router"""
        # Set up Lambda to raise an exception
        self.mock_lambda_client.invoke.side_effect = Exception("Test error")
        
        # Create a message
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "Test query"},
            sender_id="sender",
            recipient_id="agent1"
        )
        
        # Send the message
        response = self.router.send_message(message, synchronous=True)
        
        # Check response is an error
        self.assertIsNotNone(response)
        self.assertEqual(response.message_type, MessageType.ERROR)
        self.assertIn("Test error", response.content['error_message'])
        
        # Check message status
        self.assertEqual(message.status, MessageStatus.FAILED)
    
    def test_message_history(self):
        """Test message history tracking"""
        # Create and send a message
        message = Message(
            message_type=MessageType.QUERY,
            content={"query": "Test query"},
            sender_id="sender",
            recipient_id="agent1",
            conversation_id="conv-123"
        )
        
        self.router.send_message(message, synchronous=True)
        
        # Check message history
        self.assertIn(message.message_id, self.router.message_history)
        
        # Get message by ID
        stored_message = self.router.get_message(message.message_id)
        self.assertEqual(stored_message.content['query'], "Test query")
        
        # Get conversation messages
        conv_messages = self.router.get_conversation_messages("conv-123")
        self.assertEqual(len(conv_messages), 2)  # Original message and response
        
        # Clear history
        count = self.router.clear_history()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.router.message_history), 0)

if __name__ == '__main__':
    unittest.main()
