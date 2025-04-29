# Action layer - handles tool execution and response processing
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.messages import ToolMessage, AIMessage


async def process_tool_calls(
    tool_calls: List[Dict], tools: List[Any]
) -> List[ToolMessage]:
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
            print(f"Executing tool: {tool_call['name']}")
            tool_output = await selected_tool.ainvoke(tool_call["args"])
            messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )
        else:
            print(f"Tool {tool_call['name']} not found in available tools")

    return messages


async def execute_actions(
    response: Any, messages: List[Any], tools: List[Any], llm: Optional[Any] = None
) -> Tuple[Any, List[Any]]:
    """Execute any tool calls in the response and update the message chain.

    Args:
        response: The LLM response
        messages: The existing message chain
        tools: The available tools
        llm: Optional LLM instance (not used in this simplified version)

    Returns:
        Updated tuple of (response, messages)
    """
    try:
        if response.tool_calls:
            # Handle tool calls
            print(f"Processing {len(response.tool_calls)} tool call(s)...")
            tool_messages = await process_tool_calls(response.tool_calls, tools)
            messages.extend(tool_messages)

            # Summarize the tool executions
            tool_names = [tc["name"] for tc in response.tool_calls]
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
