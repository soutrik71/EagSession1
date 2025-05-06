# Example of how to use the decision making and action layers
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv
import uuid
import os

# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import from our modules
from url_rag.client.decision import get_llm_decision
from url_rag.client.action import execute_actions, print_message_chain
from url_rag.client.memory import ConversationMemory

# Import LLM directly from provider
from url_rag.utility.llm_provider import default_llm
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

# Server parameters
server_params = StdioServerParameters(
    command="python", args=["url_rag/server/server.py"]
)


async def main(query: str, conversation_memory=None, conv_id=None):
    """Main function that coordinates the decision making and action layers for a single query.

    Args:
        query: The user's query string
        conversation_memory: ConversationMemory instance for storing chat history
        conv_id: The conversation ID

    Returns:
        Tuple of (response, updated message chain)
    """
    messages = []
    # Initialize empty conversation memory if None
    if conversation_memory is None:
        # Initialize conversation memory with a unique ID and get the chat history
        conversation_memory = ConversationMemory(
            embedder, index_folder=history_index_name, reset_index=True
        )
        chat_history = conversation_memory.get_conversation_as_lc_messages(str(conv_id))
    else:
        # Get messages from conversation memory for the given conversation ID
        chat_history = conversation_memory.get_conversation_as_lc_messages(str(conv_id))

    try:
        # Add the user query to conversation memory
        messages.append({"sender": "human", "content": query})

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
                response, msg_objs = await get_llm_decision(
                    session=session,
                    query=query,
                    tools=tools,
                    llm=llm,
                    chat_history=chat_history,
                )

                # Convert message objects to dicts for storage
                def msg_to_dict(msg):
                    if hasattr(msg, "content"):
                        return {
                            "sender": getattr(
                                msg, "role", msg.__class__.__name__.lower()
                            ),
                            "content": msg.content,
                        }
                    elif isinstance(msg, dict):
                        return msg
                    else:
                        return {"sender": str(type(msg)), "content": str(msg)}

                messages.extend([msg_to_dict(m) for m in msg_objs])

                # Check if response is an error string
                if isinstance(response, str) and response.startswith("Error:"):
                    print(f"LLM decision failed: {response}")
                    # Create a message with the error to show to the user
                    messages.append(
                        {
                            "sender": "ai",
                            "content": f"I encountered an error: {response}",
                        }
                    )

                    # Save the error message to conversation memory
                    conversation_memory.store_conversation(str(conv_id), messages)

                    return response, messages

                # Step 5: Execute tool calls (in action_layer)
                print("Executing tool calls...")
                response, tool_msgs = await execute_actions(response, [], tools)

                # Convert tool messages to dicts and add to messages
                messages.extend(
                    [msg_to_dict(m) for m in tool_msgs if hasattr(m, "content")]
                )

                # Step 6: Print the final message chain (in action_layer)
                print_message_chain(msg_objs + tool_msgs)

                # Save AI response to conversation memory
                if hasattr(response, "content") and response.content:
                    messages.append({"sender": "ai", "content": response.content})
                elif hasattr(response, "tool_calls") and response.tool_calls:
                    raw_tool_info = ", ".join(
                        [tc["name"] for tc in response.tool_calls]
                    )
                    messages.append({"sender": "ai", "content": raw_tool_info})

                # Save the messages to conversation memory
                conversation_memory.store_conversation(str(conv_id), messages)

                return response, messages
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()

        # Add error to conversation memory
        if conversation_memory:
            conversation_memory.store_conversation(str(conv_id), messages)

        return f"Error: {str(e)}", []


async def run_conversation():
    """Run a conversation with multiple queries, maintaining chat history."""
    # List of example queries to process in sequence
    queries = [
        "What is the use of docker?",
        # "Give me the importance of helm in kubernetes?",
        # "Give me best 2 articles on the same topic?",
    ]

    # Initialize conversation memory with a unique ID

    conv_id = uuid.uuid4()
    conversation_memory = ConversationMemory(
        embedder, index_folder=history_index_name, reset_index=True
    )

    # Process each query in sequence
    for i, query in enumerate(queries, 1):
        print("\n" + "=" * 50)
        print(f"QUERY {i}: {query}")
        print("=" * 50 + "\n")

        # Run the main function with the current query and conversation memory
        response, messages = await main(query, conversation_memory, conv_id)

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
