# Decision making layer - handles query enhancement and LLM calls
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
from typing import Optional, Tuple, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from url_rag.client.perception import WebContentSearch, get_perception_chain
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]

# Import LLM provider
from url_rag.utility.llm_provider import default_llm

llm = default_llm.chat_model

# Get default LLM and perception chain
perception_chain = get_perception_chain(llm)


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

    # print(f"The chat history is: {chat_history}")

    query_lower = query.lower()

    try:
        print("Processing query through perception chain...")
        perception_result = perception_chain.invoke(
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
        perception_explanation: Optional explanation from the perception chain
        tools: Optional list of pre-loaded tools
        llm: Optional LLM instance to use instead of the default

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

        # get the enhanced query
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
