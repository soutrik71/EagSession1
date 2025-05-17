# Decision making layer - handles query enhancement and LLM calls
import sys
import os

# Add the parent directory (eag_agentic_rag) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Add the current path and project root to the Python path to enable module imports
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)


import json
from typing import Optional, Tuple, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LLM provider - this handles SSL configuration
from client.llm_provider import default_llm

llm = default_llm.chat_model

# Try to import perception chain, but don't fail if it's not available
try:
    from client.perception import ContentSearch, get_perception_chain, Process

    perception_chain = get_perception_chain(llm)
    PERCEPTION_AVAILABLE = True
except ImportError:
    print("Perception module not available - will use queries directly")
    perception_chain = None
    PERCEPTION_AVAILABLE = False

    # Define a minimal ContentSearch class for type hints if not imported above
    class ContentSearch:
        def model_dump(self):
            return {}

    class Process:
        sub_question: str
        tool: str


def explain_perception_result(perception_result: ContentSearch) -> str:
    """Create a human-readable explanation of the perception chain result.

    Args:
        perception_result: The ContentSearch object from the perception chain

    Returns:
        A string explaining each part of the JSON output
    """
    result_dict = perception_result.model_dump()

    if not result_dict:
        return "No perception analysis available."

    explanation = "I understand your original query as follows:\n\n"
    explanation += (
        f"Enhanced query: {result_dict.get('enhanced_user_query', 'N/A')}\n\n"
    )

    if "list_of_processes" in result_dict:
        explanation += "Breaking this down into the following sub-questions:\n"
        for process in result_dict["list_of_processes"]:
            explanation += f"- {process.get('sub_question', 'N/A')} (using {process.get('tool', 'N/A')})\n"

    explanation += f"\nJSON representation: {json.dumps(result_dict, indent=2)}"

    return explanation


async def analyze_query(
    query: str, chat_history=None
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Analyze a user query with the perception chain.

    Args:
        query: The user's query string
        chat_history: List of previous conversation messages

    Returns:
        A tuple of (enhanced query, list of sub-questions with tools) or (original query, []) if perception failed
    """
    # If perception is not available, return the original query with empty sub-questions
    if not PERCEPTION_AVAILABLE or perception_chain is None:
        return query, []

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

        # Extract enhanced query and sub-questions
        enhanced_query = perception_result.enhanced_user_query
        sub_questions = []

        # Extract each sub-question and its tool
        for process in perception_result.list_of_processes:
            sub_questions.append(
                {"sub_question": process.sub_question, "tool": process.tool}
            )

        print(f"Enhanced query: {enhanced_query}")
        print(f"Sub-questions: {sub_questions}")

        return enhanced_query, sub_questions

    except Exception as e:
        print(f"Perception chain failed: {e}")
        print("Falling back to original query")
        return query, []


async def get_llm_decision(
    client,  # Can be either ClientSession or MultiServerMCPClient
    query: str,
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    chat_history: Optional[List[Dict]] = None,
) -> Tuple[Any, List[Dict]]:
    """Get a decision from the LLM based on the query and perception explanation.

    Args:
        client: The MCP client (either ClientSession or MultiServerMCPClient)
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
            # Check if we have a ClientSession or MultiServerMCPClient
            if hasattr(client, "get_tools"):
                # It's a MultiServerMCPClient
                tools = await client.get_tools()
            else:
                # It's a ClientSession
                tools = await load_mcp_tools(client)

        print(f"The tools recognized by the langchain are::: {tools}")

        print("Binding tools to model...")
        llm_with_tools = model.bind_tools(tools)

        # Get enhanced query and sub-questions or fall back to original
        enhanced_query, sub_questions = await analyze_query(query, chat_history)

        # Initialize message chain with the user's original query
        messages = [HumanMessage(content=query)]

        # If we have sub-questions from perception, process each one separately
        if sub_questions:
            print(f"Processing {len(sub_questions)} sub-questions...")

            all_responses = []
            all_tool_names = []

            for i, sub_q in enumerate(sub_questions, 1):
                sub_question = sub_q["sub_question"]
                expected_tool = sub_q["tool"]

                print(
                    f"Processing sub-question {i}/{len(sub_questions)}: {sub_question}"
                )
                print(f"Expected tool: {expected_tool}")

                # Find tools that match the expected tool type
                matching_tools = [
                    t
                    for t in tools
                    if t.name.lower() == expected_tool.lower()
                    or any(
                        keyword in t.name.lower() for keyword in [expected_tool.lower()]
                    )
                ]

                if matching_tools:
                    print(
                        f"Found {len(matching_tools)} matching tools for '{expected_tool}'"
                    )
                    # If we have a specific tool for this sub-question, bind only that tool
                    specific_tool = matching_tools[0]
                    print(f"Using tool: {specific_tool.name} for '{expected_tool}'")

                    # Create a specialized model with just this tool
                    specialized_model = model.bind_tools([specific_tool])

                    # Process the sub-question with the specialized model
                    sub_response = await specialized_model.ainvoke(sub_question)
                else:
                    print(
                        f"No matching tools found for '{expected_tool}', using all tools"
                    )
                    # If no specific tool found, use all tools
                    sub_response = await llm_with_tools.ainvoke(sub_question)

                all_responses.append(sub_response)

                # Extract tool call information
                if hasattr(sub_response, "tool_calls") and sub_response.tool_calls:
                    try:
                        # Extract tool names for this sub-question
                        for tc in sub_response.tool_calls:
                            if isinstance(tc, dict) and "name" in tc:
                                all_tool_names.append(tc["name"])
                                print(f"Found tool call: {tc['name']}")
                            elif hasattr(tc, "name"):
                                all_tool_names.append(tc.name)
                                print(f"Found tool call: {tc.name}")
                            elif (
                                isinstance(tc, dict)
                                and "function" in tc
                                and "name" in tc["function"]
                            ):
                                all_tool_names.append(tc["function"]["name"])
                                print(f"Found tool call: {tc['function']['name']}")
                            else:
                                print(f"Unknown tool call format: {tc}")
                                all_tool_names.append("unknown_tool")
                    except Exception as e:
                        print(f"Error extracting tool names for sub-question {i}: {e}")
                else:
                    print(f"No tool calls found for sub-question {i}")
                    # If the specialized model didn't generate a tool call, try to create one manually
                    if matching_tools:
                        print(f"Creating manual tool call for {matching_tools[0].name}")
                        # Create a synthetic tool call
                        if not hasattr(sub_response, "tool_calls"):
                            setattr(sub_response, "tool_calls", [])

                        # Create appropriate arguments based on tool type and sub-question
                        tool_args = {}
                        tool_name = matching_tools[0].name

                        if tool_name == "create_gsheet":
                            # For create_gsheet, extract email from sub-question
                            import re

                            email_match = re.search(r"[\w\.-]+@[\w\.-]+", sub_question)
                            email = (
                                email_match.group(0)
                                if email_match
                                else "user@example.com"
                            )
                            tool_args = {"email_id": email}
                        elif tool_name == "search_web":
                            # For search_web, use the sub-question as query
                            tool_args = {"query": sub_question}
                        elif tool_name == "send_email":
                            # For send_email, provide basic arguments
                            import re

                            email_match = re.search(r"[\w\.-]+@[\w\.-]+", sub_question)
                            email = (
                                email_match.group(0)
                                if email_match
                                else "user@example.com"
                            )
                            tool_args = {
                                "recipient_id": email,
                                "subject": "Information Requested",
                                "message": "Here is the information you requested.",
                                "attachment_path": "./server/outputs/latest.json",
                            }

                        # Add the tool call
                        tool_call = {
                            "name": tool_name,
                            "id": f"manual-tool-call-{i}",
                            "args": tool_args,
                        }
                        sub_response.tool_calls.append(tool_call)
                        all_tool_names.append(tool_name)
                        print(
                            f"Added manual tool call: {tool_name} with args: {tool_args}"
                        )

            # Create a combined response with all tool calls
            # This will be used by the action layer
            if all_responses:
                # Create a new custom response that combines all tool calls
                combined_response = None

                # Store all tool calls from all sub-questions in the combined response
                all_tool_calls = []
                for resp in all_responses:
                    if hasattr(resp, "tool_calls") and resp.tool_calls:
                        all_tool_calls.extend(resp.tool_calls)

                print(
                    f"Collected a total of {len(all_tool_calls)} tool calls from {len(all_responses)} sub-responses"
                )

                # Take the last response as the base for our combined response
                if all_responses:
                    combined_response = all_responses[-1]

                    # For better debugging
                    for i, tc in enumerate(all_tool_calls):
                        if isinstance(tc, dict) and "name" in tc:
                            name = tc["name"]
                            args = tc.get("args", {})
                        elif hasattr(tc, "name"):
                            name = tc.name
                            args = getattr(tc, "args", {})
                        else:
                            name = "unknown"
                            args = {}
                        print(f"Tool call {i+1}: {name} with args: {args}")

                    # If we have any tool calls, ensure they're all captured properly
                    if all_tool_calls:
                        # Always set both tool_calls and combined_tool_calls
                        setattr(combined_response, "tool_calls", all_tool_calls)
                        setattr(
                            combined_response, "combined_tool_calls", all_tool_calls
                        )

                        # Print debug info to verify tool calls are being preserved
                        print(
                            f"Combined {len(all_tool_calls)} tool calls from {len(all_responses)} sub-responses"
                        )
                    else:
                        print("Warning: No tool calls found in any sub-responses")

                # If we have tool calls in any response, add the message about tools
                if all_tool_names:
                    unique_tools = list(set(all_tool_names))
                    tools_message = (
                        f"I'll help with that by using: {', '.join(unique_tools)}"
                    )
                    messages.append(AIMessage(content=tools_message))
                else:
                    # If no tool calls, use content from the last response
                    messages.append(
                        AIMessage(
                            content=(
                                combined_response.content
                                if hasattr(combined_response, "content")
                                else "I'll help you with that."
                            )
                        )
                    )

                # Return the combined response and all messages
                return combined_response, messages
        else:
            # No sub-questions, process enhanced query directly
            print("No sub-questions available, processing enhanced query directly")
            response = await llm_with_tools.ainvoke(enhanced_query)

            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = []
                try:
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
                            tool_names.append(tc["function"]["name"])
                        else:
                            print(f"Unknown tool call format: {tc}")
                            tool_names.append("unknown_tool")
                except Exception as e:
                    print(f"Error extracting tool names: {e}")
                    tool_names = ["unknown_tool"]

                tools_message = f"I'll help with that by using: {', '.join(tool_names)}"
                messages.append(AIMessage(content=tools_message))
            else:
                messages.append(
                    AIMessage(
                        content=(
                            response.content
                            if hasattr(response, "content")
                            else "I'll help you with that."
                        )
                    )
                )

        print(f"The response from the decision making layer is::: {response}")
        return response, messages
    except Exception as e:
        print(f"Error in decision making: {e}")
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}", [HumanMessage(content=query)]


if __name__ == "__main__":
    print("Testing decision making...")
    # If you need to run test code, add it here
