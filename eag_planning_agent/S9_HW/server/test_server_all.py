#!/usr/bin/env python3
"""
Multi-Server Test Client for S9_HW MCP Stream Servers

Tests all three stream servers using a single multi-server client:
- server1_stream.py: Calculator operations (port 4201)
- server2_stream.py: Web tools (port 4202)
- server3_stream.py: Document search (port 4203)
"""

import asyncio
from fastmcp import Client
import logging
import json
import os
import math

# Disable SSL verification for local testing
os.environ.pop("SSL_CERT_FILE", None)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Multi-server configuration
config = {
    "mcpServers": {
        "calculator": {
            "url": "http://127.0.0.1:4201/mcp/",
            "transport": "streamable-http",
        },
        "web_tools": {
            "url": "http://127.0.0.1:4202/mcp/",
            "transport": "streamable-http",
        },
        "doc_search": {
            "url": "http://127.0.0.1:4203/mcp/",
            "transport": "streamable-http",
        },
    }
}

# Create single multi-server client
client = Client(config)


def parse_result(result_text):
    """Parse JSON result and extract value"""
    try:
        data = json.loads(result_text)
        return data.get("result", data)
    except (json.JSONDecodeError, AttributeError):
        return result_text


async def test_all_servers():
    """Test all servers using single multi-server client"""
    async with client:
        print(f"✅ Multi-server client connected: {client.is_connected()}")

        # List all available tools
        tools = await client.list_tools()
        print(f"\n📋 Available tools from all servers ({len(tools)}):")

        # Group tools by server
        server_tools = {"calculator": [], "web_tools": [], "doc_search": []}
        for tool in tools:
            if tool.name.startswith("calculator_"):
                server_tools["calculator"].append(tool.name)
            elif tool.name.startswith("web_tools_"):
                server_tools["web_tools"].append(tool.name)
            elif tool.name.startswith("doc_search_"):
                server_tools["doc_search"].append(tool.name)

        for server, tool_list in server_tools.items():
            if tool_list:
                print(f"   {server}: {len(tool_list)} tools")

        # Test Calculator Server (1 test per tool)
        print("\n🧮 Testing Calculator Server:")
        calc_tests = [
            ("calculator_add", {"input": {"a": 15, "b": 25}}, "15 + 25"),
            ("calculator_subtract", {"input": {"a": 50, "b": 18}}, "50 - 18"),
            ("calculator_multiply", {"input": {"a": 7, "b": 8}}, "7 × 8"),
            ("calculator_divide", {"input": {"a": 144, "b": 12}}, "144 ÷ 12"),
            ("calculator_power", {"input": {"a": 2, "b": 8}}, "2^8"),
            ("calculator_cbrt", {"input": {"a": 27}}, "∛27"),
            ("calculator_factorial", {"input": {"a": 5}}, "5!"),
            ("calculator_remainder", {"input": {"a": 17, "b": 5}}, "17 % 5"),
            ("calculator_sin", {"input": {"a": math.pi / 6}}, "sin(π/6)"),
            ("calculator_cos", {"input": {"a": math.pi / 6}}, "cos(π/6)"),
            ("calculator_tan", {"input": {"a": math.pi / 6}}, "tan(π/6)"),
            ("calculator_mine", {"input": {"a": 10, "b": 3}}, "mine(10, 3)"),
            ("calculator_fibonacci_numbers", {"input": {"n": 8}}, "fibonacci(8)"),
            (
                "calculator_strings_to_chars_to_int",
                {"input": {"string": "Hello"}},
                "ASCII('Hello')",
            ),
            (
                "calculator_int_list_to_exponential_sum",
                {"input": {"numbers": [1, 2, 3]}},
                "exp_sum([1,2,3])",
            ),
        ]

        for tool_name, params, description in calc_tests:
            if any(tool.name == tool_name for tool in tools):
                try:
                    result = await client.call_tool(tool_name, params)
                    print(f"🔍 Raw result for {tool_name}: {result[0].text}")
                    parsed = parse_result(result[0].text)
                    if tool_name in [
                        "calculator_sin",
                        "calculator_cos",
                        "calculator_tan",
                    ]:
                        print(f"✅ {description} = {float(parsed):.6f}")
                    elif tool_name == "calculator_int_list_to_exponential_sum":
                        print(f"✅ {description} = {float(parsed):.4f}")
                    else:
                        print(f"✅ {description} = {parsed}")
                except Exception as e:
                    print(f"❌ {tool_name} failed: {str(e)}")

        # Test create_thumbnail (expected to fail)
        if any(tool.name == "calculator_create_thumbnail" for tool in tools):
            try:
                result = await client.call_tool(
                    "calculator_create_thumbnail", {"input": {"image_path": "test.jpg"}}
                )
                print(f"🔍 Raw result for calculator_create_thumbnail: {result[0].text}")
                print(f"✅ thumbnail(test.jpg) = {parse_result(result[0].text)}")
            except Exception as e:
                print(f"⚠️  thumbnail(test.jpg) failed (expected): {type(e).__name__}")

        # Test Web Tools Server (1 test per tool)
        print("\n🌐 Testing Web Tools Server:")

        if any(tool.name == "web_tools_search_web" for tool in tools):
            try:
                result = await client.call_tool(
                    "web_tools_search_web",
                    {"input": {"query": "Python programming", "max_results": 3}},
                )
                print(f"🔍 Raw result for web_tools_search_web: {result[0].text}")
                parsed = parse_result(result[0].text)
                if parsed.get("success", False):
                    results_len = len(parsed.get("results", ""))
                    print(f"✅ search('Python programming') = {results_len} chars")
                else:
                    print(f"❌ search failed: {parsed.get('error_message', 'Unknown')}")
            except Exception as e:
                print(f"❌ web_tools_search_web failed: {str(e)}")

        if any(tool.name == "web_tools_fetch_webpage" for tool in tools):
            try:
                result = await client.call_tool(
                    "web_tools_fetch_webpage",
                    {"input": {"url": "https://httpbin.org/html", "max_length": 500}},
                )
                print(f"🔍 Raw result for web_tools_fetch_webpage: {result[0].text}")
                parsed = parse_result(result[0].text)
                if parsed.get("success", False):
                    content_len = len(parsed.get("content", ""))
                    print(f"✅ fetch('httpbin.org/html') = {content_len} chars")
                else:
                    print(f"❌ fetch failed: {parsed.get('error_message', 'Unknown')}")
            except Exception as e:
                print(f"❌ web_tools_fetch_webpage failed: {str(e)}")

        # Test Document Search Server (1 test per tool)
        print("\n📚 Testing Document Search Server:")

        if any(tool.name == "doc_search_query_documents" for tool in tools):
            try:
                result = await client.call_tool(
                    "doc_search_query_documents",
                    {"input": {"query": "Who is MS Dhoni ?", "top_k": 3}},
                )
                print(f"🔍 Raw result for doc_search_query_documents: {result[0].text}")
                parsed = parse_result(result[0].text)
                if parsed.get("success", False):
                    results = parsed.get("results", [])
                    total = parsed.get("total_results", 0)
                    print(
                        f"✅ query('Who is MS Dhoni ?') = {len(results)}/{total} results"
                    )
                    if results:
                        first = results[0]
                        source = first.get("source", "Unknown")
                        score = first.get("score", 0.0)
                        print(f"   Top: {source} (Score: {score:.4f})")
                else:
                    error = parsed.get("error_message", "Unknown")
                    print(f"❌ query failed: {error}")
                    if "No documents found" in error:
                        print(
                            "   💡 Add documents to 'documents' folder and run create_index.py"
                        )
            except Exception as e:
                print(f"❌ doc_search_query_documents failed: {str(e)}")

        # Test Error Handling (1 per server)
        print("\n🚫 Testing Error Handling:")

        # Calculator: Division by zero
        if any(tool.name == "calculator_divide" for tool in tools):
            try:
                result = await client.call_tool(
                    "calculator_divide", {"input": {"a": 42, "b": 0}}
                )
                print(
                    f"🔍 Raw result for calculator_divide (error test): {result[0].text}"
                )
                print(f"⚠️  Expected error but got: {parse_result(result[0].text)}")
            except Exception as e:
                print(f"✅ Calculator division by zero caught: {type(e).__name__}")

        # Web Tools: Invalid URL
        if any(tool.name == "web_tools_fetch_webpage" for tool in tools):
            try:
                result = await client.call_tool(
                    "web_tools_fetch_webpage",
                    {"input": {"url": "invalid-url", "max_length": 500}},
                )
                print(
                    f"🔍 Raw result for web_tools_fetch_webpage (error test): {result[0].text}"
                )
                parsed = parse_result(result[0].text)
                if not parsed.get("success", True):
                    print("✅ Web Tools invalid URL handled correctly")
                else:
                    print("⚠️  Expected error but got success")
            except Exception as e:
                print(f"✅ Web Tools invalid URL caught: {type(e).__name__}")

        # Document Search: Empty query
        if any(tool.name == "doc_search_query_documents" for tool in tools):
            try:
                result = await client.call_tool(
                    "doc_search_query_documents", {"input": {"query": "", "top_k": 5}}
                )
                print(
                    f"🔍 Raw result for doc_search_query_documents (error test): {result[0].text}"
                )
                parsed = parse_result(result[0].text)
                if not parsed.get("success", True):
                    print("✅ Document Search empty query handled correctly")
                else:
                    print("⚠️  Expected error but got success")
            except Exception as e:
                print(f"✅ Document Search empty query caught: {type(e).__name__}")

        return True


async def main():
    """Main test function"""
    print("🌟 Testing S9_HW MCP Stream Servers (Multi-Server Client)")
    print("🔗 Connecting to three HTTP stream servers:")
    print("   🧮 Calculator: http://127.0.0.1:4201/mcp/ (server1_stream.py)")
    print("   🌐 Web Tools: http://127.0.0.1:4202/mcp/ (server2_stream.py)")
    print("   📚 Doc Search: http://127.0.0.1:4203/mcp/ (server3_stream.py)")
    print("=" * 70)

    try:
        success = await test_all_servers()

        if success:
            print(f"\n✅ Multi-server client disconnected: {not client.is_connected()}")
            print("=" * 70)
            print("✅ All stream server tests completed!")
            print("🎯 Summary: 16 calculator + 2 web + 1 doc + 3 error tests")
            print("🌐 Transport: HTTP streaming to all servers")
            print("=" * 70)

    except Exception as e:
        print(f"\n❌ Multi-server test failed: {str(e)}")
        print("\n🚀 Start all servers:")
        print("   python server1_stream.py")
        print("   python server2_stream.py")
        print("   python server3_stream.py")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
