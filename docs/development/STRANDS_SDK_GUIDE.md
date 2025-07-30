# Strands SDK Complete Guide for LLMs

*Generated from https://strandsagents.com/ on 2025-06-10*

## Quick Reference

### Installation
```bash
pip install strands-agents
```

### Basic Agent Creation
```python
from strands import Agent

# Create an agent with default settings
agent = Agent()

# Ask the agent a question
response = agent("Tell me about agentic AI")
```

## Core Concepts

### 1. Agent Fundamentals

**Agent Class**: The main entry point for creating agents
- Lightweight and production-ready
- Supports multiple model providers
- Built-in observability and tracing
- Customizable agent loop

**Key Features**:
- Model provider agnostic (Bedrock, OpenAI, Anthropic, etc.)
- Streaming and non-streaming support
- Multi-agent capabilities
- Built-in safety and security features

### 2. Model Providers

#### Amazon Bedrock (Default)
```python
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    region_name="us-west-2",
    model_id="anthropic.claude-3-7-sonnet-20241022-v1:0"
)
agent = Agent(model=model)
```

**Configuration**:
- Requires AWS credentials (boto3)
- Default region: us-west-2
- Default model: Claude 3.7 Sonnet
- Supports guardrails integration
- Tool calling capabilities

#### OpenAI
```python
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    model="gpt-4",
    api_key="your-api-key"
)
agent = Agent(model=model)
```

#### Anthropic
```python
from strands.models.anthropic import AnthropicModel

model = AnthropicModel(
    model="claude-3-sonnet-20240229",
    api_key="your-api-key"
)
agent = Agent(model=model)
```

#### Other Providers
- **LiteLLM**: Universal LLM proxy
- **Ollama**: Local model serving
- **LlamaAPI**: Llama model access
- **Custom Providers**: Extensible architecture

### 3. Tools and Capabilities

#### Built-in Tools
Strands provides powerful built-in tools for common tasks:

```python
from strands import Agent
from strands.tools import FileOperations, WebSearch

agent = Agent(
    tools=[FileOperations(), WebSearch()]
)
```

#### Python Tools
```python
def custom_tool(query: str) -> str:
    """Custom tool implementation"""
    return f"Processed: {query}"

agent = Agent(tools=[custom_tool])
```

#### Model Context Protocol (MCP) Tools
```python
from strands.tools.mcp import MCPTool

mcp_tool = MCPTool(server_url="your-mcp-server")
agent = Agent(tools=[mcp_tool])
```

### 4. Agent Loop and Execution

#### Basic Agent Loop
The agent follows a standard loop:
1. Receive user input
2. Process with LLM
3. Execute tools if needed
4. Return response

#### Streaming Support
```python
# Async streaming
async for chunk in agent.stream("Your question"):
    print(chunk, end="")

# Callback handlers
def on_chunk(chunk):
    print(chunk, end="")

agent("Your question", callback=on_chunk)
```

### 5. Sessions and State Management

#### Session Management
```python
from strands import Agent, Session

session = Session()
agent = Agent(session=session)

# Maintains conversation history
agent("Hello")
agent("What did I just say?")  # Agent remembers context
```

#### State Persistence
```python
# Save session state
session.save("session.json")

# Load session state
session = Session.load("session.json")
agent = Agent(session=session)
```

### 6. Multi-Agent Systems

#### Agents as Tools
```python
from strands import Agent

# Create specialized agents
research_agent = Agent(name="researcher")
writer_agent = Agent(name="writer")

# Use agents as tools
supervisor = Agent(
    tools=[research_agent, writer_agent]
)
```

#### Agent Workflows
```python
from strands.workflows import Workflow

workflow = Workflow([
    ("research", research_agent),
    ("write", writer_agent),
    ("review", review_agent)
])

result = workflow.run("Create a report on AI trends")
```

### 7. Context Management

#### System Prompts
```python
agent = Agent(
    system_prompt="You are a helpful financial analyst specializing in FinOps."
)
```

#### Context Windows
- Automatic context window management
- Overflow detection and handling
- Message truncation strategies

### 8. Observability and Monitoring

#### Built-in Observability
```python
from strands.observability import enable_tracing

enable_tracing()
agent = Agent()  # Automatically traced
```

#### Metrics Collection
- Request/response times
- Token usage
- Error rates
- Tool execution metrics

#### Logging
```python
import logging
from strands.logging import configure_logging

configure_logging(level=logging.INFO)
```

### 9. Safety and Security

#### Guardrails (Bedrock)
```python
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    guardrail_identifier="your-guardrail-id",
    guardrail_version="1"
)
```

#### Prompt Engineering Best Practices
- Input validation
- Output filtering
- Content moderation
- Rate limiting

#### Responsible AI
- Bias detection
- Fairness monitoring
- Transparency features

### 10. Deployment Options

#### AWS Lambda
```python
# lambda_handler.py
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

#### AWS Fargate
```dockerfile
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install strands-agents
CMD ["python", "agent.py"]
```

#### Amazon EKS
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strands-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: strands-agent
  template:
    metadata:
      labels:
        app: strands-agent
    spec:
      containers:
      - name: agent
        image: your-registry/strands-agent:latest
        ports:
        - containerPort: 8000
```

#### Amazon EC2
```bash
# Install dependencies
pip install strands-agents

# Run agent server
python agent_server.py
```

### 11. Production Considerations

#### Performance Optimization
- Connection pooling
- Request batching
- Caching strategies
- Load balancing

#### Scaling Patterns
- Horizontal scaling
- Auto-scaling groups
- Container orchestration
- Serverless deployment

#### Monitoring and Alerting
- CloudWatch integration
- Custom metrics
- Error tracking
- Performance monitoring

## Common Patterns for FinOps Agents

### Cost Analysis Agent
```python
from strands import Agent
from strands.tools import AWSCostExplorer

cost_agent = Agent(
    system_prompt="You are a FinOps specialist focused on AWS cost optimization.",
    tools=[AWSCostExplorer()],
    model=BedrockModel(region_name="us-east-1")
)

response = cost_agent("Analyze our monthly AWS spend trends")
```

### Multi-Service Integration
```python
# Supervisor agent that coordinates multiple specialized agents
supervisor = Agent(
    name="FinOps Supervisor",
    tools=[cost_forecast_agent, trusted_advisor_agent],
    system_prompt="Coordinate cost analysis and optimization recommendations."
)
```

### Streaming Responses for UI
```python
async def stream_response(query):
    async for chunk in agent.stream(query):
        yield f"data: {chunk}\n\n"
```

## Best Practices

1. **Model Selection**: Choose appropriate models for your use case
2. **Tool Design**: Keep tools focused and reusable
3. **Error Handling**: Implement robust error handling
4. **Security**: Always validate inputs and outputs
5. **Monitoring**: Enable comprehensive observability
6. **Testing**: Test agents thoroughly before production
7. **Documentation**: Document your agent's capabilities and limitations

## Troubleshooting

### Common Issues
- **Authentication**: Ensure proper credentials for model providers
- **Rate Limits**: Implement backoff strategies
- **Context Limits**: Monitor token usage
- **Tool Errors**: Handle tool execution failures gracefully

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = Agent(debug=True)
```

This guide provides comprehensive coverage of the Strands SDK for building production-ready agents, with specific focus on FinOps use cases.
