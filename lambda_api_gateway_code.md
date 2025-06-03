# Lambda Function Code for API Gateway Integration

This document provides the code pattern for a Lambda function that works correctly with API Gateway proxy integration.

## Basic Structure

```python
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    AWS Lambda handler function for the FinOps Agent
    """
    try:
        logger.info(f"Received event: {event}")
        
        # Extract query from the event
        query = None
        
        # Check if the event is from API Gateway
        if 'body' in event:
            try:
                # If body is a string (from API Gateway), parse it
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
                
                query = body.get('query', '')
            except Exception as e:
                logger.error(f"Error parsing request body: {str(e)}")
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f"Invalid request format: {str(e)}"})
                }
        # Direct Lambda invocation
        elif 'query' in event:
            query = event['query']
        
        if not query:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'No query provided in the request'})
            }
        
        # Process the query
        logger.info(f"Processing query: {query}")
        response = process_query(query)
        logger.info(f"Response: {response}")
        
        # Return the response in the format expected by API Gateway
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'query': query,
                'response': str(response)
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def get_cors_headers():
    """
    Return CORS headers for API Gateway responses
    """
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    }

def process_query(query):
    """
    Process the query using your agent or other logic
    """
    # Replace this with your actual query processing logic
    return f"Processed query: {query}"
```

## FinOps Agent Implementation

For the FinOps Agent, the `process_query` function would initialize the Strands agent and process the query:

```python
def process_query(query):
    """
    Process the query using the Strands agent
    """
    # Initialize the agent with tools
    finops_agent = Agent(
        system_prompt=FINOPS_SYSTEM_PROMPT,
        tools=[calculator, current_time, get_aws_cost_summary],
    )
    
    # Get the response from the agent
    response = finops_agent(query)
    
    return str(response)
```

## Error Handling

The code includes error handling for:

1. Invalid request format
2. Missing query
3. Processing errors

Each error returns an appropriate HTTP status code and error message.

## CORS Headers

The `get_cors_headers` function returns the CORS headers needed for browser-based applications:

```python
def get_cors_headers():
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    }
```

## Logging

The code includes logging to help with debugging:

```python
logger.info(f"Received event: {event}")
logger.info(f"Processing query: {query}")
logger.info(f"Response: {response}")
logger.error(f"Error parsing request body: {str(e)}")
logger.error(f"Error processing request: {str(e)}")
```

## Testing

You can test the Lambda function directly:

```bash
aws lambda invoke \
  --function-name finops-agent \
  --payload '{"query": "What is the current AWS spend?"}' \
  response.json
```

Or through API Gateway:

```bash
curl -X POST \
  https://YOUR_API_ID.execute-api.REGION.amazonaws.com/prod/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is the current AWS spend?"}'
```
