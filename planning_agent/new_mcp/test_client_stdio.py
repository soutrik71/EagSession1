from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
import os
import sys

server_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "tools_server_extended_stdio.py")
)
# Option 1: Inferred transport - issue with windows
# client = Client(server_script_path)

# Option 2: Explicit transport with custom configuration
python_commands = ["python", "python.exe", sys.executable]

for python_cmd in python_commands:
    print(f"\nTrying with Python command: {python_cmd}")

    try:
        transport = PythonStdioTransport(
            script_path=server_script_path,
            python_cmd=python_cmd,
        )
        client = Client(transport=transport)
        print(client.transport)
        print("Connected successfully")
        break
    except Exception as e:
        print(f"Error with Python command {python_cmd}: {e}")
        continue


async def main():
    # Connection is established here
    async with client:
        print(f"Client connected: {client.is_connected()}")

        # Make MCP calls within the context
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        if any(tool.name == "reverse_string" for tool in tools):
            result = await client.call_tool("reverse_string", {"text": "Hello, World!"})
            print(f"Reverse string result: {result}")

    # Connection is closed automatically here
    print(f"Client connected: {client.is_connected()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
