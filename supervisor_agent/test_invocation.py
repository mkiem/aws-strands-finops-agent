#!/usr/bin/env python3
"""Test script to verify Lambda-to-Lambda invocation"""

import json
import boto3
import time

def test_trusted_advisor_invocation():
    """Test invoking the trusted advisor agent directly"""
    lambda_client = boto3.client('lambda')
    
    try:
        print("Testing trusted advisor agent invocation...")
        start_time = time.time()
        
        response = lambda_client.invoke(
            FunctionName='trusted-advisor-agent-trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({"query": "What are my cost optimization opportunities?"})
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Invocation completed in {duration:.2f} seconds")
        print(f"Status Code: {response['StatusCode']}")
        
        if 'FunctionError' in response:
            print(f"Function Error: {response['FunctionError']}")
        
        # Read payload
        payload_data = response['Payload'].read()
        print(f"Payload size: {len(payload_data)} bytes")
        
        # Parse response
        payload_str = payload_data.decode()
        response_data = json.loads(payload_str)
        
        print("Response structure:")
        print(json.dumps(response_data, indent=2)[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_trusted_advisor_invocation()
