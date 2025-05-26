import asyncio
import os
from fastmcp import Client

# Import the server instance from basic_server
from basic_server import mcp as server_instance


async def main():
    """Main function using in-memory transport for reliable connection."""

    print("Using in-memory transport for reliable FastMCP connection...")

    # Create client pointing directly to the server instance (in-memory transport)
    # This is the recommended approach from FastMCP documentation for testing and development
    client = Client(server_instance)

    try:
        # Connection is established here and managed by the context manager
        async with client:
            print(f"Client connected: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            # Test each tool
            print("\n--- Testing Tools ---")

            if any(tool.name == "add" for tool in tools):
                add_result = await client.call_tool("add", {"a": 1, "b": 2})
                print(f"Add result: {add_result[0].text}")

            if any(tool.name == "subtract" for tool in tools):
                subtract_result = await client.call_tool("subtract", {"a": 5, "b": 3})
                print(f"Subtract result: {subtract_result[0].text}")

            if any(tool.name == "multiply" for tool in tools):
                multiply_result = await client.call_tool("multiply", {"a": 4, "b": 3})
                print(f"Multiply result: {multiply_result[0].text}")

            if any(tool.name == "divide" for tool in tools):
                divide_result = await client.call_tool("divide", {"a": 10, "b": 2})
                print(f"Divide result: {divide_result[0].text}")

            # Test resources
            print("\n--- Testing Resources ---")

            try:
                version = await client.read_resource("config://version")
                print(f"Version: {version}")
            except Exception as e:
                print(f"Error reading version resource: {e}")

            try:
                profile = await client.read_resource("users://1/profile")
                print(f"Profile: {profile}")
            except Exception as e:
                print(f"Error reading profile resource: {e}")

            # Test prompts
            print("\n--- Testing Prompts ---")

            try:
                prompts = await client.list_prompts()
                print(f"Available prompts: {[prompt.name for prompt in prompts]}")

                if prompts:
                    prompt_result = await client.get_prompt(
                        "summarize_request", {"text": "This is a test text."}
                    )
                    print(f"Prompt result: {prompt_result}")
            except Exception as e:
                print(f"Error testing prompts: {e}")

        # Connection is closed automatically here
        print(f"\nClient connected after context: {client.is_connected()}")
        print("✅ FastMCP client-server communication successful!")

    except Exception as e:
        print(f"Error during client operation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
