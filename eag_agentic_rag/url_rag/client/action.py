# Action layer - handles tool execution and response processing

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import List, Dict, Any, Tuple
from langchain_core.messages import ToolMessage, AIMessage


async def process_tool_calls(
    tool_calls: List[Dict], tools: List[Any]
) -> List[ToolMessage]:
    """
    Process tool calls by invoking the appropriate tool with arguments.
    Handles schema validation and nested argument structures.
    If invocation with nested dict fails, fallback to simple dict.

    Args:
        tool_calls: List of tool calls from the LLM response.
        tools: List of available tools.

    Returns:
        List of ToolMessage objects with the results.
    """
    messages = []
    tool_dict = {tool.name: tool for tool in tools}
    print(f"Tool dict: {tool_dict}")
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_id = tool_call.get("id")
        tool_args = tool_call.get("args", {})
        print(f"\nProcessing tool call: {tool_name} (id: {tool_id})")
        if tool_name not in tool_dict:
            print(f"Tool {tool_name} not found in available tools")
            messages.append(
                ToolMessage(
                    content=f"Tool {tool_name} not found.", tool_call_id=tool_id
                )
            )
            continue

        selected_tool = tool_dict[tool_name]

        # More comprehensive debugging
        print("\n----- FULL STACK DEBUG START -----")
        print(f"Tool type: {type(selected_tool).__name__}")
        print(f"Tool name: {selected_tool.name}")
        print(
            f"Tool attributes: {[attr for attr in dir(selected_tool) if not attr.startswith('_')]}"
        )

        # Print all tool properties that can be accessed
        for attr in dir(selected_tool):
            if not attr.startswith("_") and attr not in (
                "ainvoke",
                "invoke",
                "coroutine",
            ):
                try:
                    val = getattr(selected_tool, attr)
                    if not callable(val):
                        print(f"Tool.{attr} = {val}")
                except Exception as e:
                    print(f"Couldn't access {attr}: {e}")

        if hasattr(selected_tool, "coroutine"):
            print(f"Coroutine: {selected_tool.coroutine}")

        # Try direct connection to MCP
        print("\nAttempting direct MCP connection debug:")
        try:
            from mcp.client.stdio import stdio_client
            from mcp import ClientSession, StdioServerParameters
            import sys

            # Get the server path from client.py
            server_path = os.path.join(
                os.getcwd(), "url_rag", "server", "basic_server.py"
            )
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_path],
                cwd=os.getcwd(),
            )

            print(f"Server path: {server_path}")
            print(f"Exists: {os.path.exists(server_path)}")

            # Test a direct connection
            async def test_direct_connection():
                async with stdio_client(server_params) as (read, write):
                    print("Direct connection established!")
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        print("Session initialized directly!")
                        # Try a simple call
                        try:
                            result = await session.call(
                                "web_vector_search", query="Test query", k="1"
                            )
                            print(f"Direct call successful: {result}")
                        except Exception as e:
                            print(f"Direct call failed: {str(e)}")
                            import traceback

                            traceback.print_exc()

            try:
                # We can't await here directly, so just log the fact we would try this
                print(
                    "Would attempt direct connection (code available but commented out)"
                )
                # Uncomment the next line for direct testing, but it may cause issues in the current flow
                # await test_direct_connection()
            except Exception as e:
                print(f"Direct connection attempt failed: {str(e)}")
                import traceback

                traceback.print_exc()

        except Exception as e:
            print(f"Setup for direct debugging failed: {str(e)}")
            import traceback

            traceback.print_exc()

        print("----- FULL STACK DEBUG END -----\n")

        # Continue with the original hardcoded debug tests
        print("\n----- DEBUG TOOL START -----")
        print(f"Testing tool {tool_name} with hardcoded input")
        try:
            # Debug: First try standard method with 'input' parameter
            print("Method 1: Using standard ainvoke with input parameter")
            debug_input = {"query": "What is Docker?", "k": "1"}

            # Add extra error handling and stack trace
            try:
                print(f"About to call ainvoke with input={debug_input}")
                debug_output = await selected_tool.ainvoke(input=debug_input)
                print(f"SUCCESS - Method 1 output: {debug_output}")
            except Exception as detailed_e:
                import traceback

                print(f"Detailed error in Method 1: {detailed_e}")
                print("Stack trace:")
                traceback.print_exc()
                raise  # Re-raise to be caught by outer try/except

        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            try:
                # Debug: Try accessing coroutine directly
                print("Method 2: Try accessing coroutine directly")
                if hasattr(selected_tool, "coroutine"):
                    # Add extra error handling and stack trace
                    try:
                        print("About to call coroutine directly")
                        debug_output = await selected_tool.coroutine(
                            query="What is Docker?", k="1"
                        )
                        print(f"SUCCESS - Method 2 output: {debug_output}")
                    except Exception as detailed_e:
                        import traceback

                        print(f"Detailed error in Method 2: {detailed_e}")
                        print("Stack trace:")
                        traceback.print_exc()
                        raise  # Re-raise to be caught by outer try/except
                else:
                    print("Method 2 skipped: No coroutine attribute")
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                print("All debug methods failed")
        print("----- DEBUG TOOL END -----\n")

        print(f"Executing tool: {tool_name}")
        print(f"Selected tool: {selected_tool}")

        # Print original tool args
        print(f"Original tool args: {tool_args}")

        # Handle schema if present
        tool_schema = getattr(selected_tool, "args_schema", None)
        if tool_schema is not None:
            schema_name = getattr(tool_schema, "__name__", type(tool_schema).__name__)
            print(f"Tool schema found: {schema_name} with type {type(tool_schema)}")

        try:
            # First check if this is a simple dict that can be passed directly
            if isinstance(tool_args, dict):
                # If it's a nested dict, get the innermost dict
                if "request" in tool_args and isinstance(tool_args["request"], dict):
                    # Extract the inner request parameters
                    inner_args = tool_args["request"]
                    print(f"Using inner request args: {inner_args}")
                    args_to_use = inner_args
                else:
                    # Use the original args if not nested
                    print(f"Using original args: {tool_args}")
                    args_to_use = tool_args

                print(f"Calling tool {tool_name} with args: {args_to_use}")

                # Use correct invocation for LangChain's StructuredTool
                if hasattr(selected_tool, "ainvoke"):
                    print(f"Ainvoke found for tool: {tool_name}")
                    # LangChain's StructuredTool.ainvoke requires 'input' parameter
                    tool_output = await selected_tool.ainvoke(input=args_to_use)
                else:
                    print(f"Invoke found for tool: {tool_name}")
                    # For synchronous tools
                    tool_output = selected_tool.invoke(input=args_to_use)

                messages.append(AIMessage(content=tool_output))
            else:
                # Handle non-dict case
                print(f"Non-dict args: {tool_args}")
                if hasattr(selected_tool, "ainvoke"):
                    tool_output = await selected_tool.ainvoke(tool_args)
                else:
                    tool_output = selected_tool.invoke(tool_args)
                messages.append(AIMessage(content=tool_output))
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {e}"
            print(error_msg)
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
            print(f"Processing {response.tool_calls} tool call(s)...")
            print(f"Tools: {tools}")

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
