import asyncio
from fastmcp import FastMCP, Client

# Create FastMCP server instance
mcp = FastMCP("basic_server")


@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


@mcp.tool()
async def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b


@mcp.tool()
async def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
async def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    return a / b


# Static resource
@mcp.resource("config://version")
def get_version():
    """Get the server version"""
    return "2.0.1"


# Dynamic resource template
@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: int):
    """Get user profile by ID"""
    return {"name": f"User {user_id}", "status": "active"}


@mcp.prompt()
def summarize_request(text: str) -> str:
    """Generate a prompt asking for a summary."""
    return f"Please summarize the following text:\n\n{text}"


async def main():
    """Test using in-memory transport as recommended in FastMCP docs."""

    # Create client pointing directly to the server instance (in-memory transport)
    client = Client(mcp)

    try:
        async with client:
            print("Connected to server successfully using in-memory transport!")
            print(f"Client connected: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            # Test each tool
            print("\n--- Testing Tools ---")

            add_result = await client.call_tool("add", {"a": 1, "b": 2})
            print(f"Add result: {add_result}")

            subtract_result = await client.call_tool("subtract", {"a": 5, "b": 3})
            print(f"Subtract result: {subtract_result}")

            multiply_result = await client.call_tool("multiply", {"a": 4, "b": 3})
            print(f"Multiply result: {multiply_result}")

            divide_result = await client.call_tool("divide", {"a": 10, "b": 2})
            print(f"Divide result: {divide_result}")

            # Test resources
            print("\n--- Testing Resources ---")

            version = await client.read_resource("config://version")
            print(f"Version: {version}")

            profile = await client.read_resource("users://1/profile")
            print(f"Profile: {profile}")

            # Test prompts
            print("\n--- Testing Prompts ---")

            prompts = await client.list_prompts()
            print(f"Available prompts: {[prompt.name for prompt in prompts]}")

            if prompts:
                prompt_result = await client.get_prompt(
                    "summarize_request", {"text": "This is a test text."}
                )
                print(f"Prompt result: {prompt_result}")

        print(f"\nClient connected after context: {client.is_connected()}")

    except Exception as e:
        print(f"Error during client operation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
