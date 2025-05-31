import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import handlers
from agents.supervisor.appsync_handler import handler as supervisor_handler
from agents.cost_analysis.appsync_handler import handler as cost_analysis_handler
from agents.optimization.appsync_handler import handler as optimization_handler

class TestAppSyncIntegration(unittest.TestCase):
    """Test AppSync integration with Lambda handlers"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock AWS clients
        self.appsync_patcher = patch('boto3.client')
        self.mock_boto3_client = self.appsync_patcher.start()
        
        # Mock context
        self.context = MagicMock()
        self.context.function_name = 'test-function'
        self.context.aws_request_id = '12345'
        
    def tearDown(self):
        """Clean up after tests"""
        self.appsync_patcher.stop()
    
    def test_supervisor_get_agent_status(self):
        """Test supervisor handler for getAgentStatus query"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Query',
                'fieldName': 'getAgentStatus'
            },
            'arguments': {
                'agentId': 'supervisor-agent'
            }
        }
        
        # Call handler
        response = supervisor_handler(event, self.context)
        
        # Verify response
        self.assertIn('agentId', response)
        self.assertEqual(response['agentId'], 'supervisor-agent')
        self.assertIn('status', response)
    
    def test_supervisor_send_message(self):
        """Test supervisor handler for sendMessage mutation"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Mutation',
                'fieldName': 'sendMessage'
            },
            'arguments': {
                'input': {
                    'content': 'How can I optimize my AWS costs?',
                    'userId': 'user-123'
                }
            }
        }
        
        # Call handler
        response = supervisor_handler(event, self.context)
        
        # Verify response
        self.assertIn('id', response)
        self.assertIn('content', response)
        self.assertEqual(response['content'], 'How can I optimize my AWS costs?')
        self.assertEqual(response['sender'], 'USER')
    
    def test_cost_analysis_get_cost_analysis(self):
        """Test cost analysis handler for getCostAnalysis query"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Query',
                'fieldName': 'getCostAnalysis'
            },
            'arguments': {
                'timeRange': {
                    'startDate': '2025-05-01T00:00:00Z',
                    'endDate': '2025-05-31T00:00:00Z'
                }
            }
        }
        
        # Call handler
        response = cost_analysis_handler(event, self.context)
        
        # Verify response
        self.assertIn('id', response)
        self.assertIn('status', response)
        self.assertIn('totalCost', response)
        self.assertIn('costByService', response)
    
    def test_cost_analysis_request_cost_analysis(self):
        """Test cost analysis handler for requestCostAnalysis mutation"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Mutation',
                'fieldName': 'requestCostAnalysis'
            },
            'arguments': {
                'input': {
                    'timeRange': {
                        'startDate': '2025-05-01T00:00:00Z',
                        'endDate': '2025-05-31T00:00:00Z'
                    },
                    'granularity': 'DAILY'
                }
            }
        }
        
        # Call handler
        response = cost_analysis_handler(event, self.context)
        
        # Verify response
        self.assertIn('id', response)
        self.assertEqual(response['status'], 'REQUESTED')
        self.assertIn('timeRange', response)
    
    def test_optimization_get_recommendations(self):
        """Test optimization handler for getOptimizationRecommendations query"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Query',
                'fieldName': 'getOptimizationRecommendations'
            },
            'arguments': {}
        }
        
        # Call handler
        response = optimization_handler(event, self.context)
        
        # Verify response
        self.assertTrue(isinstance(response, list))
        self.assertTrue(len(response) > 0)
        self.assertIn('id', response[0])
        self.assertIn('title', response[0])
        self.assertIn('estimatedSavings', response[0])
    
    def test_optimization_apply_optimization(self):
        """Test optimization handler for applyOptimization mutation"""
        # Create test event
        event = {
            'info': {
                'parentTypeName': 'Mutation',
                'fieldName': 'applyOptimization'
            },
            'arguments': {
                'recommendationId': 'rec-1'
            }
        }
        
        # Call handler
        response = optimization_handler(event, self.context)
        
        # Verify response
        self.assertIn('recommendationId', response)
        self.assertEqual(response['recommendationId'], 'rec-1')
        self.assertIn('status', response)
        self.assertIn('message', response)

if __name__ == '__main__':
    unittest.main()
