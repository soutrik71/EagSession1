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
import re
from typing import Optional, Tuple, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utils for logging
from client.utils import log, LogLevel

# Import LLM provider - this handles SSL configuration
from client.llm_provider import default_llm

llm = default_llm.chat_model

# Try to import perception chain, but don't fail if it's not available
try:
    from client.perception import ContentSearch, get_perception_chain, Process

    perception_chain = get_perception_chain(llm)
    PERCEPTION_AVAILABLE = True
except ImportError:
    log(
        "Perception module not available - will use queries directly",
        level=LogLevel.WARN,
    )
    perception_chain = None
    PERCEPTION_AVAILABLE = False

    # Define minimal ContentSearch class for type hints if not imported above
    class ContentSearch:
        def model_dump(self):
            return {}

    class Process:
        sub_question: str
        tool: str


def explain_perception_result(perception_result: ContentSearch) -> str:
    """Create a human-readable explanation of the perception chain result."""
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
    """
    Analyze a user query with the perception chain.

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
        log("Processing query through perception chain...", level=LogLevel.INFO)
        perception_result = await perception_chain.ainvoke(
            {"user_query": query_lower, "chat_history": chat_history}
        )

        log(
            f"Perception result: {perception_result.model_dump()}", level=LogLevel.DEBUG
        )

        # Create explanation of perception results for debugging
        explanation = explain_perception_result(perception_result)
        log(f"Perception explanation: {explanation}", level=LogLevel.DEBUG)

        # Extract enhanced query and sub-questions
        enhanced_query = perception_result.enhanced_user_query
        sub_questions = []

        # Extract each sub-question and its tool
        for process in perception_result.list_of_processes:
            sub_questions.append(
                {
                    "sub_question": process.sub_question,
                    "tool": process.tool,
                    "tool_args": (
                        process.tool_args if hasattr(process, "tool_args") else {}
                    ),
                }
            )

        log(f"Enhanced query: {enhanced_query}", level=LogLevel.INFO)
        log(f"Identified {len(sub_questions)} sub-questions", level=LogLevel.INFO)

        return enhanced_query, sub_questions

    except Exception as e:
        log(f"Perception chain failed: {e}", level=LogLevel.ERROR)
        log("Falling back to original query", level=LogLevel.WARN)
        return query, []


async def get_llm_decision(
    client,  # Can be either ClientSession or MultiServerMCPClient
    query: str,
    tools: Optional[List[Any]] = None,
    llm: Optional[Any] = None,
    chat_history: Optional[List[Dict]] = None,
) -> Tuple[Any, List[Dict]]:
    """Get a decision from the LLM based on the query and perception explanation."""
    try:
        # Use provided LLM or fall back to default
        model = llm if llm is not None else default_llm.chat_model

        # Load tools if not provided
        if tools is None:
            log("Loading tools...", level=LogLevel.INFO)
            # Check if we have a ClientSession or MultiServerMCPClient
            if hasattr(client, "get_tools"):
                # It's a MultiServerMCPClient
                tools = await client.get_tools()
            else:
                # It's a ClientSession
                tools = await load_mcp_tools(client)

        log(f"Loaded {len(tools)} available tools", level=LogLevel.DEBUG)

        log("Binding tools to model...", level=LogLevel.DEBUG)
        llm_with_tools = model.bind_tools(tools)

        # Get enhanced query and sub-questions or fall back to original
        enhanced_query, sub_questions = await analyze_query(query, chat_history)

        # Initialize message chain with the user's original query
        messages = [HumanMessage(content=query)]

        # If we have sub-questions from perception, process each one separately
        if sub_questions:
            log(
                f"Processing {len(sub_questions)} sub-questions...", level=LogLevel.INFO
            )

            all_responses = []
            all_tool_names = []

            for i, sub_q in enumerate(sub_questions, 1):
                sub_question = sub_q["sub_question"]
                expected_tool = sub_q["tool"]

                log(
                    f"Processing sub-question {i}/{len(sub_questions)}: {sub_question}",
                    level=LogLevel.INFO,
                )
                log(f"Expected tool: {expected_tool}", level=LogLevel.DEBUG)

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
                    log(
                        f"Found {len(matching_tools)} matching tools for '{expected_tool}'",
                        level=LogLevel.DEBUG,
                    )
                    # If we have a specific tool for this sub-question, bind only that tool
                    specific_tool = matching_tools[0]
                    log(f"Using tool: {specific_tool.name}", level=LogLevel.DEBUG)

                    # Check if the process has tool_args and use them if available
                    if hasattr(sub_q, "tool_args") and sub_q["tool_args"]:
                        log(
                            f"Using tool_args from perception: {sub_q['tool_args']}",
                            level=LogLevel.DEBUG,
                        )
                        # Create a specialized model with the arguments from perception
                        specialized_model = model.bind_tools([specific_tool])
                        sub_response = await specialized_model.ainvoke(
                            sub_question,
                            tool_choice={
                                "name": specific_tool.name,
                                "arguments": json.dumps(sub_q["tool_args"]),
                            },
                        )
                    else:
                        # Create a specialized model with just this tool
                        specialized_model = model.bind_tools([specific_tool])
                        # Process the sub-question with the specialized model
                        sub_response = await specialized_model.ainvoke(sub_question)
                else:
                    log(
                        f"No matching tools found for '{expected_tool}', using all tools",
                        level=LogLevel.WARN,
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
                                log(
                                    f"Found tool call: {tc['name']}",
                                    level=LogLevel.DEBUG,
                                )
                            elif hasattr(tc, "name"):
                                all_tool_names.append(tc.name)
                                log(f"Found tool call: {tc.name}", level=LogLevel.DEBUG)
                            elif (
                                isinstance(tc, dict)
                                and "function" in tc
                                and "name" in tc["function"]
                            ):
                                all_tool_names.append(tc["function"]["name"])
                                log(
                                    f"Found tool call: {tc['function']['name']}",
                                    level=LogLevel.DEBUG,
                                )
                            else:
                                log(
                                    f"Unknown tool call format: {tc}",
                                    level=LogLevel.WARN,
                                )
                                all_tool_names.append("unknown_tool")
                    except Exception as e:
                        log(
                            f"Error extracting tool names for sub-question {i}: {e}",
                            level=LogLevel.ERROR,
                        )
                else:
                    log(
                        f"No tool calls found for sub-question {i}", level=LogLevel.WARN
                    )
                    # If the specialized model didn't generate a tool call, try to create one manually
                    if matching_tools:
                        log(
                            f"Creating manual tool call for {matching_tools[0].name}",
                            level=LogLevel.INFO,
                        )
                        # Create a synthetic tool call
                        if not hasattr(sub_response, "tool_calls"):
                            setattr(sub_response, "tool_calls", [])

                        # First check if we have tool_args from perception
                        if hasattr(sub_q, "tool_args") and sub_q["tool_args"]:
                            log(
                                f"Using tool_args from perception for manual call: {sub_q['tool_args']}",
                                level=LogLevel.DEBUG,
                            )
                            tool_args = sub_q["tool_args"]
                        else:
                            # Create appropriate arguments based on tool type and sub-question
                            tool_args = {}
                            tool_name = matching_tools[0].name

                            if tool_name == "create_gsheet":
                                # For create_gsheet, extract email from sub-question
                                email_match = re.search(
                                    r"[\w\.-]+@[\w\.-]+", sub_question
                                )
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
                                email_match = re.search(
                                    r"[\w\.-]+@[\w\.-]+", sub_question
                                )
                                email = (
                                    email_match.group(0)
                                    if email_match
                                    else "user@example.com"
                                )
                                tool_args = {
                                    "recipient_id": email,
                                    "subject": "Information Requested",
                                    "message": "Here is the information you requested.",
                                }

                        # Add the tool call
                        tool_call = {
                            "name": tool_name,
                            "id": f"manual-tool-call-{i}",
                            "args": tool_args,
                        }
                        sub_response.tool_calls.append(tool_call)
                        all_tool_names.append(tool_name)
                        log(
                            f"Added manual tool call: {tool_name}", level=LogLevel.DEBUG
                        )

            # Create a combined response with all tool calls
            if all_responses:
                log(
                    f"Collecting tool calls from {len(all_responses)} sub-responses",
                    level=LogLevel.INFO,
                )

                # Store all tool calls from all sub-questions in the combined response
                all_tool_calls = []
                for resp in all_responses:
                    if hasattr(resp, "tool_calls") and resp.tool_calls:
                        all_tool_calls.extend(resp.tool_calls)

                log(
                    f"Collected {len(all_tool_calls)} total tool calls",
                    level=LogLevel.INFO,
                )

                # Debug tool calls
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
                    log(f"Tool call {i+1}: {name}", level=LogLevel.DEBUG)

                # Take the last response as the base for our combined response
                combined_response = all_responses[-1] if all_responses else None

                # If we have any tool calls, ensure they're all captured properly
                if all_tool_calls and combined_response:
                    # Set both tool_calls and combined_tool_calls attributes
                    setattr(combined_response, "tool_calls", all_tool_calls)
                    setattr(combined_response, "combined_tool_calls", all_tool_calls)
                elif not all_tool_calls:
                    log(
                        "Warning: No tool calls found in any sub-responses",
                        level=LogLevel.WARN,
                    )

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

                return combined_response, messages
            else:
                log(
                    "No sub-question responses generated, falling back to enhanced query",
                    level=LogLevel.WARN,
                )
                response = await llm_with_tools.ainvoke(enhanced_query)
        else:
            # No sub-questions, process enhanced query directly
            log(
                "No sub-questions available, processing enhanced query directly",
                level=LogLevel.INFO,
            )
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
                            log(f"Unknown tool call format: {tc}", level=LogLevel.WARN)
                            tool_names.append("unknown_tool")
                except Exception as e:
                    log(f"Error extracting tool names: {e}", level=LogLevel.ERROR)
                    tool_names = ["unknown_tool"]

                tools_message = f"I'll help with that by using: {', '.join(tool_names)}"
                messages.append(AIMessage(content=tools_message))
            else:
                content = (
                    response.content
                    if hasattr(response, "content")
                    else "I'll help you with that."
                )
                messages.append(AIMessage(content=content))

        log("Decision making complete", level=LogLevel.INFO)
        return response, messages
    except Exception as e:
        log(f"Error in decision making: {e}", level=LogLevel.ERROR)
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}", [HumanMessage(content=query)]


if __name__ == "__main__":
    log("Testing decision making...", level=LogLevel.INFO)
