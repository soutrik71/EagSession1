# Decision making layer - handles query enhancement and LLM calls
import sys
import os

# Add the parent directory (eag_agentic_rag) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

import json
from typing import Optional, Tuple, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LLM provider - this handles SSL configuration
from url_rag.client.llm_provider import default_llm

llm = default_llm.chat_model

# Try to import perception chain, but don't fail if it's not available
try:
    from url_rag.client.perception import WebContentSearch, get_perception_chain

    perception_chain = get_perception_chain(llm)
    PERCEPTION_AVAILABLE = True
except ImportError:
    print("Perception module not available - will use queries directly")
    perception_chain = None
    PERCEPTION_AVAILABLE = False

    # Define a minimal WebContentSearch class for type hints
    class WebContentSearch:
        def model_dump(self):
            return {}


def explain_perception_result(perception_result: WebContentSearch) -> str:
    """Create a human-readable explanation of the perception chain result.

    Args:
        perception_result: The TravelSearch object from the perception chain

    Returns:
        A string explaining each part of the JSON output
    """
    result_dict = perception_result.model_dump()

    if not result_dict:
        return "No perception analysis available."

    explanation = "I understand your original query as follows:\n\n"

    # Add explanation for each field in the JSON output
    for field, value in result_dict.items():
        explanation += f"- {field}: {value}\n"

    explanation += f"\nJSON representation of the actual query: {json.dumps(result_dict, indent=2)}"

    return explanation


async def analyze_query(query: str, chat_history=None) -> Optional[str]:
    """Analyze a user query with the perception chain.

    Args:
        query: The user's query string
        chat_history: List of previous conversation messages

    Returns:
        An explanation of the perception results, or None if perception failed
    """
    # If perception is not available, return the original query
    if not PERCEPTION_AVAILABLE or perception_chain is None:
        return query

    # Initialize empty chat history if None
    if chat_history is None:
        chat_history = []

    query_lower = query.lower()

    try:
        print("Processing query through perception chain...")
        perception_result = await perception_chain.ainvoke(
            {"user_query": query_lower, "chat_history": chat_history}
        )

        print(f"The perception result is::: {perception_result.model_dump()}")

        # Create explanation of perception results
        print("Creating explanation of perception results...")
        explanation = explain_perception_result(perception_result)

        print(f"\nPerception explanation:\n{explanation}\n")
        return explanation

    except Exception as e:
        print(f"Perception chain failed: {e}")
        print("Falling back to original query")
        return query


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
        chat_history: Optional list of previous conversation messages

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

        # Get enhanced query or fall back to original
        enhanced_query = await analyze_query(query, chat_history)

        # If enhanced_query is None, use the original query
        input_query = enhanced_query if enhanced_query is not None else query

        # Process query
        print("Invoking model...")
        response = await llm_with_tools.ainvoke(input_query)

        # print(f"The response is::: {response}")
        # Build initial message chain - this is the message chain that will be used to build the action chain
        messages = [HumanMessage(content=query)]

        if hasattr(response, "tool_calls") and response.tool_calls:
            # Extract the tool names from the tool calls with error handling
            tool_names = []

            try:
                # Debug information
                print(f"Tool calls structure: {type(response.tool_calls)}")
                print(f"Tool calls data: {response.tool_calls}")

                # Handle both list of dicts and list of objects formats
                for tc in response.tool_calls:
                    if isinstance(tc, dict) and "name" in tc:
                        tool_names.append(tc["name"])
                    elif hasattr(tc, "name"):
                        tool_names.append(tc.name)
                    elif (
                        isinstance(tc, dict)
                        and "function" in tc
                        and "name" in tc["function"]
                    ):
                        # Handle OpenAI-style format
                        tool_names.append(tc["function"]["name"])
                    else:
                        print(f"Unknown tool call format: {tc}")
                        tool_names.append("unknown_tool")

                print(f"Extracted tool names: {tool_names}")
            except Exception as e:
                print(f"Error extracting tool names: {e}")
                tool_names = ["unknown_tool"]

            # Create a more informative message about which tools are being used
            tools_message = f"I'll help with that by using: {', '.join(tool_names)}"

            # Log the tools being used
            print(f"Using tools: {tool_names}")

            # Add AI message with tool calls
            messages.append(AIMessage(content=tools_message))
        else:
            # Add AI message with content
            messages.append(AIMessage(content=response.content))

        return response, messages
    except Exception as e:
        print(f"Error in decision making: {e}")
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}", [HumanMessage(content=query)]


if __name__ == "__main__":
    print("Testing decision making...")
    # If you need to run test code, add it here
