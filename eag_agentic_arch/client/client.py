# Example of how to use the decision making and action layers
from ssl_helper import patch_ssl_verification

patch_ssl_verification()

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import from our modules
from decision_making import analyze_query, get_llm_decision
from action_layer import execute_actions, print_message_chain
from memory import ConversationMemory

# Import LLM directly from provider
from llm_provider import default_llm

# Get the default LLM
llm = default_llm.chat_model

# Server parameters
server_params = StdioServerParameters(command="python", args=["server/server.py"])

"""
Architecture Overview:
---------------------
The system is organized into three distinct layers:

1. Client Layer (client.py):
   - Entry point for the application
   - Coordinates the flow between decision making and action layers
   - Maintains conversation history across queries

2. Decision Making Layer (decision_making.py):
   - Analyzes user queries with perception chain
   - Generates explanations of travel search parameters
   - Makes LLM calls to get decisions or tool calls

3. Action Layer (action_layer.py):
   - Executes tool calls from the LLM
   - Formats and displays message chains

This separation provides:
- Clear responsibility boundaries
- Better maintainability
- Easier testing of individual components
- Flexibility to swap or enhance individual layers
"""


async def main(query: str, conversation_memory=None):
    """Main function that coordinates the decision making and action layers.

    Args:
        query: The user's query string
        conversation_memory: ConversationMemory instance for storing chat history

    Returns:
        Tuple of (response, updated message chain)
    """
    # Initialize empty conversation memory if None
    if conversation_memory is None:
        conversation_memory = ConversationMemory()
        chat_history = []
    else:
        # Get messages from conversation memory
        chat_history = conversation_memory.get_langchain_messages()

    try:
        # Add the user query to conversation memory
        conversation_memory.add_human_message(query)

        # Step 1: Analyze the query with perception (in decision_making)
        explanation = await analyze_query(query, chat_history)

        # Step 2: Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()

                # Step 3: Get tools (load only once)
                print("Loading tools...")
                tools = await load_mcp_tools(session)

                # Step 4: Get LLM decision (in decision_making), explicitly passing the LLM
                print("Getting LLM decision...")
                response, messages = await get_llm_decision(
                    session, query, explanation, tools, llm=llm
                )

                # Check if response is an error string
                if isinstance(response, str) and response.startswith("Error:"):
                    print(f"LLM decision failed: {response}")
                    # Create a message with the error to show to the user
                    from langchain_core.messages import AIMessage

                    error_message = AIMessage(
                        content=f"I encountered an error: {response}"
                    )
                    messages.append(error_message)

                    # Save the error message to conversation memory
                    conversation_memory.add_ai_message(
                        f"I encountered an error: {response}"
                    )

                    # Save conversation to disk
                    conversation_memory.save()

                    return response, messages

                # Step 5: Execute tool calls (in action_layer)
                print("Executing tool calls...")
                response, messages = await execute_actions(response, messages, tools)

                # Step 6: Print the final message chain (in action_layer)
                print_message_chain(messages)

                # Save AI response to conversation memory
                # We save only the most recent AI message to avoid duplicating the entire message chain
                if hasattr(response, "content") and response.content:
                    conversation_memory.add_ai_message(response.content)
                # If it's a tool call response, we include that information
                elif hasattr(response, "tool_calls") and response.tool_calls:
                    # Extract just the tool names without adding prefix text
                    raw_tool_info = ", ".join(
                        [tc["name"] for tc in response.tool_calls]
                    )
                    conversation_memory.add_ai_message(raw_tool_info)

                # Save the messages from tools to conversation memory
                for msg in messages:
                    if (
                        hasattr(msg, "content")
                        and msg.content
                        and msg.__class__.__name__ == "ToolMessage"
                    ):
                        # Extract just the tool result content without adding prefix text
                        conversation_memory.add_ai_message(msg.content)

                # Save conversation to disk
                conversation_memory.save()

                return response, messages
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()

        # Add error to conversation memory
        if conversation_memory:
            conversation_memory.add_ai_message(f"Error: {str(e)}")
            conversation_memory.save()

        return f"Error: {str(e)}", []


async def run_conversation():
    """Run a conversation with multiple queries, maintaining chat history."""
    # List of example queries to process in sequence
    queries = [
        "I want to search for flights from New York to Los Angeles on 2025-05-01 with return on 2025-05-05",
        "What about booking a hotel for the same dates and same destination?",
        "What is the capital of France?",
        "I want to book hotel in New York for 2 nights starting on 2025-05-01 to 2025-05-05 for 2 adults",
        "What about booking a return flight for the same dates?",
        "I want to search for flights from New York to Los Angeles on 2025-05-01 "
        "with return on 2025-05-05 and a hotel for 2 adults in Los Angeles for the same dates",
    ]

    # Initialize conversation memory with a unique ID
    conversation_memory = ConversationMemory(save_dir="conversations")
    print(f"Starting conversation with ID: {conversation_memory.conversation_id}")

    # Process each query in sequence
    for i, query in enumerate(queries, 1):
        print("\n" + "=" * 50)
        print(f"QUERY {i}: {query}")
        print("=" * 50 + "\n")

        # Run the main function with the current query and conversation memory
        response, messages = await main(query, conversation_memory)

        # Add a separator between queries
        print("\n" + "-" * 50 + "\n")

    print(f"Conversation complete. Processed {len(queries)} queries.")
    print(
        f"Conversation saved to: {conversation_memory.save_dir}/{conversation_memory.conversation_id}.json"
    )


if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except NotImplementedError as e:
        print(f"NotImplementedError: {e}")
        print("This is likely due to Windows asyncio subprocess issues.")
        print("Consider using a different approach for subprocess handling on Windows.")
