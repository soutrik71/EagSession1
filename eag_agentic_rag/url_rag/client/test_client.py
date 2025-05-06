# Standard library imports
import asyncio
import json
import os
import pickle
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Third-party imports
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# Load environment variables
load_dotenv()

# Local imports
from url_rag.client.perception import WebContentSearch, get_perception_chain
from url_rag.client.memory import ConversationMemory
from url_rag.utility.llm_provider import default_llm
from url_rag.utility.embedding_provider import OpenAIEmbeddingProvider
from url_rag.utility.utils import read_yaml_file

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize global variables
llm = default_llm.chat_model
embedder = OpenAIEmbeddingProvider().embeddings
perception_chain = get_perception_chain(llm)

# Read config from file
config = read_yaml_file("url_rag/utility/config.yaml")
print(config)

# Set up history index path
history_index_name = config["history_index_name"]
history_index_name = os.path.join(os.getcwd(), history_index_name)

# Server parameters with absolute paths and proper python interpreter
server_path = os.path.join(os.getcwd(), "url_rag", "server", "server.py")
server_params = StdioServerParameters(
    command=sys.executable,  # Use the same Python interpreter as the client
    args=[server_path],
    cwd=os.getcwd(),  # Set the working directory explicitly
)


def explain_perception_result(perception_result: WebContentSearch) -> str:
    """Create a human-readable explanation of the perception chain result.

    Args:
        perception_result: The TravelSearch object from the perception chain

    Returns:
        A string explaining each part of the JSON output
    """
    result_dict = perception_result.model_dump()

    explanation = "I understand your original query as follows:\n\n"

    # Add explanation for each field in the JSON output
    for field, value in result_dict.items():
        explanation += f"- {field}: {value}\n"

    explanation += f"\nJSON representation: {json.dumps(result_dict, indent=2)}"

    return explanation


async def analyze_query(query: str, chat_history=None) -> Optional[str]:
    """Analyze a user query with the perception chain.

    Args:
        query: The user's query string
        chat_history: List of previous conversation messages

    Returns:
        An explanation of the perception results, or None if perception failed
    """
    # Initialize empty chat history if None
    if chat_history is None:
        chat_history = []

    query_lower = query.lower()

    try:
        print("Processing query through perception chain...")
        perception_result = await perception_chain.ainvoke(
            {"user_query": query_lower, "chat_history": chat_history}
        )

        print(f"The perception result is: {perception_result.model_dump()}")

        # Create explanation of perception results
        print("Creating explanation of perception results...")
        explanation = explain_perception_result(perception_result)

        print(f"\nPerception explanation:\n{explanation}\n")
        return explanation

    except Exception as e:
        print(f"Perception chain failed: {e}")
        print(
            "Query may not be related to travel booking - skipping perception analysis"
        )
        return None


async def get_llm_decision(
    session: ClientSession,
    query: str,
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    chat_history: Optional[List[Dict]] = None,
) -> Tuple[Any, List[Dict]]:
    """Get a decision from the LLM based on the query and perception explanation.

    Args:
        session: The MCP client session
        query: The user's original query
        tools: Optional list of pre-loaded tools
        llm: Optional LLM instance to use instead of the default
        chat_history: Optional chat history for context

    Returns:
        Tuple of (LLM response, message chain)
    """
    try:
        # Use provided LLM or fall back to default
        model = llm if llm is not None else default_llm.chat_model

        # Load tools if not provided
        if tools is None:
            print("Loading tools...")
            tools = await load_mcp_tools(session)

        print("Binding tools to model...")
        llm_with_tools = model.bind_tools(tools)

        # Get the enhanced query
        enhanced_query = await analyze_query(query, chat_history)

        # Process query
        print("Invoking model...")
        response = await llm_with_tools.ainvoke(enhanced_query)

        # Build initial message chain
        messages = [HumanMessage(content=query)]

        if response.tool_calls:
            # Add AI message with tool calls
            messages.append(AIMessage(content="", tool_calls=response.tool_calls))
        else:
            # Add AI message with content
            messages.append(AIMessage(content=response.content))

        return response, messages
    except Exception as e:
        print(f"Error in decision making: {e}")
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}", [HumanMessage(content=query)]


async def main(query: str, conversation_memory=None, conv_id=None):
    """Main function that coordinates the decision making and action layers for a single query.

    Args:
        query: The user's query string
        conversation_memory: Optional conversation memory instance
        conv_id: Optional conversation ID

    Returns:
        Tuple of (response, message objects, tools)
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

        # Add the user query to conversation memory
        messages.append({"sender": "human", "content": query})

    try:
        # Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            try:
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    await session.initialize()

                    # Get tools (load only once)
                    print("Loading tools...")
                    tools = await load_mcp_tools(session)

                    print(f"The tools are: {tools}")

                    # Get LLM decision
                    print("Getting LLM decision...")
                    response, msg_objs = await get_llm_decision(
                        session=session,
                        query=query,
                        tools=tools,
                        llm=llm,
                        chat_history=chat_history,
                    )

                    return response, msg_objs, tools
            except Exception as e:
                print(f"Session error: {e}")
                raise
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback

        traceback.print_exc()
        return None, None, None


if __name__ == "__main__":
    # Run the main function with a test query
    response, msg_objs, tools = asyncio.run(
        main(
            "What is the object of using helm?",
            memory_store := ConversationMemory(
                embedder, index_folder=history_index_name, reset_index=True
            ),
            uuid.uuid4(),
        )
    )

    # Create a data structure with three keys: response, message, tools
    output_data = {"response": response, "msg_objs": msg_objs, "tools": tools}

    print(f"The output data is: {output_data}")

    # Try to save raw data with pickle first - but handle the unpicklable coroutine
    try:
        # Create a modified version of the data for pickling
        pickle_data = {
            "response": response,
            "msg_objs": msg_objs,
            # For tools, we need to remove the coroutine attribute that can't be pickled
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "args_schema": (
                        tool.args_schema if hasattr(tool, "args_schema") else None
                    ),
                    "response_format": (
                        tool.response_format
                        if hasattr(tool, "response_format")
                        else None
                    ),
                }
                for tool in tools
            ],
        }

        pickle_filename = "url_rag/client/test_client_output.pickle"
        with open(pickle_filename, "wb") as f:
            pickle.dump(pickle_data, f)
        print(f"Successfully saved raw data to {pickle_filename}")
    except Exception as e:
        print(f"Error saving pickle data: {str(e)}")
        print("Attempting to save with protocol 0 (most compatible)...")
        try:
            with open(pickle_filename, "wb") as f:
                pickle.dump(pickle_data, f, protocol=0)
            print(f"Successfully saved with protocol 0 to {pickle_filename}")
        except Exception as e2:
            print(f"Still failed with protocol 0: {str(e2)}")

    # Extract and save the important components as JSON
    json_output = {
        "response": {
            "content": response.content if hasattr(response, "content") else "",
            "tool_calls": [
                {
                    "name": tc["name"],
                    "id": tc["id"],
                    "type": tc.get("type", "function"),
                    "args": tc["args"],
                }
                for tc in (
                    response.tool_calls if hasattr(response, "tool_calls") else []
                )
            ],
            "model": (
                response.response_metadata.get("model_name")
                if hasattr(response, "response_metadata")
                else None
            ),
            "finish_reason": (
                response.response_metadata.get("finish_reason")
                if hasattr(response, "response_metadata")
                else None
            ),
            "usage": {
                "total_tokens": (
                    response.usage_metadata.get("total_tokens")
                    if hasattr(response, "usage_metadata")
                    else None
                ),
                "input_tokens": (
                    response.usage_metadata.get("input_tokens")
                    if hasattr(response, "usage_metadata")
                    else None
                ),
                "output_tokens": (
                    response.usage_metadata.get("output_tokens")
                    if hasattr(response, "usage_metadata")
                    else None
                ),
            },
        },
        "messages": [
            {
                "type": msg.__class__.__name__,
                "content": msg.content if hasattr(msg, "content") else "",
                "tool_calls": (
                    [
                        {
                            "name": tc["name"],
                            "id": tc["id"],
                            "type": tc.get("type", "function"),
                            "args": tc["args"],
                        }
                        for tc in (msg.tool_calls if hasattr(msg, "tool_calls") else [])
                    ]
                    if hasattr(msg, "tool_calls") and msg.tool_calls
                    else []
                ),
            }
            for msg in msg_objs
        ],
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": (
                    tool.args_schema if hasattr(tool, "args_schema") else None
                ),
                "response_format": (
                    tool.response_format if hasattr(tool, "response_format") else None
                ),
            }
            for tool in tools
        ],
    }

    # Save as JSON
    json_filename = "url_rag/client/test_client_output.json"
    with open(json_filename, "w") as f:
        json.dump(json_output, f, indent=2, default=str)

    print(f"Saved components to {json_filename}")
