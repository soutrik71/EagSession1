import asyncio
import os
import sys
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

# Get the absolute path to the server script
server_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "basic_server.py")
)


async def test_stdio_transport():
    """Test stdio transport with comprehensive error handling."""

    print(f"Server script path: {server_script_path}")
    print("Attempting stdio transport connection...")

    # Try different Python command variations for Windows compatibility
    python_commands = ["python", "python.exe", sys.executable]

    for python_cmd in python_commands:
        print(f"\nTrying with Python command: {python_cmd}")

        try:
            # Create explicit transport
            transport = PythonStdioTransport(
                script_path=server_script_path,
                python_cmd=python_cmd,
            )

            # Create client with explicit transport
            client = Client(transport)

            # Test connection with timeout
            async with client:
                print(f"✅ Connected successfully with {python_cmd}!")
                print(f"Client connected: {client.is_connected()}")

                # Quick test
                tools = await client.list_tools()
                print(f"Available tools: {[tool.name for tool in tools]}")

                if tools:
                    result = await client.call_tool("add", {"a": 1, "b": 2})
                    print(f"Test result: {result}")

                return True  # Success

        except Exception as e:
            print(f"❌ Failed with {python_cmd}: {e}")
            continue

    print("\n❌ All stdio transport attempts failed.")
    return False


async def test_in_memory_fallback():
    """Fallback to in-memory transport."""

    print("\n🔄 Falling back to in-memory transport...")

    try:
        # Import server instance for in-memory transport
        from basic_server import mcp as server_instance

        client = Client(server_instance)

        async with client:
            print("✅ In-memory transport connected successfully!")

            # Full test
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            # Test tools
            add_result = await client.call_tool("add", {"a": 1, "b": 2})
            print(f"Add result: {add_result}")

            # Test resources
            version = await client.read_resource("config://version")
            print(f"Version: {version}")

            return True

    except Exception as e:
        print(f"❌ In-memory transport also failed: {e}")
        return False


async def main():
    """Main function that tries stdio first, then falls back to in-memory."""

    print("FastMCP Client Test - Stdio with In-Memory Fallback")
    print("=" * 50)

    # Try stdio transport first
    stdio_success = await test_stdio_transport()

    if not stdio_success:
        # Fall back to in-memory transport
        inmemory_success = await test_in_memory_fallback()

        if not inmemory_success:
            print("\n❌ Both transport methods failed!")
            return

    print("\n✅ FastMCP client test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
