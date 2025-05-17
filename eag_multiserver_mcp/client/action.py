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

    # Also create a more flexible dictionary for matching similar tool names
    flexible_tool_dict = {}
    for tool in tools:
        flexible_tool_dict[tool.name.lower()] = tool
        # Add common aliases
        if "search" in tool.name.lower() or "web" in tool.name.lower():
            flexible_tool_dict["websearch"] = tool
        if "sheet" in tool.name.lower() or "gsuite" in tool.name.lower():
            flexible_tool_dict["gsuite"] = tool
        if "email" in tool.name.lower() or "gmail" in tool.name.lower():
            flexible_tool_dict["gmail"] = tool

    print(
        f"Processing {len(tool_calls)} tool call(s) with {len(tools)} available tools"
    )
    print(f"Available tools: {', '.join(tool_dict.keys())}")

    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call.get("name", "")
        tool_id = tool_call.get("id", f"tool-{i}")
        tool_args = tool_call.get("args", {})

        print(f"Tool call {i}/{len(tool_calls)}: '{tool_name}'")

        # First try exact match
        if tool_name in tool_dict:
            selected_tool = tool_dict[tool_name]
        # Then try lowercase match
        elif tool_name.lower() in flexible_tool_dict:
            selected_tool = flexible_tool_dict[tool_name.lower()]
            print(f"Using flexible match: {tool_name} -> {selected_tool.name}")
        else:
            error_msg = f"Tool {tool_name} not found in available tools."
            print(error_msg)
            print(f"Available tools: {', '.join(tool_dict.keys())}")
            messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
            continue

        print(f"Found tool '{selected_tool.name}', executing with args: {tool_args}")

        try:
            if isinstance(tool_args, dict):
                # Special handling for specific tools
                if (
                    selected_tool.name == "create_gsheet"
                    and "email_id" not in tool_args
                ):
                    # Extract email from tool args or use default
                    import re

                    email = None
                    for val in tool_args.values():
                        if isinstance(val, str):
                            email_match = re.search(r"[\w\.-]+@[\w\.-]+", val)
                            if email_match:
                                email = email_match.group(0)
                                break

                    if not email:
                        # Check if there's an email in any of the messages
                        for msg in messages:
                            if hasattr(msg, "content") and isinstance(msg.content, str):
                                email_match = re.search(
                                    r"[\w\.-]+@[\w\.-]+", msg.content
                                )
                                if email_match:
                                    email = email_match.group(0)
                                    break

                    if email:
                        print(f"Found email: {email} for create_gsheet")
                        tool_args = {"email_id": email}
                    else:
                        print("No email found, using default")
                        tool_args = {"email_id": "user@example.com"}

                # Structure args correctly based on schema type
                if is_pydantic_schema and "input_data" not in tool_args:
                    # For Pydantic schema tools, wrap in input_data if not already present
                    args_to_use = {"input_data": tool_args}
                    print(f"Using Pydantic schema format: {args_to_use}")
                else:
                    # For non-Pydantic tools, use tool_args directly
                    args_to_use = tool_args
                    print(f"Using direct args format: {args_to_use}")

                # Use correct invocation method based on tool type
                if hasattr(selected_tool, "ainvoke"):
                    print(f"Invoking async tool '{selected_tool.name}'")
                    tool_output = await selected_tool.ainvoke(input=args_to_use)
                else:
                    print(f"Invoking sync tool '{selected_tool.name}'")
                    tool_output = selected_tool.invoke(input=args_to_use)

                print(f"Tool '{selected_tool.name}' executed successfully")
                print(f"Tool output: {tool_output[:200]}...")
                messages.append(AIMessage(content=tool_output))
            else:
                # Handle non-dict case
                print(f"Tool args is not a dict: {type(tool_args)}")
                if hasattr(selected_tool, "ainvoke"):
                    tool_output = await selected_tool.ainvoke(tool_args)
                else:
                    tool_output = selected_tool.invoke(tool_args)
                messages.append(AIMessage(content=tool_output))

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {e}"
            print(f"ERROR: {error_msg}")
            import traceback

            traceback.print_exc()
            messages.append(AIMessage(content=error_msg))

    return messages


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

            # Print detailed information about tool calls
            print(
                f"Execute_actions: Processing {len(tool_calls_to_process)} tool call(s)..."
            )
            for i, tc in enumerate(tool_calls_to_process):
                if isinstance(tc, dict) and "name" in tc:
                    print(f"  Tool {i+1}: {tc['name']}")
                elif hasattr(tc, "name"):
                    print(f"  Tool {i+1}: {tc.name}")
                else:
                    print(f"  Tool {i+1}: unknown format {type(tc)}")

            # Process tool calls
            tool_messages = await process_tool_calls(
                tool_calls_to_process, tools, is_pydantic_schema
            )
            messages.extend(tool_messages)

            # Summarize the tool executions
            tool_names = []
            for tc in tool_calls_to_process:
                if isinstance(tc, dict) and "name" in tc:
                    tool_names.append(tc["name"])
                elif hasattr(tc, "name"):
                    tool_names.append(tc.name)
                else:
                    tool_names.append("unknown_tool")

            print(f"Executed tools: {', '.join(tool_names)}")
        else:
            print("No tool calls to execute")

        return response, messages
    except Exception as e:
        print(f"Error in action execution: {e}")
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
    print("\nProcessed messages chain:")
    for i, msg in enumerate(messages, 1):
        msg_type = type(msg).__name__
        msg_preview = msg.content
        print(f"{i}. {msg_type}: {msg_preview}")

        # Print tool calls if present
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"   Tool calls: {[tc['name'] for tc in msg.tool_calls]}")


if __name__ == "__main__":
    print("Testing action execution...")
