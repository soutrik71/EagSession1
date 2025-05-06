# Example of how to use the decision making and action layers with perception and memory
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import llm_provider first to ensure SSL patching happens before any other imports
from url_rag.utility.llm_provider import default_llm

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import from our modules
from url_rag.client.decision import get_llm_decision
from url_rag.client.action import execute_actions, print_message_chain

# Import LLM directly from provider
from url_rag.utility.embedding_provider import OpenAIEmbeddingProvider
from url_rag.utility.utils import read_yaml_file

# Get the default LLM
llm = default_llm.chat_model
embedder = OpenAIEmbeddingProvider().embeddings

# read config
config = read_yaml_file("url_rag/utility/config.yaml")
print(config)

history_index_name = config["history_index_name"]
history_index_name = os.path.join(os.getcwd(), history_index_name)

# Server parameters with absolute paths and proper python interpreter
server_path = os.path.join(os.getcwd(), "url_rag", "server", "basic_server.py")
server_params = StdioServerParameters(
    command=sys.executable,  # Use the same Python interpreter as the client
    args=[server_path],
    cwd=os.getcwd(),  # Set the working directory explicitly
)


async def main(query: str):
    """Main function that coordinates the decision making and action layers for a single query."""
    chat_history = []

    try:
        # Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            try:
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    await session.initialize()

                    # Step 3: Get tools (load only once)
                    print("Loading tools...")
                    tools = await load_mcp_tools(session)

                    print(f"LC Tools: {tools}")

                    # Step 4: Get LLM decision, explicitly passing the LLM
                    print("Getting LLM decision...")
                    response, messages = await get_llm_decision(
                        session=session,
                        query=query,
                        tools=tools,
                        llm=llm,
                        chat_history=chat_history,
                    )

                    print("\n\n")
                    print(f"LLM Decision Messages: {messages}")
                    print("\n\n")
                    print(f"LLM Decision Response: {response}")

                    # Check if response is an error string
                    if isinstance(response, str) and response.startswith("Error:"):
                        print(f"LLM decision failed: {response}")
                        # Create a message with the error to show to the user
                        error_msg = f"I'm sorry, but I encountered an error processing your request: {response}"
                        messages.append(AIMessage(content=error_msg))
                        return response, messages

                    # Step 5: Execute tool calls
                    print("Executing tool calls...")
                    response, messages = await execute_actions(
                        response=response,
                        messages=messages,
                        tools=tools,
                    )

                    print(f"Execute Actions Messages: {messages}")
                    print("\n\n")
                    print(f"Execute Actions Response: {response}")

                    if isinstance(response, str) and response.startswith("Error:"):
                        print(f"Error in Execute Actions: {response}")
                        # Create a message with the error to show to the user
                        error_msg = f"I'm sorry, but I encountered an error processing your request: {response}"
                        messages.append(AIMessage(content=error_msg))
                        return response, messages

                    # Save AI response to messages
                    if hasattr(response, "content") and response.content:
                        messages.append({"sender": "ai", "content": response.content})
                    elif hasattr(response, "tool_calls") and response.tool_calls:
                        raw_tool_info = ", ".join(
                            [tc["name"] for tc in response.tool_calls]
                        )
                        messages.append({"sender": "ai", "content": raw_tool_info})

                    return response, messages
            except Exception as e:
                print(f"Session error: {e}")
                raise
    except Exception as e:
        print(f"Error occurred in main: {e}")
        import traceback

        traceback.print_exc()

        # Add error to messages
        error_msg = (
            f"I'm sorry, but I encountered an error processing your request: {str(e)}"
        )
        messages.append({"sender": "ai", "content": error_msg})

        return AIMessage(content=error_msg), [
            HumanMessage(content=query),
            AIMessage(content=error_msg),
        ]


async def run_conversation():
    """Run a conversation with multiple queries."""
    # List of example queries to process in sequence
    queries = [
        "What is the use of docker?",
        # "Give me the importance of helm in kubernetes?",
        # "Give me best 2 articles on the same topic?",
    ]

    # Process each query in sequence
    for i, query in enumerate(queries, 1):
        print("\n" + "=" * 50)
        print(f"QUERY {i}: {query}")
        print("=" * 50 + "\n")

        # Run the main function with the current query
        response, messages = await main(query)

        print(f"Messages: {messages}")
        print(f"Response: {response}")

        # Add a separator between queries
        print("\n" + "-" * 50 + "\n")

    print(f"Conversation complete. Processed {len(queries)} queries.")


if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except NotImplementedError as e:
        print(f"NotImplementedError: {e}")
        print("This is likely due to Windows asyncio subprocess issues.")
        print("Consider using a different approach for subprocess handling on Windows.")
