# Action layer - handles tool execution and response processing

import sys
import os

# Add the parent directory (eag_agentic_rag) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

from typing import List, Dict, Any, Tuple
from langchain_core.messages import ToolMessage, AIMessage


async def process_tool_calls(
    tool_calls: List[Dict], tools: List[Any]
) -> List[AIMessage]:
    """
    Process tool calls by invoking the appropriate tool with arguments.
    Handles schema validation and nested argument structures.

    Args:
        tool_calls: List of tool calls from the LLM response.
        tools: List of available tools.

    Returns:
        List of ToolMessage objects with the results.
    """
    messages = []
    tool_dict = {tool.name: tool for tool in tools}

    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_id = tool_call.get("id")
        tool_args = tool_call.get("args", {})

        if tool_name not in tool_dict:
            messages.append(
                ToolMessage(
                    content=f"Tool {tool_name} not found.", tool_call_id=tool_id
                )
            )
            continue

        selected_tool = tool_dict[tool_name]

        try:
            # The MCP tool expects arguments in an "input_data" structure
            if isinstance(tool_args, dict):
                # Structure args correctly for MCP tools
                if "input_data" not in tool_args:
                    # Wrap args in input_data if not already present
                    args_to_use = {"input_data": tool_args}
                else:
                    args_to_use = tool_args

                # Use correct invocation method based on tool type
                if hasattr(selected_tool, "ainvoke"):
                    tool_output = await selected_tool.ainvoke(input=args_to_use)
                else:
                    tool_output = selected_tool.invoke(input=args_to_use)

                messages.append(AIMessage(content=tool_output))
            else:
                # Handle non-dict case
                if hasattr(selected_tool, "ainvoke"):
                    tool_output = await selected_tool.ainvoke(tool_args)
                else:
                    tool_output = selected_tool.invoke(tool_args)
                messages.append(AIMessage(content=tool_output))

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {e}"
            messages.append(AIMessage(content=error_msg))

    return messages


async def execute_actions(
    response: Any,
    messages: List[Any],
    tools: List[Any],
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
        # Check if response has tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
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


if __name__ == "__main__":
    print("Testing action execution...")
    from url_rag.client.llm_provider import default_llm
    from url_rag.client.utils import read_yaml_file
    from url_rag.client.embedding_provider import OpenAIEmbeddingProvider
    from url_rag.client.memory import ConversationMemory
    import uuid
