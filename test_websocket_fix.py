#!/usr/bin/env python3
"""
Test script to verify WebSocket background processor fix
"""
import json
import boto3
import uuid
import time

def test_websocket_background_processor():
    """Test the WebSocket background processor with a sample job."""
    
    # Create SQS client
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    # Get the processing queue URL
    queue_url = 'https://sqs.us-east-1.amazonaws.com/837882009522/finops-websocket-processing-queue'
    
    # Create a test job
    job_id = str(uuid.uuid4())
    connection_id = "test-connection-" + str(uuid.uuid4())[:8]
    
    test_message = {
        'jobId': job_id,
        'connectionId': connection_id,
        'userId': 'test-user',
        'username': 'test-user',
        'query': 'What cost optimization recommendations do you have?',
        'action': 'process_finops_query'
    }
    
    print(f"🧪 Testing WebSocket Background Processor Fix")
    print(f"📝 Job ID: {job_id}")
    print(f"🔗 Connection ID: {connection_id}")
    print(f"❓ Query: {test_message['query']}")
    print()
    
    try:
        # Send message to SQS queue
        print("📤 Sending test message to SQS queue...")
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(test_message),
            MessageAttributes={
                'jobType': {
                    'StringValue': 'finops_query',
                    'DataType': 'String'
                }
            }
        )
        
        print(f"✅ Message sent successfully!")
        print(f"📨 Message ID: {response['MessageId']}")
        print()
        
        # Check DynamoDB for job status updates
        print("🔍 Monitoring job status in DynamoDB...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        jobs_table = dynamodb.Table('finops-websocket-jobs')
        
        # Wait a bit for processing
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = jobs_table.get_item(Key={'jobId': job_id})
                if 'Item' in response:
                    job = response['Item']
                    status = job.get('status', 'unknown')
                    message = job.get('message', 'No message')
                    print(f"📊 Job Status: {status} - {message}")
                    
                    if status in ['completed', 'failed']:
                        break
                        
            except Exception as e:
                print(f"⚠️  Error checking job status: {e}")
            
            time.sleep(1)
            
        print()
        print("🎯 Test completed! Check CloudWatch logs for detailed processing information.")
        print(f"📋 Log Group: /aws/lambda/finops-websocket-background-processor")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_websocket_background_processor()
