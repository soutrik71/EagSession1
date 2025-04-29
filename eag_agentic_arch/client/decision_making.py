# Decision making layer - handles query enhancement and LLM calls
import json
from typing import Optional, Tuple, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from perception import TravelSearch, get_perception_chain

# Import LLM provider
from llm_provider import default_llm


# Get default LLM and perception chain
perception_chain = get_perception_chain()


def explain_perception_result(perception_result: TravelSearch) -> str:
    """Create a human-readable explanation of the perception chain result.

    Args:
        perception_result: The TravelSearch object from the perception chain

    Returns:
        A string explaining each part of the JSON output
    """
    result_dict = perception_result.model_dump()

    explanation = "I understand your travel query as follows:\n\n"

    # Explain search type
    search_type = result_dict.get("search_type")
    if search_type == "flight":
        explanation += "- You want to search for FLIGHTS\n"
    elif search_type == "hotel":
        explanation += "- You want to search for HOTELS\n"
    elif search_type == "combined":
        explanation += "- You want to search for BOTH FLIGHTS AND HOTELS\n"

    # Explain dates
    start_date = result_dict.get("start_date")
    end_date = result_dict.get("end_date")
    if start_date:
        explanation += f"- Starting on: {start_date}\n"
    if end_date:
        explanation += f"- Ending on: {end_date}\n"

    # Explain flight-specific details
    flight_data = result_dict.get("flight")
    if flight_data:
        departure = flight_data.get("departure_id")
        arrival = flight_data.get("arrival_id")
        if departure:
            explanation += f"- Departing from: {departure}\n"
        if arrival:
            explanation += f"- Arriving at: {arrival}\n"

    # Explain hotel-specific details
    hotel_data = result_dict.get("hotel")
    if hotel_data:
        location = hotel_data.get("location")
        adults = hotel_data.get("adults")
        if location:
            explanation += f"- Hotel Location: {location}\n"
        if adults:
            explanation += f"- Number of adults: {adults}\n"

    # Explain currency
    currency = result_dict.get("currency")
    if currency:
        explanation += f"- Currency: {currency}\n"

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

    # Quick check if this is likely a travel query before running full perception
    travel_keywords = [
        "flight",
        "hotel",
        "book",
        "travel",
        "trip",
        "vacation",
        "airport",
        "airline",
        "stay",
        "accommodation",
        "reservation",
    ]

    query_lower = query.lower()
    is_likely_travel_query = any(keyword in query_lower for keyword in travel_keywords)

    if not is_likely_travel_query:
        print("Query doesn't appear to be travel-related, skipping perception analysis")
        return None

    try:
        print("Processing query through perception chain...")
        perception_result = perception_chain.invoke(
            {"user_query": query, "chat_history": chat_history}
        )

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
    perception_explanation: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
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

        # Add perception explanation to query if available
        enhanced_query = query
        if perception_explanation:
            enhanced_query = (
                f"{query}\n\nAnalysis of your query extracting the key entities: "
                f"{perception_explanation}"
            )

        # Process query
        print("Invoking model...")
        response = await llm_with_tools.ainvoke(enhanced_query)

        # Build initial message chain
        messages = [HumanMessage(content=enhanced_query)]

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
