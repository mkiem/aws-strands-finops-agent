"""
Tests for the Lambda handlers.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the Lambda handlers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the Lambda handlers
from lambda.supervisor_agent.handler import handler as supervisor_handler
from lambda.cost_analysis_agent.handler import handler as cost_analysis_handler
from lambda.cost_optimization_agent.handler import handler as cost_optimization_handler


class TestSupervisorHandler(unittest.TestCase):
    """Tests for the Supervisor Agent Lambda handler."""
    
    @patch('lambda.supervisor_agent.handler.finops_agent')
    def test_handler_valid_request(self, mock_agent):
        """Test that the handler processes a valid request correctly."""
        # Mock the agent response
        mock_agent.return_value = "This is a test response"
        
        # Create a test event
        event = {
            'body': json.dumps({
                'message': 'What is my AWS cost?',
                'session_id': 'test-session'
            })
        }
        
        # Call the handler
        response = supervisor_handler(event, None)
        
        # Check the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "This is a test response")
        self.assertEqual(body['session_id'], "test-session")
        
        # Verify the agent was called with the correct message
        mock_agent.assert_called_once_with('What is my AWS cost?')
    
    def test_handler_missing_message(self):
        """Test that the handler returns an error for a missing message."""
        # Create a test event with no message
        event = {
            'body': json.dumps({
                'session_id': 'test-session'
            })
        }
        
        # Call the handler
        response = supervisor_handler(event, None)
        
        # Check the response
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)


class TestCostAnalysisHandler(unittest.TestCase):
    """Tests for the Cost Analysis Agent Lambda handler."""
    
    @patch('lambda.cost_analysis_agent.handler.cost_analysis_agent')
    def test_handler_valid_request(self, mock_agent):
        """Test that the handler processes a valid request correctly."""
        # Mock the agent response
        mock_agent.return_value = "Cost analysis response"
        
        # Create a test event
        event = {
            'body': json.dumps({
                'message': 'What was my cost last month?',
                'session_id': 'test-session'
            })
        }
        
        # Call the handler
        response = cost_analysis_handler(event, None)
        
        # Check the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "Cost analysis response")
        self.assertEqual(body['session_id'], "test-session")
        
        # Verify the agent was called with the correct message
        mock_agent.assert_called_once_with('What was my cost last month?')


class TestCostOptimizationHandler(unittest.TestCase):
    """Tests for the Cost Optimization Agent Lambda handler."""
    
    @patch('lambda.cost_optimization_agent.handler.cost_optimization_agent')
    def test_handler_valid_request(self, mock_agent):
        """Test that the handler processes a valid request correctly."""
        # Mock the agent response
        mock_agent.return_value = "Cost optimization response"
        
        # Create a test event
        event = {
            'body': json.dumps({
                'message': 'How can I optimize my costs?',
                'session_id': 'test-session'
            })
        }
        
        # Call the handler
        response = cost_optimization_handler(event, None)
        
        # Check the response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "Cost optimization response")
        self.assertEqual(body['session_id'], "test-session")
        
        # Verify the agent was called with the correct message
        mock_agent.assert_called_once_with('How can I optimize my costs?')


if __name__ == '__main__':
    unittest.main()
