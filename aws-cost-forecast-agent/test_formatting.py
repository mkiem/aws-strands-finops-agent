#!/usr/bin/env python3
"""
Test script for the FinOps Agent response formatting.
This script simulates a request to the Lambda handler and displays the formatted response.
"""

import json
from lambda_handler import handler

def test_formatting():
    """
    Test the formatting of the FinOps Agent responses.
    """
    # Create a test event
    test_event = {
        'query': 'what is my total S3 spend for the month of June so far?'
    }
    
    # Call the lambda handler
    response = handler(test_event, None)
    
    # Print the formatted response
    print("Response Status Code:", response['statusCode'])
    print("\nFormatted Response Headers:")
    for header, value in response['headers'].items():
        print(f"  {header}: {value}")
    
    # Parse and pretty-print the response body
    response_body = json.loads(response['body'])
    print("\nQuery:", response_body['query'])
    print("\nResponse Content Blocks:")
    
    for i, block in enumerate(response_body['response']):
        print(f"\nBlock {i+1}:")
        print(json.dumps(block, indent=2))
    
    # Print how it would look when rendered
    print("\n\nRendered Response:")
    print("=" * 50)
    for block in response_body['response']:
        if 'text' in block:
            print(block['text'], end='')
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_formatting()
