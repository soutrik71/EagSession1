# Import and apply SSL certificate patch first (before any other imports)
from ssl_helper import patch_ssl_verification

patch_ssl_verification()

import asyncio
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import LLM provider and perception
from llm_provider import default_llm
from perception import get_perception_chain, TravelSearch

# Get the default LLM and perception chain
llm = default_llm.chat_model
perception_chain = get_perception_chain()

# Server parameters
server_params = StdioServerParameters(command="python", args=["server/server.py"])


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


async def process_tool_calls(tool_calls, tools):
    """Process tool calls by invoking the appropriate tool with arguments.

    Args:
        tool_calls: List of tool calls from the LLM response
        tools: List of available tools

    Returns:
        List of ToolMessage objects with the results
    """
    messages = []
    tool_dict = {tool.name: tool for tool in tools}

    for tool_call in tool_calls:
        if tool_call["name"] in tool_dict:
            selected_tool = tool_dict[tool_call["name"]]
            tool_output = await selected_tool.ainvoke(tool_call["args"])
            messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )
        else:
            print(f"Tool {tool_call['name']} not found in available tools")

    return messages


async def main(llm, query, perception_explanation=None):
    """Main function to run the client and process the response.

    Args:
        llm: The language model to use
        query: The user query to process
        perception_explanation: Optional explanation of the perception results

    Returns:
        Tuple of (original response, processed message chain)
    """
    try:
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()

                # Load and bind tools
                print("Loading tools...")
                tools = await load_mcp_tools(session)
                print("Binding tools to model...")
                llm_with_tools = llm.bind_tools(tools)

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

                # Build message chain
                messages = [HumanMessage(content=enhanced_query)]

                if response.tool_calls:
                    # Handle tool calls
                    print("Processing tool calls...")
                    messages.append(
                        AIMessage(content="", tool_calls=response.tool_calls)
                    )
                    tool_messages = await process_tool_calls(response.tool_calls, tools)
                    messages.extend(tool_messages)
                else:
                    # Handle direct content response
                    print("Processing direct content response...")
                    messages.append(AIMessage(content=response.content))

                return response, messages
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}", []


if __name__ == "__main__":
    # Choose one query to run
    # query = "I want to search for flights from New York to Los Angeles on 2025-05-01 with return on 2025-05-05"
    # query = "I want to book hotel in New York for 2 nights starting on 2025-05-01 to 2025-05-02 for 2 adults"
    query = "What is the capital of France?"
    # query = "I want to search for flights from New York to Los Angeles on 2025-05-01 with return on 2025-05-05 and a hotel for 2 adults in Los Angeles for the same dates"

    try:
        explanation = None
        # Process query through perception chain
        print("Processing query through perception chain...")
        try:
            perception_result = perception_chain.invoke(
                {"user_query": query, "chat_history": []}
            )

            # Create explanation of perception results
            print("Creating explanation of perception results...")
            explanation = explain_perception_result(perception_result)
            print(f"\nPerception explanation:\n{explanation}\n")
        except Exception as e:
            print(f"Perception chain failed: {e}")
            print(
                "Query may not be related to travel booking - skipping perception analysis"
            )

        # Run main function with perception explanation if available
        op, messages = asyncio.run(main(llm, query, explanation))

        print("\nProcessed messages chain:")
        for msg in messages:
            msg_type = type(msg).__name__
            msg_preview = msg.content
            print(f"- {msg_type}: {msg_preview}")

            # Print tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                print(f"  Tool calls: {[tc['name'] for tc in msg.tool_calls]}")

    except NotImplementedError as e:
        print(f"NotImplementedError: {e}")
        print("This is likely due to Windows asyncio subprocess issues.")
        print("Consider using a different approach for subprocess handling on Windows.")
