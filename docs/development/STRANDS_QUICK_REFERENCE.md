# Strands SDK Quick Reference

## Installation & Basic Setup
```bash
pip install strands-agents
```

```python
from strands import Agent

# Basic agent
agent = Agent()
response = agent("Your question here")
```

## Model Providers

### Amazon Bedrock (Default)
```python
from strands.models.bedrock import BedrockModel

agent = Agent(model=BedrockModel(
    region_name="us-east-1",
    model_id="anthropic.claude-3-7-sonnet-20241022-v1:0"
))
```

### OpenAI
```python
from strands.models.openai import OpenAIModel

agent = Agent(model=OpenAIModel(
    model="gpt-4",
    api_key="your-key"
))
```

### Anthropic
```python
from strands.models.anthropic import AnthropicModel

agent = Agent(model=AnthropicModel(
    model="claude-3-sonnet-20240229",
    api_key="your-key"
))
```

## Tools Integration

### Python Functions as Tools
```python
def analyze_costs(account_id: str) -> str:
    """Analyze AWS costs for account"""
    # Your implementation
    return "Cost analysis results"

agent = Agent(tools=[analyze_costs])
```

### Built-in Tools
```python
from strands.tools import FileOperations, WebSearch

agent = Agent(tools=[FileOperations(), WebSearch()])
```

## Sessions & State
```python
from strands import Session

session = Session()
agent = Agent(session=session)

# Maintains conversation context
agent("Hello")
agent("What did I say?")  # Remembers previous message
```

## Streaming
```python
# Async streaming
async for chunk in agent.stream("Your question"):
    print(chunk, end="")

# Callback streaming
def handle_chunk(chunk):
    print(chunk, end="")

agent("Your question", callback=handle_chunk)
```

## Multi-Agent Patterns

### Agents as Tools
```python
specialist_agent = Agent(name="specialist")
supervisor = Agent(tools=[specialist_agent])
```

### Agent Workflows
```python
from strands.workflows import Workflow

workflow = Workflow([
    ("analyze", cost_agent),
    ("optimize", advisor_agent)
])
```

## AWS Lambda Deployment
```python
from strands import Agent

agent = Agent()

def lambda_handler(event, context):
    query = event.get('query', '')
    response = agent(query)
    return {
        'statusCode': 200,
        'body': response
    }
```

## System Prompts
```python
agent = Agent(
    system_prompt="You are a FinOps expert specializing in AWS cost optimization."
)
```

## Error Handling
```python
try:
    response = agent("Your question")
except Exception as e:
    print(f"Agent error: {e}")
```

## Observability
```python
from strands.observability import enable_tracing

enable_tracing()
agent = Agent()  # Automatically traced
```

## Common FinOps Agent Pattern
```python
from strands import Agent
from strands.models.bedrock import BedrockModel

# Create specialized FinOps agent
finops_agent = Agent(
    model=BedrockModel(region_name="us-east-1"),
    system_prompt="You are a FinOps specialist focused on AWS cost optimization and analysis.",
    tools=[cost_analysis_tool, trusted_advisor_tool]
)

# Use in Lambda
def lambda_handler(event, context):
    query = event.get('query', '')
    response = finops_agent(query)
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'response': response})
    }
```
