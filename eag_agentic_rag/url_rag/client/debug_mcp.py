#!/usr/bin/env python
"""
Debug script to directly test MCP server connection without the entire app stack.
This helps isolate where the "[Errno 9] Bad file descriptor" issue is occurring.
"""

import sys
import os
import asyncio
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


async def test_direct_connection():
    """Test direct connection to MCP server"""
    # Setup server parameters
    server_path = os.path.join(os.getcwd(), "url_rag", "server", "basic_server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        cwd=os.getcwd(),
    )

    print(f"Server path: {server_path}")
    print(f"Exists: {os.path.exists(server_path)}")

    # Try to connect and make a call
    try:
        print("Attempting direct connection to MCP server...")
        async with stdio_client(server_params) as (read, write):
            print("Direct connection established!")
            try:
                async with ClientSession(read, write) as session:
                    print("Session initialized!")

                    # Verify the server is responsive
                    await session.initialize()
                    print("Server initialized!")

                    # Try a simple call
                    print("Making direct web_vector_search call...")
                    try:
                        result = await session.call(
                            "web_vector_search", query="Test query", k="1"
                        )
                        print(f"Direct call successful: {result}")
                    except Exception as e:
                        print(f"Direct call failed: {str(e)}")
                        traceback.print_exc()
            except Exception as session_error:
                print(f"Session error: {session_error}")
                traceback.print_exc()
    except Exception as conn_error:
        print(f"Connection error: {conn_error}")
        traceback.print_exc()


if __name__ == "__main__":
    # Fix for Windows asyncio subprocess
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        print("Starting direct MCP server test...")
        asyncio.run(test_direct_connection())
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
