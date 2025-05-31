"""
Unit tests for the FinOps Supervisor Agent.
"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agent and tools
from agents.supervisor.agent import FinOpsSupervisorAgent
from agents.supervisor.tools.intent_classifier import IntentClassifierTool
from agents.supervisor.tools.parameter_extractor import ParameterExtractorTool
from agents.supervisor.tools.agent_invoker import AgentInvokerTool
from agents.supervisor.tools.response_synthesizer import ResponseSynthesizerTool

class TestIntentClassifier(unittest.TestCase):
    """Test the Intent Classifier Tool"""
    
    def setUp(self):
        """Set up the test environment"""
        self.tool = IntentClassifierTool()
    
    def test_cost_analysis_intent(self):
        """Test classification of cost analysis intent"""
        message = "What was my AWS cost for last month?"
        result = self.tool._run(message)
        
        self.assertEqual(result['primary_intent'], 'COST_ANALYSIS')
        self.assertIn('COST_ANALYSIS', result['agents_to_invoke'])
    
    def test_cost_optimization_intent(self):
        """Test classification of cost optimization intent"""
        message = "How can I optimize my AWS costs?"
        result = self.tool._run(message)
        
        self.assertEqual(result['primary_intent'], 'COST_OPTIMIZATION')
        self.assertIn('COST_OPTIMIZATION', result['agents_to_invoke'])
    
    def test_multiple_intents(self):
        """Test classification of message with multiple intents"""
        message = "Show me my EC2 costs and suggest optimization opportunities"
        result = self.tool._run(message)
        
        # Either COST_ANALYSIS or COST_OPTIMIZATION could be primary
        # depending on the exact implementation
        self.assertIsNotNone(result['primary_intent'])
        self.assertIsNotNone(result['secondary_intent'])
        self.assertGreater(len(result['agents_to_invoke']), 1)

class TestParameterExtractor(unittest.TestCase):
    """Test the Parameter Extractor Tool"""
    
    def setUp(self):
        """Set up the test environment"""
        self.tool = ParameterExtractorTool()
    
    def test_time_range_extraction(self):
        """Test extraction of time range"""
        message = "What was my AWS cost for last month?"
        result = self.tool._run(message)
        
        self.assertIn('time_range', result)
        self.assertIn('start_date', result['time_range'])
        self.assertIn('end_date', result['time_range'])
        self.assertEqual(result['time_range']['period_type'], 'month')
    
    def test_service_extraction(self):
        """Test extraction of AWS services"""
        message = "Show me the cost of EC2 and S3 for last month"
        result = self.tool._run(message)
        
        self.assertIn('services', result)
        self.assertIn('EC2', result['services'])
        self.assertIn('S3', result['services'])
    
    def test_granularity_extraction(self):
        """Test extraction of time granularity"""
        message = "Show me daily costs for last month"
        result = self.tool._run(message)
        
        self.assertIn('granularity', result)
        self.assertEqual(result['granularity'], 'DAILY')

class TestAgentInvoker(unittest.TestCase):
    """Test the Agent Invoker Tool"""
    
    def setUp(self):
        """Set up the test environment"""
        self.mock_lambda_client = MagicMock()
        self.tool = AgentInvokerTool(
            cost_analysis_function='mock-cost-analysis',
            optimization_function='mock-optimization',
            lambda_client=self.mock_lambda_client
        )
        
        # Set up mock response for Lambda invocation
        mock_response = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_response['Payload'].read.return_value = json.dumps({
            'result': 'success'
        }).encode('utf-8')
        self.mock_lambda_client.invoke.return_value = mock_response
    
    def test_invoke_cost_analysis(self):
        """Test invocation of Cost Analysis Agent"""
        agents_to_invoke = ['COST_ANALYSIS']
        parameters = {'time_range': {'period_type': 'month'}}
        
        result = self.tool._run(agents_to_invoke, parameters)
        
        self.mock_lambda_client.invoke.assert_called_once()
        self.assertIn('cost_analysis', result)
    
    def test_invoke_both_agents(self):
        """Test invocation of both specialized agents"""
        agents_to_invoke = ['COST_ANALYSIS', 'COST_OPTIMIZATION']
        parameters = {'time_range': {'period_type': 'month'}}
        
        result = self.tool._run(agents_to_invoke, parameters)
        
        self.assertEqual(self.mock_lambda_client.invoke.call_count, 2)
        self.assertIn('cost_analysis', result)
        self.assertIn('cost_optimization', result)

class TestResponseSynthesizer(unittest.TestCase):
    """Test the Response Synthesizer Tool"""
    
    def setUp(self):
        """Set up the test environment"""
        self.tool = ResponseSynthesizerTool()
    
    def test_synthesize_cost_analysis(self):
        """Test synthesis of cost analysis response"""
        agent_responses = {
            'cost_analysis': {
                'summary': 'Your total AWS cost for last month was $1,234.56.',
                'details': {
                    'total_cost': 1234.56,
                    'cost_by_service': [
                        {'service_name': 'EC2', 'cost': 567.89, 'percentage': 46.0},
                        {'service_name': 'S3', 'cost': 123.45, 'percentage': 10.0}
                    ]
                }
            }
        }
        
        intent = {'primary_intent': 'COST_ANALYSIS'}
        parameters = {'time_range': {'period_type': 'month'}}
        
        result = self.tool._run(agent_responses, intent, parameters)
        
        self.assertIn('response', result)
        self.assertIn('Your total AWS cost', result['response'])
        self.assertIn('EC2', result['response'])
        self.assertIn('S3', result['response'])
    
    def test_synthesize_with_errors(self):
        """Test synthesis with error responses"""
        agent_responses = {
            'cost_analysis': {
                'error': 'Failed to retrieve cost data'
            }
        }
        
        intent = {'primary_intent': 'COST_ANALYSIS'}
        parameters = {'time_range': {'period_type': 'month'}}
        
        result = self.tool._run(agent_responses, intent, parameters)
        
        self.assertIn('response', result)
        self.assertIn('errors', result)
        self.assertEqual(len(result['errors']), 1)
        self.assertIn('Failed to retrieve cost data', result['errors'][0])

class TestFinOpsSupervisorAgent(unittest.TestCase):
    """Test the FinOps Supervisor Agent"""
    
    @patch('agents.supervisor.agent.Agent')
    def setUp(self, mock_agent_class):
        """Set up the test environment"""
        # Mock the Strands Agent
        self.mock_agent = MagicMock()
        mock_agent_class.return_value = self.mock_agent
        
        # Create the supervisor agent
        self.agent = FinOpsSupervisorAgent()
    
    def test_process_message(self):
        """Test processing a user message"""
        # Set up mock response from Strands Agent
        mock_response = MagicMock()
        mock_response.content = "This is a test response"
        mock_response.metadata = {}
        self.mock_agent.process_message.return_value = mock_response
        
        # Process a test message
        result = self.agent.process_message(
            user_message="What was my AWS cost last month?",
            conversation_id="test-conversation",
            user_id="test-user"
        )
        
        # Verify the result
        self.assertIn('message', result)
        self.assertEqual(result['message'], "This is a test response")
        self.assertEqual(result['conversation_id'], "test-conversation")
        self.assertIn('timestamp', result)
        
        # Verify conversation history was updated
        self.assertEqual(len(self.agent.conversation_history), 2)
        self.assertEqual(self.agent.conversation_history[0]['role'], 'user')
        self.assertEqual(self.agent.conversation_history[1]['role'], 'assistant')

if __name__ == '__main__':
    unittest.main()
