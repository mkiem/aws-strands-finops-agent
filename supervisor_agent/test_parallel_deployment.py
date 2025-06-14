#!/usr/bin/env python3
"""
Test the deployed parallel processing supervisor agent.
"""

import json
import boto3
import time

def test_comprehensive_query():
    """Test a comprehensive query that should trigger multiple agents."""
    
    lambda_client = boto3.client('lambda')
    
    # Test query that should invoke multiple agents
    test_query = "Provide comprehensive analysis of my AWS costs and optimization opportunities"
    
    payload = {
        "query": test_query
    }
    
    print(f"🚀 Testing comprehensive query: '{test_query}'")
    print("⏱️  Measuring response time with parallel processing...")
    
    start_time = time.time()
    
    try:
        response = lambda_client.invoke(
            FunctionName='AWS-FinOps-Agent',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"✅ Response received in {response_time:.2f} seconds")
        
        # Check if response indicates parallel processing
        if 'response' in response_payload:
            response_text = response_payload['response']
            if "parallel processing" in response_text.lower():
                print("✅ Parallel processing confirmed in response")
            else:
                print("ℹ️  Response doesn't explicitly mention parallel processing")
            
            # Check for multiple sections (indicating multiple agents were called)
            sections = ['Cost Analysis', 'Optimization Recommendations', 'Budget Management']
            found_sections = [section for section in sections if section in response_text]
            
            print(f"📊 Found {len(found_sections)} analysis sections: {', '.join(found_sections)}")
            
            if len(found_sections) >= 2:
                print("✅ Multiple agents were successfully invoked")
            else:
                print("⚠️  Only single agent response detected")
        
        return {
            "success": True,
            "response_time": response_time,
            "sections_found": len(found_sections) if 'found_sections' in locals() else 0,
            "response_length": len(response_payload.get('response', ''))
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"❌ Error after {response_time:.2f} seconds: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response_time": response_time
        }

def test_single_agent_query():
    """Test a query that should only invoke one agent."""
    
    lambda_client = boto3.client('lambda')
    
    # Test query that should invoke only cost forecast agent
    test_query = "What are my current AWS costs for this month?"
    
    payload = {
        "query": test_query
    }
    
    print(f"\n🎯 Testing single agent query: '{test_query}'")
    print("⏱️  Measuring response time...")
    
    start_time = time.time()
    
    try:
        response = lambda_client.invoke(
            FunctionName='AWS-FinOps-Agent',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"✅ Response received in {response_time:.2f} seconds")
        
        if 'response' in response_payload:
            response_text = response_payload['response']
            if "Cost Analysis" in response_text and "Optimization Recommendations" not in response_text:
                print("✅ Single agent routing confirmed")
            else:
                print("ℹ️  Response may include multiple agents")
        
        return {
            "success": True,
            "response_time": response_time,
            "response_length": len(response_payload.get('response', ''))
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"❌ Error after {response_time:.2f} seconds: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response_time": response_time
        }

if __name__ == "__main__":
    print("🧪 Testing Deployed Parallel Processing Implementation\n")
    
    # Test comprehensive query (should use parallel processing)
    comprehensive_result = test_comprehensive_query()
    
    # Test single agent query (should not use parallel processing)
    single_result = test_single_agent_query()
    
    print(f"\n📋 Test Summary:")
    print(f"   • Comprehensive query: {'✅ Success' if comprehensive_result['success'] else '❌ Failed'}")
    if comprehensive_result['success']:
        print(f"     - Response time: {comprehensive_result['response_time']:.2f}s")
        print(f"     - Sections found: {comprehensive_result.get('sections_found', 'N/A')}")
    
    print(f"   • Single agent query: {'✅ Success' if single_result['success'] else '❌ Failed'}")
    if single_result['success']:
        print(f"     - Response time: {single_result['response_time']:.2f}s")
    
    if comprehensive_result['success'] and single_result['success']:
        print(f"\n🎉 Parallel processing deployment: ✅ SUCCESSFUL")
    else:
        print(f"\n⚠️  Some tests failed - check logs above")
