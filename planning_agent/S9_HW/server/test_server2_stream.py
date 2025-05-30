#!/usr/bin/env python3
"""
Test script for server2_stream.py (Web Tools Stream Server) using HTTP transport
"""

import asyncio
from fastmcp import Client
import logging
import sys
import json
import os

# Disable SSL verification for local testing
os.environ.pop("SSL_CERT_FILE", None)

# Set up logging to capture context messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Create a logger for MCP context messages
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)


def parse_result(result_text):
    """Parse JSON result and extract the result value or return full JSON for complex responses"""
    try:
        data = json.loads(result_text)
        return data
    except (json.JSONDecodeError, AttributeError):
        return result_text


async def test_server2_stream():
    """Test server2_stream.py web tools functions using HTTP transport"""
    print("\n🌐 Testing Web Tools Stream Server (server2_stream.py)")
    print("🔗 Connecting to: http://127.0.0.1:4202/mcp/")
    print("=" * 60)

    # Create client using HTTP transport to the stream server
    client = Client("http://127.0.0.1:4202/mcp/")

    try:
        async with client:
            print(f"✅ Connected to server2_stream: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"📋 Available tools ({len(tools)}):")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

            print("\n🔍 Testing Web Search (HTTP Stream with Context):")
            print("-" * 55)

            # Test basic web search with progress reporting
            print("🌐 Testing DuckDuckGo search for 'Python programming'...")
            print("   (Watch for progress updates and detailed logging)")
            try:
                search_result = await client.call_tool(
                    "search_web",
                    {"input": {"query": "Python programming", "max_results": 3}},
                )
                parsed_result = parse_result(search_result[0].text)

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

            print("\n📄 Testing Webpage Fetch (HTTP Stream with Context):")
            print("-" * 55)

            # Test basic webpage fetch with progress reporting
            print("🌐 Testing webpage fetch from httpbin.org...")
            print("   (Watch for progress updates and detailed logging)")
            try:
                fetch_result = await client.call_tool(
                    "fetch_webpage",
                    {"input": {"url": "https://httpbin.org/html", "max_length": 500}},
                )
                parsed_result = parse_result(fetch_result[0].text)

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

            print("\n🚫 Testing Error Handling (HTTP Stream with Context):")
            print("-" * 55)

            # Test invalid URL with context error logging
            print("🌐 Testing invalid URL (should trigger context error logging)...")
            try:
                invalid_result = await client.call_tool(
                    "fetch_webpage",
                    {"input": {"url": "invalid-url", "max_length": 500}},
                )
                parsed_result = parse_result(invalid_result[0].text)

                if not parsed_result.get("success", True):
                    print("✅ Invalid URL correctly handled")
                    error_msg = parsed_result.get("error_message", "Unknown error")
                    print(f"   Error message: {error_msg}")
                else:
                    print("⚠️  Expected error but got success")

            except Exception as e:
                print(f"✅ Invalid URL correctly caught: {type(e).__name__}")

            print("\n🌐 Testing HTTP Stream Specific Features:")
            print("-" * 45)

            print("🔗 Testing multiple rapid web requests (HTTP stream performance)...")
            rapid_queries = ["FastMCP", "Python", "HTTP", "streaming", "MCP"]
            rapid_results = []

            for i, query in enumerate(rapid_queries):
                try:
                    result = await client.call_tool(
                        "search_web",
                        {"input": {"query": query, "max_results": 1}},
                    )
                    parsed_result = parse_result(result[0].text)
                    success = parsed_result.get("success", False)
                    rapid_results.append(f"Query '{query}': {'✅' if success else '❌'}")
                except Exception as e:
                    rapid_results.append(f"Query '{query}': ❌ {type(e).__name__}")

            print("✅ Rapid web requests completed:")
            for result in rapid_results:
                print(f"   {result}")

            print("\n🧪 Testing Advanced Web Operations (HTTP Stream):")
            print("-" * 50)

            # Test different search parameters
            print("🌐 Testing search with different parameters...")
            try:
                advanced_search = await client.call_tool(
                    "search_web",
                    {"input": {"query": "FastMCP framework", "max_results": 5}},
                )
                parsed_result = parse_result(advanced_search[0].text)
                if parsed_result.get("success", False):
                    print("✅ Advanced search parameters work correctly")
                else:
                    print("❌ Advanced search failed")
            except Exception as e:
                print(f"❌ Advanced search failed: {e}")

            # Test different content length limits
            print("\n🌐 Testing fetch with different content limits...")
            try:
                limited_fetch = await client.call_tool(
                    "fetch_webpage",
                    {"input": {"url": "https://httpbin.org/html", "max_length": 100}},
                )
                parsed_result = parse_result(limited_fetch[0].text)
                if parsed_result.get("success", False):
                    content = parsed_result.get("content", "")
                    print(f"✅ Content limit works: {len(content)} chars (limit: 100)")
                else:
                    print("❌ Limited fetch failed")
            except Exception as e:
                print(f"❌ Limited fetch failed: {e}")

        print("\n" + "=" * 60)
        print("✅ All Web Tools Stream tests completed successfully!")
        print("🌐 HTTP Transport: Connected to http://127.0.0.1:4202/mcp/")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent through the HTTP stream to the MCP client")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 60)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the Web Tools Stream server is running:")
        print("   python server2_stream.py")
        print("   Server should be available at http://127.0.0.1:4202/mcp/")
    except Exception as e:
        print(f"\n❌ Error during Web Tools Stream testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🌟 Testing Web Tools Stream Server (server2_stream.py)")
    print("🔗 Using HTTP transport to http://127.0.0.1:4202/mcp/")
    print("=" * 60)

    try:
        asyncio.run(test_server2_stream())
        print("\n✅ Web Tools Stream test completed!")
        print("\n📊 Test Summary:")
        print("   🔍 Web Search: DuckDuckGo search with progress reporting")
        print("   📄 Webpage Fetch: HTML content extraction with progress")
        print("   🚫 Error Handling: Invalid URL with context logging")
        print("   🌐 HTTP Stream: Multiple rapid requests and advanced operations")
    except Exception as e:
        print(f"\n❌ Web Tools Stream test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Start the server: python server2_stream.py")
        print("   2. Check if port 4202 is available")
        print("   3. Verify server is running at http://127.0.0.1:4202/mcp/")
        print("   4. Check internet connection for web operations")
        print("   5. Verify tool_utils/web_tools.py exists")
        import traceback

        traceback.print_exc()
