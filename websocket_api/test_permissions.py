#!/usr/bin/env python3
"""
Test script to verify Lambda invoke permissions
"""

import boto3
import json

def test_lambda_permissions():
    """Test if we can invoke the individual agents"""
    lambda_client = boto3.client('lambda')
    
    agents_to_test = [
        'aws-cost-forecast-agent',
        'trusted-advisor-agent-trusted-advisor-agent', 
        'budget-management-agent'
    ]
    
    test_query = "What are my current AWS costs?"
    
    print("🧪 Testing Lambda invoke permissions...")
    
    for agent in agents_to_test:
        try:
            print(f"\n📞 Testing {agent}...")
            
            # Test with a simple query
            response = lambda_client.invoke(
                FunctionName=agent,
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": test_query})
            )
            
            # Check if we got a response
            if response['StatusCode'] == 200:
                print(f"✅ {agent}: Permission granted and function responsive")
            else:
                print(f"⚠️  {agent}: Unexpected status code {response['StatusCode']}")
                
        except Exception as e:
            if "AccessDeniedException" in str(e):
                print(f"❌ {agent}: Access denied - {str(e)}")
            elif "ResourceNotFoundException" in str(e):
                print(f"⚠️  {agent}: Function not found - {str(e)}")
            else:
                print(f"❓ {agent}: Other error - {str(e)}")
    
    print(f"\n🎉 Permission test completed!")

if __name__ == "__main__":
    test_lambda_permissions()
