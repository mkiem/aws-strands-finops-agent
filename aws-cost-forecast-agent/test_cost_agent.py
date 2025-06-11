#!/usr/bin/env python3
"""
Test script for AWS Cost Analysis and Forecasting Agent
"""

import json
import sys
import os

# Add the current directory to the path so we can import the lambda handler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_handler import handler

def test_agent():
    """Test the cost analysis agent with various queries"""
    
    test_queries = [
        "What were my AWS costs for last month?",
        "Show me my current month AWS spending",
        "What is my cost forecast for next month?",
        "What were my top expenses for Q1 2024?",
        "Show me EC2 costs for the last 6 months",
        "What are my savings plan recommendations?"
    ]
    
    print("🧪 Testing AWS Cost Analysis and Forecasting Agent")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {query}")
        print("-" * 40)
        
        # Create test event
        event = {
            'body': json.dumps({
                'query': query
            })
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = 'aws-cost-forecast-agent'
                self.memory_limit_in_mb = 256
                self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:aws-cost-forecast-agent'
        
        context = MockContext()
        
        try:
            # Call the handler
            response = handler(event, context)
            
            # Parse and display response
            if response['statusCode'] == 200:
                body = json.loads(response['body'])
                print("✅ Success!")
                
                if 'content_blocks' in body:
                    print("\n📄 Response Content:")
                    for block in body['content_blocks']:
                        print(block['text'])
                else:
                    print(f"📄 Response: {body}")
            else:
                print(f"❌ Error: {response['statusCode']}")
                print(f"📄 Response: {response['body']}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ['REGION'] = 'us-east-1'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    test_agent()
