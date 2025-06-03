What is the Model Context Protocol (MCP)?
Before we dive into the code, let's briefly talk about MCP:
The Model Context Protocol (MCP) is an open protocol standardizing how AI agents connect to external services, like databases, APIs, legacy systems, or third-party tools. Instead of building custom integrations for each service, MCP provides one standard interface for all external connections - somewhat like REST, but for AI agents.
Manual MCP implementation involves a lot of work: managing handshakes, connection state, message parsing, schema validation, etc.
With Strands, on the other hand, it's really just a few lines of code:

mcp_client = MCPClient(lambda: streamablehttp_client("http://example-service.com/mcp"))
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
The Strands SDK handles all the protocol complexity, letting you focus on agent functionality rather than integration details.
Building Our Quiz MCP Server
To demonstrate MCP integration, we'll create a simple quiz server in a new file, called quiz_mcp_server.py:

# Strands already includes MCP, no additional install required
from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP(
    name="Computer Science Quiz Service",
    host="0.0.0.0",
    port=8080
)

# Quiz database
QUIZ_CATALOG = {
    "python_basics": {
        "title": "Python Programming Fundamentals",
        "questions": [
            {
                "question": "What keyword is used to define a function in Python?",
                "options": ["func", "def", "function", "define"],
                "correct_answer": "def"
            },
            {
                "question": "Which of these creates a list in Python?",
                "options": ["(1, 2, 3)", "{1, 2, 3}", "[1, 2, 3]", "<1, 2, 3>"],
                "correct_answer": "[1, 2, 3]"
            }
        ]
    },
    "data_structures": {
        "title": "Data Structures Essentials",
        "questions": [
            {
                "question": "What is the time complexity of accessing an element in an array by index?",
                "options": ["O(n)", "O(log n)", "O(1)", "O(n²)"],
                "correct_answer": "O(1)"
            }
        ]
    }
}

@mcp.tool()
def list_quiz_topics() -> dict:
    """List all available quiz topics."""
    topics = {}
    for topic_id, quiz_data in QUIZ_CATALOG.items():
        topics[topic_id] = {
            "title": quiz_data["title"],
            "question_count": len(quiz_data["questions"])
        }
    return {"available_topics": topics}

@mcp.tool()
def get_quiz_for_topic(topic: str) -> dict:
    """Retrieve a quiz for a specific topic."""
    if topic.lower() not in QUIZ_CATALOG:
        return {
            "error": f"Topic '{topic}' not found",
            "available_topics": list(QUIZ_CATALOG.keys())
        }
    
    return QUIZ_CATALOG[topic.lower()]

# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
Running the MCP Server
Once you've create quiz_mcp_server.py with the code above, start it in its own terminal:

# Activate your virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Start the quiz MCP server
python quiz_mcp_server.py
Now you should see something similar to this:

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
Important: Keep this terminal running! The MCP server needs to stay active for your agent to connect to it.
Connecting to the MCP Server
Now let's integrate our subject expert agent with the quiz service. Create subject_expert_with_mcp.py:


from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

def main():
    # Connect to the quiz MCP server
    print("\nConnecting to MCP Server...")
    mcp_quiz_server = MCPClient(lambda: streamablehttp_client("http://localhost:8080/mcp"))

    try:
        with mcp_quiz_server:

            # Create the subject expert agent with a system prompt
            subject_expert = Agent(
                system_prompt="""You are a Computer Science Subject Expert with access to 
                an external quiz service. You can list available quiz topics, retrieve 
                quizzes for students, ask the user to take a quiz, and check their answers.

                When a student requests a quiz:
                1. Show available topics if they ask what's available
                2. Retrieve the specific quiz they want
                3. Present questions clearly, one at a time, with numbered options
                5. After they have provided all answers, check their responses against the
                   correct answers
                6. Once done with the quiz, give encouraging feedback and explanations

                Rules:
                - You must use the tools provided to you by the MCP server.
                - You must NOT make up your own quiz topics or questions.
                - The quiz data includes correct answers, so you can grade responses yourself.
                """
            )

            # List the tools available on the MCP server...
            mcp_tools = mcp_quiz_server.list_tools_sync()
            print(f"Available tools: {[tool.tool_name for tool in mcp_tools]}")

            # ... and add them to the agent
            subject_expert.tool_registry.process_tools(mcp_tools)

            # Start an interactive learning session
            print("\n👨‍💻 CS Subject Expert with MCP Integration")
            print("=" * 50)
            print("\n📋 Try: 'What quiz topics are available?' or 'Give me a Python quiz'")

            while True:
                user_input = input("\n🎯 Your request: ")
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("👋 Happy learning!")
                    break
                
                print("\n🤔 Processing...\n")
                subject_expert(user_input)
               
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure the quiz service is running: python quiz_mcp_server.py")

if __name__ == "__main__":
    main()
Connecting Your Agent
Open a second terminal and activate your virtual environment there too:

# In a NEW terminal window/tab
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Run your agent (make sure the server is still running in the other terminal)
python subject_expert_with_mcp.py
You should see:

Connecting to MCP Server...
Available tools: ['list_quiz_topics', 'get_quiz_for_topic']

👨‍💻 CS Subject Expert with MCP Integration
==================================================

📋 Try: 'What quiz topics are available?' or 'Give me a Python quiz'
Testing the Integration
Now you can interact with your agent, which seamlessly combines local tools with external services:
Discovering available content:

🎯 Your request: What quiz topics are available?

🤔 Processing...

I'd be happy to help you find out what quiz topics are available!
Let me check that for you.

Tool #1: list_quiz_topics

Here are the available quiz topics:

1. **Python Programming Fundamentals** (2 questions)
2. **Data Structures Essentials** (1 question)

Would you like to take a quiz on one of these topics?
Taking a quiz:

🎯 Your request: I'd like to try the Python basics quiz

🤔 Processing...

Great choice! Let me retrieve the Python Programming Fundamentals quiz for you.
Tool #2: get_quiz_for_topic

# Python Programming Fundamentals Quiz

I'll present one question at a time. Please provide your answer by selecting
one of the options.

## Question 1:
What keyword is used to define a function in Python?
1. func
2. def
3. function
4. define

Please answer with the number (1-4).
Getting feedback:
Once you've answered all questions, the agent will show you the results.

🙌 Congratulations! You've completed the Python Programming Fundamentals quiz
with a perfect score of 2/2! 

Would you like to try another quiz topic, or do you have any questions about
the material we covered?
Now try experimenting with correct and incorrect answers. You could also ask the agent for more detailed explanations to help you learn the concepts.
Direct Tool Calling
While the agent automatically selects tools based on conversation, you can also call MCP tools directly:

# Example of direct tool usage
with mcp_quiz_server:
    mcp_tools = mcp_quiz_server.list_tools_sync()
    agent = Agent(tools=mcp_tools)
    
    # Direct tool call via MCP
    topics = agent.tool.list_quiz_topics()
    print(f"Available topics:\n{topics}")
This gives you direct control when needed, while still benefiting from the agent's natural language interface.
Understanding Strands' MCP Integration
This integration demonstrates several key advantages of the MCP approach:
Service Abstraction: Your agent doesn't need to know the internal implementation of the quiz service. It could be a simple JSON file, a complex database, or even an AI-powered agent itself - the MCP interface remains the same.
Technology Independence: The quiz service could be rewritten in Java, hosted anywhere on the internet, or replaced with a completely different provider - your agent code doesn't change.
Scalability: You can easily connect to multiple services, and even mix them with your own custom or built-in tools:

# Connect to external MCP servers
quiz_service = MCPClient(lambda: streamablehttp_client("http://quiz-provider.com/mcp"))
library_service = MCPClient(lambda: streamablehttp_client("http://cs-library.edu/mcp"))

with quiz_service, library_server:
    # Combine all tools - they all work the same way!
    tools = (
        quiz_service.list_tools_sync() +      # Tools from the external quiz server
        library_service.list_tools_sync() +   # Tools from the external library server
        [http_request] +                      # Built-in tools from the Strands SDK
        [cs_glossary, ...]                    # Your custom tools
    )
    
    # Create agent with all tools
    agent = Agent(tools=tools)
Production Considerations
Some important considerations when connecting to real MCP servers in production are...
📊 Monitoring: Track service health and performance.
⚠️ Error Handling: Implement robust fallbacks for service unavailability.
🔐 Authentication: Many commercial MCP servers may require API keys or OAuth.
Here is an example with a custom timeout, an authorization header, and a local fallback in case the MCP server is unavailable:

mcp_client = MCPClient(lambda: streamablehttp_client(
    "https://example.com/mcp",
    timeout=timedelta(seconds=10),
    headers={"Authorization": "Bearer <token>"}, 
))

try:
    tools = mcp_client.list_tools_sync()
except Exception as e:
    print(f"Service unavailable: {e}")
    # Fall back to local tools only
    tools = [cs_glossary]
What We've Learned
In this tutorial, we've:
✅ Built a simple MCP server to demonstrate external integration
✅ Connected our agent to the MCP server with minimal code
✅ Accomplished seamless tool integration through natural language
✅ Understood how the Strands Agents SDK abstracts MCP complexity
✅ Explored advanced patterns for scaling, security, and error handling
Our subject expert agent can now use external services, opening up endless possibilities to integrate with all kinds of specialized platforms and tools.
Next Steps & Resources
In Part 4, we'll explore Alternative Model Providers, showing you how to set up local model deployment for development and testing.
Want to learn more about the Strands Agents SDK?
Here are some resources to help you deepen your understanding:
📚 Strands Agents Documentation - Comprehensive guides and API references
💻 GitHub Repository - Source code and examples - and if you like it, consider giving it a ⭐
🧩 Example Gallery - Explore sample implementations for various use cases
What kind of MCP servers would you like to use - or even build yourself? Share your ideas in the comments below!
💡 Troubleshooting Tips
Connection Issues:
Ensure the MCP server is running before starting your agent
Verify the URL includes the /mcp path: http://localhost:8080/mcp
Check firewall settings if running on different machines
Service Discovery Problems:
Restart both server and client if tools aren't discovered
Check the MCP server terminal for error messages
Virtual Environment Issues:
Make sure both terminals have the virtual environment activated before running the server and client
If you see import errors, verify that strands-agents and strand-agents-tools are installed in your active environment with pip list | grep strands
 
 Model Context Protocol (MCP) Tools¶
The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Strands Agents integrates with MCP to extend agent capabilities through external tools and services.

MCP enables communication between agents and MCP servers that provide additional tools. Strands includes built-in support for connecting to MCP servers and using their tools.

MCP Server Connection Options¶
Strands provides several ways to connect to MCP servers:

1. Standard I/O (stdio)¶
For command-line tools and local processes that implement the MCP protocol:


from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
# Note: uvx command syntax differs by platform

# For macOS/Linux:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# For Windows:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=[
            "--from", 
            "awslabs.aws-documentation-mcp-server@latest", 
            "awslabs.aws-documentation-mcp-server.exe"
        ]
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
2. Streamable HTTP¶
For HTTP-based MCP servers that use Streamable-HTTP Events transport:


from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient

streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client("http://localhost:8000/mcp"))

# Create an agent with MCP tools
with streamable_http_mcp_client:
    # Get the tools from the MCP server
    tools = streamable_http_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
3. Server-Sent Events (SSE)¶
For HTTP-based MCP servers that use Server-Sent Events transport:


from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    # Get the tools from the MCP server
    tools = sse_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
4. Custom Transport with MCPClient¶
For advanced use cases, you can implement a custom transport mechanism by using the underlying MCPClient class directly. This requires implementing the MCPTransport protocol, which is a tuple of read and write streams:


from typing import Callable
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.tools.mcp.mcp_types import MCPTransport

# Define a function that returns your custom transport
def custom_transport_factory() -> MCPTransport:
    # Implement your custom transport mechanism
    # Must return a tuple of (read_stream, write_stream)
    # Both must implement the AsyncIterable and AsyncIterator protocols
    ...
    return read_stream, write_stream

# Create an MCPClient with your custom transport
custom_mcp_client = MCPClient(transport_callable=custom_transport_factory)

# Use the server with context manager
with custom_mcp_client:
    # Get the tools from the MCP server
    tools = custom_mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(tools=tools)
Using Multiple MCP Servers¶
You can connect to multiple MCP servers simultaneously and combine their tools:


from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to multiple MCP servers
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
stdio_mcp_client = MCPClient(lambda: stdio_client(StdioServerParameters(command="python", args=["path/to/mcp_server.py"])))

# Use both servers together
with sse_mcp_client, stdio_mcp_client:
    # Combine tools from both servers
    tools = sse_mcp_client.list_tools_sync() + stdio_mcp_client.list_tools_sync()

    # Create an agent with all tools
    agent = Agent(tools=tools)
MCP Tool Response Format¶
MCP tools can return responses in two primary content formats:

Text Content: Simple text responses
Image Content: Binary image data with associated MIME type
Strands automatically maps these MCP content types to the appropriate ToolResultContent format used by the agent framework:


def _map_mcp_content_to_tool_result_content(content):
    if isinstance(content, MCPTextContent):
        return {"text": content.text}
    elif isinstance(content, MCPImageContent):
        return {
            "image": {
                "format": map_mime_type_to_image_format(content.mimeType),
                "source": {"bytes": base64.b64decode(content.data)},
            }
        }
    else:
        # Unsupported content type
        return None
Tool Result Structure¶
When an MCP tool is called, the result is converted to a ToolResult with the following structure:


{
    "status": str,          # "success" or "error" based on the MCP call result
    "toolUseId": str,       # The ID of the tool use request
    "content": List[dict]   # A list of content items (text or image)
}
Implementing an MCP Server¶
You can create your own MCP server to extend agent capabilities. Here's a simple example of a calculator MCP server:


from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP("Calculator Server")

# Define a tool
@mcp.tool(description="Calculator tool which performs calculations")
def calculator(x: int, y: int) -> int:
    return x + y

# Run the server with SSE transport
mcp.run(transport="sse")
MCP Server Implementation Details¶
The MCP server connection in Strands is managed by the MCPClient class, which:

Establishes a connection to the MCP server using the provided transport
Initializes the MCP session
Discovers available tools
Handles tool invocation and result conversion
Manages the connection lifecycle
The connection runs in a background thread to avoid blocking the main application thread while maintaining communication with the MCP service.

Advanced Usage¶
Direct Tool Invocation¶
While tools are typically invoked by the agent based on user requests, you can also call MCP tools directly:


# Directly invoke an MCP tool
result = mcp_client.call_tool_sync(
    tool_use_id="tool-123",
    name="calculator",
    arguments={"x": 10, "y": 20}
)

# Process the result
print(f"Calculation result: {result['content'][0]['text']}")
Best Practices¶
Tool Descriptions: Provide clear descriptions for your tools to help the agent understand when and how to use them
Parameter Types: Use appropriate parameter types and descriptions to ensure correct tool usage
Error Handling: Return informative error messages when tools fail to execute properly
Security: Consider security implications when exposing tools via MCP, especially for network-accessible servers
Connection Management: Always use context managers (with statements) to ensure proper cleanup of MCP connections
Timeouts: Set appropriate timeouts for tool calls to prevent hanging on long-running operations
Troubleshooting¶
Common Issues¶
Connection Failures:

Ensure the MCP server is running and accessible
Check network connectivity and firewall settings
Verify the URL or command is correct
Tool Discovery Issues:

Ensure the MCP server properly implements the list_tools method
Check that tools are correctly registered with the server
Tool Execution Errors:

Verify that tool arguments match the expected schema
Check server logs for detailed error information

# Strands using MCP Summary

## MCP Server Connection Options

Strands provides several ways to connect to MCP servers:

### 1. Standard I/O (stdio)

For command-line tools and local processes:

python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)


### 2. Streamable HTTP

For HTTP-based MCP servers using Streamable-HTTP Events transport:

python
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient

streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client("http://localhost:8000/mcp")
)

# Create an agent with MCP tools
with streamable_http_mcp_client:
    # Get the tools from the MCP server
    tools = streamable_http_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)


### 3. Server-Sent Events (SSE)

For HTTP-based MCP servers using Server-Sent Events transport:

python
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using SSE transport
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

# Create an agent with MCP tools
with sse_mcp_client:
    # Get the tools from the MCP server
    tools = sse_mcp_client.list_tools_sync()
    
    # Create an agent with these tools
    agent = Agent(tools=tools)


## Using Multiple MCP Servers

You can connect to multiple MCP servers simultaneously and combine their tools:

python
from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to multiple MCP servers
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="python", args=["path/to/mcp_server.py"])
    )
)

# Use both servers together
with sse_mcp_client, stdio_mcp_client:
    # Combine tools from both servers
    tools = sse_mcp_client.list_tools_sync() + stdio_mcp_client.list_tools_sync()
    
    # Create an agent with all tools
    agent = Agent(tools=tools)


## Creating Your Own MCP Server

You can create your own MCP server to provide custom tools. Here's a simple example:

python
from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP(
    name="Computer Science Quiz Service",
    host="0.0.0.0",
    port=8080
)

@mcp.tool()
def list_quiz_topics() -> dict:
    """List all available quiz topics."""
    topics = {
        "python_basics": {"title": "Python Programming Fundamentals", "question_count": 2},
        "data_structures": {"title": "Data Structures Essentials", "question_count": 1}
    }
    return {"available_topics": topics}

@mcp.tool()
def get_quiz_for_topic(topic: str) -> dict:
    """Retrieve a quiz for a specific topic."""
    # Implementation details...
    return quiz_data

# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")


## Direct Tool Invocation

While tools are typically invoked by the agent based on user requests, you can also call MCP tools directly:

python
# Directly invoke an MCP tool
result = mcp_client.call_tool_sync(
    tool_use_id="tool-123",
    name="calculator",
    arguments={"x": 10, "y": 20}
)

# Process the result
print(f"Calculation result: {result['content'][0]['text']}")


## Best Practices for MCP Integration

1. Monitoring: Track service health and performance
2. Error Handling: Implement robust fallbacks for service unavailability
3. Authentication: Use appropriate authentication for commercial MCP servers
4. Tool Descriptions: Provide clear descriptions to help the agent understand when and how to use tools
5. Connection Management: Always use context managers (with statements) to ensure proper cleanup
6. Timeouts: Set appropriate timeouts for tool calls to prevent hanging

## Example: Implementing a Quiz MCP Server

Here's a more complete example of implementing and using an MCP server:

1. Create the MCP server (quiz_mcp_server.py):

python
from mcp.server import FastMCP

# Create an MCP server
mcp = FastMCP(
    name="Computer Science Quiz Service",
    host="0.0.0.0",
    port=8080
)

# Quiz database
QUIZ_CATALOG = {
    "python_basics": {
        "title": "Python Programming Fundamentals",
        "questions": [
            {
                "question": "What keyword is used to define a function in Python?",
                "options": ["func", "def", "function", "define"],
                "correct_answer": "def"
            },
            # More questions...
        ]
    },
    # More topics...
}

@mcp.tool()
def list_quiz_topics() -> dict:
    """List all available quiz topics."""
    topics = {}
    for topic_id, quiz_data in QUIZ_CATALOG.items():
        topics[topic_id] = {
            "title": quiz_data["title"],
            "question_count": len(quiz_data["questions"])
        }
    return {"available_topics": topics}

@mcp.tool()
def get_quiz_for_topic(topic: str) -> dict:
    """Retrieve a quiz for a specific topic."""
    if topic.lower() not in QUIZ_CATALOG:
        return {
            "error": f"Topic '{topic}' not found",
            "available_topics": list(QUIZ_CATALOG.keys())
        }
    
    return QUIZ_CATALOG[topic.lower()]

# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")


2. Connect your agent to the MCP server:

python
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Connect to the quiz MCP server
mcp_quiz_server = MCPClient(
    lambda: streamablehttp_client("http://localhost:8080/mcp")
)

with mcp_quiz_server:
    # Create the agent with a system prompt
    subject_expert = Agent(
        system_prompt="""You are a Computer Science Subject Expert with access to 
        an external quiz service. You can list available quiz topics, retrieve 
        quizzes for students, and help them with their studies."""
    )
    
    # Get the tools from the MCP server
    mcp_tools = mcp_quiz_server.list_tools_sync()
    
    # Add them to the agent
    subject_expert.tool_registry.process_tools(mcp_tools)
    
    # Use the agent
    subject_expert("What quiz topics are available?")


## Troubleshooting MCP Connections

If you encounter issues with MCP connections:

1. Connection Issues:
   • Ensure the MCP server is running before starting your agent
   • Verify the URL includes the correct path (e.g., /mcp or /sse)
   • Check firewall settings if running on different machines

2. Service Discovery Problems:
   • Restart both server and client if tools aren't discovered
   • Check the MCP server terminal for error messages

3. Virtual Environment Issues:
   • Make sure both terminals have the virtual environment activated
   • Verify that required packages are installed

By leveraging MCP with Strands Agents SDK, you can create powerful, extensible agents that seamlessly integrate with external services and tools, all through a standardized interface.