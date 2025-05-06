#!/usr/bin/env python
"""
Simple test script to directly test the alternative server implementation.
This is a focused script for debugging the '[Errno 9] Bad file descriptor' issue.
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


async def test_alternative_server():
    """
    Test the alternative server implementation directly.
    """
    print("Testing alternative server implementation...")

    # Use the alternative server implementation
    server_path = os.path.join(
        os.getcwd(), "url_rag", "server", "alternative_server.py"
    )
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        cwd=os.getcwd(),
    )

    print(f"Server path: {server_path}")
    print(f"Exists: {os.path.exists(server_path)}")

    try:
        print("Connecting to alternative server...")
        async with stdio_client(server_params) as (read, write):
            print("Connected to server.")

            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                print("Session initialized.")

                # Try a direct tool call
                print("Calling web_vector_search directly...")
                response = await session.call(
                    "web_vector_search", query="What is Docker?", k="1"
                )
                print(f"Response from direct call: {response}")

                # If that worked, we can test the LangChain adapter
                try:
                    from langchain_mcp_adapters.tools import load_mcp_tools

                    print("Loading tools via LangChain adapter...")
                    tools = await load_mcp_tools(session)
                    print(f"Loaded tools: {tools}")

                    if tools:
                        tool = tools[0]  # Should be web_vector_search
                        print(f"Testing LangChain tool: {tool.name}")

                        # Try invoking the tool through LangChain
                        print("Invoking tool through LangChain...")
                        result = await tool.ainvoke(
                            input={"query": "What is Docker?", "k": "1"}
                        )
                        print(f"LangChain tool result: {result}")
                except Exception as lc_error:
                    print(f"LangChain adapter error: {lc_error}")
                    import traceback

                    traceback.print_exc()

    except Exception as e:
        print(f"Error testing alternative server: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Fix for Windows asyncio subprocess
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    print("Starting alternative server test...")
    asyncio.run(test_alternative_server())
