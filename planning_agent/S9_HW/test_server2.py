#!/usr/bin/env python3
"""
Test script for server2.py (Web Tools Server) only
"""

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
import asyncio
import os
import sys
import logging
import json

# Set up logging to capture context messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Create a logger for MCP context messages
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)

# Disable SSL verification for local testing
os.environ.pop("SSL_CERT_FILE", None)

server_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "server2.py")
)

# Try multiple Python commands like in test_client_stdio.py
python_commands = ["python", "python.exe", sys.executable]

client = None
successful_python_cmd = None

for python_cmd in python_commands:
    print(f"\n🔍 Trying Python command: {python_cmd}")

    try:
        transport = PythonStdioTransport(
            script_path=server_script_path,
            python_cmd=python_cmd,
        )
        client = Client(transport=transport)
        print(f"✅ Transport created successfully: {client.transport}")
        successful_python_cmd = python_cmd
        break
    except Exception as e:
        print(f"❌ Error with Python command {python_cmd}: {e}")
        continue

if not client:
    print("❌ Failed to create client with any Python command")
    sys.exit(1)


def parse_result(result_text):
    """Parse JSON result and extract the result value or return full JSON for complex responses"""
    try:
        data = json.loads(result_text)
        return data
    except (json.JSONDecodeError, AttributeError):
        return result_text


async def test_server2():
    """Test server2.py web tools functions"""
    print("\n🌐 Testing Web Tools Server (server2.py)")
    print("=" * 50)

    async with client:
        print(f"✅ Connected to server2: {client.is_connected()}")

        # List available tools
        tools = await client.list_tools()
        print(f"📋 Available tools ({len(tools)}):")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")

        print("\n🔍 Testing Web Search:")

        # Test basic web search
        try:
            result = await client.call_tool(
                "search_web",
                {"input": {"query": "Python programming", "max_results": 3}},
            )
            parsed_result = parse_result(result[0].text)

            if parsed_result.get("success", False):
                results_text = parsed_result.get("results", "")
                print("✅ Web search successful")
                print("   Query: 'Python programming'")
                print(f"   Results length: {len(results_text)} characters")
                if results_text:
                    preview = results_text.split("\n")[0][:80]
                    print(f"   Preview: {preview}...")
            else:
                error_msg = parsed_result.get("error_message", "Unknown error")
                print(f"❌ Web search failed: {error_msg}")

        except Exception as e:
            print(f"❌ search_web failed: {e}")

        print("\n📄 Testing Webpage Fetch:")

        # Test basic webpage fetch
        try:
            result = await client.call_tool(
                "fetch_webpage",
                {"input": {"url": "https://httpbin.org/html", "max_length": 500}},
            )
            parsed_result = parse_result(result[0].text)

            if parsed_result.get("success", False):
                content = parsed_result.get("content", "")
                print("✅ Webpage fetch successful")
                print("   URL: https://httpbin.org/html")
                print(f"   Content length: {len(content)} characters")
                if content:
                    preview = content.strip()[:60].replace("\n", " ")
                    print(f"   Preview: {preview}...")
            else:
                error_msg = parsed_result.get("error_message", "Unknown error")
                print(f"❌ Webpage fetch failed: {error_msg}")

        except Exception as e:
            print(f"❌ fetch_webpage failed: {e}")

        print("\n🚫 Testing Error Handling:")

        # Test invalid URL
        try:
            result = await client.call_tool(
                "fetch_webpage", {"input": {"url": "invalid-url", "max_length": 500}}
            )
            parsed_result = parse_result(result[0].text)

            if not parsed_result.get("success", True):
                print("✅ Invalid URL correctly handled")
            else:
                print("⚠️  Expected error but got success")

        except Exception as e:
            print(f"✅ Invalid URL correctly caught: {type(e).__name__}")

    print(f"\n✅ Client disconnected: {not client.is_connected()}")


if __name__ == "__main__":
    print("🌟 Testing Server2 (Web Tools) Independently")
    print(f"🔗 Using Python command: {successful_python_cmd}")
    print(f"📁 Server script: {server_script_path}")
    print("=" * 50)

    try:
        asyncio.run(test_server2())
        print("\n✅ Server2 test completed!")
        print("\n📊 Test Summary:")
        print("   🔍 Web Search: DuckDuckGo search test")
        print("   📄 Webpage Fetch: HTML content extraction test")
        print("   🚫 Error Handling: Invalid URL test")
    except Exception as e:
        print(f"\n❌ Server2 test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if server2.py exists and is executable")
        print("   2. Check internet connection for web operations")
        print("   3. Verify tool_utils/web_tools.py exists")
        print(f"   4. Try: {successful_python_cmd} {server_script_path}")
        import traceback

        traceback.print_exc()
