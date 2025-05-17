# Action layer - handles tool execution and response processing

import sys
import os

# Add the parent directory (eag_agentic_rag) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Add the current path and project root to the Python path to enable module imports
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

from typing import List, Dict, Any, Tuple
from langchain_core.messages import ToolMessage, AIMessage
import re

# Import utils for logging
from client.utils import log, LogLevel

# Tool name mapping to handle different naming conventions
TOOL_NAME_MAPPING = {
    "websearch": ["search_web", "search", "web", "websearch"],
    "gsuite": ["create_gsheet", "gsheet", "sheet", "google_sheet", "spreadsheet"],
    "gmail": ["send_email", "email", "mail", "gmail"],
}


async def process_tool_calls(
    tool_calls: List[Dict], tools: List[Any], is_pydantic_schema: bool = False
) -> List[AIMessage]:
    """
    Process tool calls by invoking the appropriate tool with arguments.
    Handles schema validation and nested argument structures.

    Args:
        tool_calls: List of tool calls from the LLM response.
        tools: List of available tools.
        is_pydantic_schema: Whether to wrap tool arguments in input_data structure.

    Returns:
        List of ToolMessage objects with the results.
    """
    messages = []
    tool_dict = {tool.name: tool for tool in tools}

    # Create a flexible tool dictionary for matching
    flexible_tool_dict = {}
    for tool in tools:
        flexible_tool_dict[tool.name.lower()] = tool
        # Add common aliases
        for canonical, aliases in TOOL_NAME_MAPPING.items():
            if any(alias in tool.name.lower() for alias in aliases):
                for alias in aliases:
                    flexible_tool_dict[alias.lower()] = tool

    log(
        "Processing {len(tool_calls)} tool call(s) with {len(tools)} available tools",
        level=LogLevel.INFO,
    )
    log("Available tools: {', '.join(tool_dict.keys())}", level=LogLevel.DEBUG)

    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call.get("name", "")
        tool_id = tool_call.get("id", f"tool-{i}")
        tool_args = tool_call.get("args", {})

        log(f"Tool call {i}/{len(tool_calls)}: '{tool_name}'", level=LogLevel.INFO)

        # Find the appropriate tool
        selected_tool = None

        # Exact match
        if tool_name in tool_dict:
            selected_tool = tool_dict[tool_name]
        # Flexible match
        elif tool_name.lower() in flexible_tool_dict:
            selected_tool = flexible_tool_dict[tool_name.lower()]
            log(
                f"Using flexible match: {tool_name} -> {selected_tool.name}",
                level=LogLevel.DEBUG,
            )

        if not selected_tool:
            error_msg = f"Tool {tool_name} not found in available tools."
            log(error_msg, level=LogLevel.ERROR)
            messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
            continue

        log(
            f"Found tool '{selected_tool.name}', executing with args: {tool_args}",
            level=LogLevel.DEBUG,
        )

        try:
            if isinstance(tool_args, dict):
                # Special handling for specific tools
                if (
                    selected_tool.name == "create_gsheet"
                    and "email_id" not in tool_args
                ):
                    # Extract email from tool args or use default
                    email = find_email_in_content(tool_args, messages)
                    if email:
                        log(
                            f"Found email for create_gsheet: {email}",
                            level=LogLevel.DEBUG,
                        )
                        tool_args = {"email_id": email}
                    else:
                        log("No email found, using default", level=LogLevel.WARN)
                        tool_args = {"email_id": "user@example.com"}

                # Structure args correctly based on schema type
                if is_pydantic_schema and "input_data" not in tool_args:
                    args_to_use = {"input_data": tool_args}
                    log("Using Pydantic schema format", level=LogLevel.DEBUG)
                else:
                    args_to_use = tool_args

                # Invoke the tool
                if hasattr(selected_tool, "ainvoke"):
                    log(
                        f"Invoking async tool '{selected_tool.name}'",
                        level=LogLevel.DEBUG,
                    )
                    tool_output = await selected_tool.ainvoke(input=args_to_use)
                else:
                    log(
                        f"Invoking sync tool '{selected_tool.name}'",
                        level=LogLevel.DEBUG,
                    )
                    tool_output = selected_tool.invoke(input=args_to_use)

                log(
                    f"Tool '{selected_tool.name}' executed successfully",
                    level=LogLevel.INFO,
                )

                # Only show part of the output in the logs to avoid verbosity
                if isinstance(tool_output, str) and len(tool_output) > 200:
                    log(
                        f"Tool output preview: {tool_output[:150]}...",
                        level=LogLevel.DEBUG,
                    )

                messages.append(AIMessage(content=tool_output))
            else:
                # Handle non-dict case with less verbosity
                if hasattr(selected_tool, "ainvoke"):
                    tool_output = await selected_tool.ainvoke(tool_args)
                else:
                    tool_output = selected_tool.invoke(tool_args)
                messages.append(AIMessage(content=tool_output))

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {e}"
            log(error_msg, level=LogLevel.ERROR)
            import traceback

            traceback.print_exc()
            messages.append(AIMessage(content=error_msg))

    return messages


def find_email_in_content(data, messages=None):
    """Helper function to extract email from content"""
    # First check in the data dictionary values
    if isinstance(data, dict):
        for val in data.values():
            if isinstance(val, str):
                email_match = re.search(r"[\w\.-]+@[\w\.-]+", val)
                if email_match:
                    return email_match.group(0)

    # Then check in the message content if provided
    if messages:
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                email_match = re.search(r"[\w\.-]+@[\w\.-]+", msg.content)
                if email_match:
                    return email_match.group(0)

    return None


async def execute_actions(
    response: Any,
    messages: List[Any],
    tools: List[Any],
    client=None,
    is_pydantic_schema: bool = False,
) -> Tuple[Any, List[Any]]:
    """Execute any tool calls in the response and update the message chain.

    Args:
        response: The LLM response
        messages: The existing message chain
        tools: The available tools
        client: Optional MCP client (MultiServerMCPClient or ClientSession instance)
        is_pydantic_schema: Whether to wrap tool arguments in input_data structure

    Returns:
        Updated tuple of (response, messages)
    """
    try:
        # Check if response has tool calls (either regular or combined from sub-questions)
        has_tool_calls = (hasattr(response, "tool_calls") and response.tool_calls) or (
            hasattr(response, "combined_tool_calls") and response.combined_tool_calls
        )

        if has_tool_calls:
            # Get the tool calls to process (prefer combined_tool_calls if available)
            tool_calls_to_process = (
                response.combined_tool_calls
                if hasattr(response, "combined_tool_calls")
                and response.combined_tool_calls
                else response.tool_calls
            )

            # Process tool calls
            log(
                f"Executing {len(tool_calls_to_process)} tool call(s)",
                level=LogLevel.INFO,
            )
            tool_messages = await process_tool_calls(
                tool_calls_to_process, tools, is_pydantic_schema
            )
            messages.extend(tool_messages)

            # Log executed tools
            tool_names = []
            for tc in tool_calls_to_process:
                if isinstance(tc, dict) and "name" in tc:
                    tool_names.append(tc["name"])
                elif hasattr(tc, "name"):
                    tool_names.append(tc.name)
                else:
                    tool_names.append("unknown_tool")

            log(f"Executed tools: {', '.join(tool_names)}", level=LogLevel.INFO)
        else:
            log("No tool calls to execute", level=LogLevel.INFO)

        return response, messages
    except Exception as e:
        log(f"Error in action execution: {e}", level=LogLevel.ERROR)
        import traceback

        traceback.print_exc()

        # Add an error message to the chain
        error_msg = f"Error executing actions: {str(e)}"
        messages.append(AIMessage(content=error_msg))

        return response, messages


def print_message_chain(messages: List[Any]) -> None:
    """Print a formatted version of the message chain.

    Args:
        messages: List of message objects
    """
    log("Processed messages chain:", level=LogLevel.INFO)
    for i, msg in enumerate(messages, 1):
        msg_type = type(msg).__name__
        # Truncate long content for readability
        if hasattr(msg, "content"):
            content_preview = (
                msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            )
        else:
            content_preview = (
                str(msg)[:100] + "..." if len(str(msg)) > 100 else str(msg)
            )

        log(f"{i}. {msg_type}: {content_preview}", level=LogLevel.INFO)

        # Print tool calls if present
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_names = [
                (
                    tc.get("name", "unknown")
                    if isinstance(tc, dict)
                    else getattr(tc, "name", "unknown")
                )
                for tc in msg.tool_calls
            ]
            log(f"   Tool calls: {tool_names}", level=LogLevel.DEBUG)


if __name__ == "__main__":
    log("Testing action execution...", level=LogLevel.INFO)
