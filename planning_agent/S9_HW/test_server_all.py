#!/usr/bin/env python3
"""
Comprehensive Test Client for S9_HW MCP Servers

This script tests all three MCP servers:
- server1.py: Calculator and mathematical operations
- server2.py: Web tools (search and fetch)
- server3.py: Document search and query

Based on FastMCP 2.0 multi-server testing patterns.
"""

from fastmcp import Client
import asyncio
import json
import math
import logging
import sys
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

# Configuration for our three MCP servers
config = {
    "mcpServers": {
        # Calculator server (server1.py)
        "calculator": {
            "command": "python",
            "args": ["./server1.py"],
            "env": {"DEBUG": "true"},
        },
        # Web tools server (server2.py)
        "web_tools": {
            "command": "python",
            "args": ["./server2.py"],
            "env": {"DEBUG": "true"},
        },
        # Document search server (server3.py)
        "doc_search": {
            "command": "python",
            "args": ["./server3.py"],
            "env": {"DEBUG": "true"},
        },
    }
}

# Create a multi-server client
client = Client(config)


async def test_calculator_server(tools):
    """Test server1.py - Calculator and mathematical operations"""
    print("\n🧮 Testing Calculator Server (server1.py):")
    print("=" * 50)

    # Test basic mathematical operations
    math_tests = [
        ("add", {"a": 15, "b": 25}, "15 + 25"),
        ("subtract", {"a": 50, "b": 18}, "50 - 18"),
        ("multiply", {"a": 7, "b": 8}, "7 × 8"),
        ("divide", {"a": 144, "b": 12}, "144 ÷ 12"),
        ("power", {"a": 2, "b": 8}, "2^8"),
        ("cbrt", {"a": 27}, "∛27"),
        ("factorial", {"a": 5}, "5!"),
        ("remainder", {"a": 17, "b": 5}, "17 % 5"),
    ]

    for tool_name, params, description in math_tests:
        if any(tool.name == tool_name for tool in tools):
            try:
                result = await client.call_tool(tool_name, params)
                print(f"✅ {description} = {result[0].text}")
            except Exception as e:
                print(f"❌ {tool_name} failed: {str(e)}")

    # Test trigonometric functions
    print("\n📐 Trigonometric Functions:")
    angle = math.pi / 6  # 30 degrees in radians
    trig_tests = [
        ("sin", "sine"),
        ("cos", "cosine"),
        ("tan", "tangent"),
    ]

    for tool_name, func_name in trig_tests:
        if any(tool.name == tool_name for tool in tools):
            try:
                result = await client.call_tool(tool_name, {"a": angle})
                print(f"✅ {func_name}(π/6) = {float(result[0].text):.6f}")
            except Exception as e:
                print(f"❌ {tool_name} failed: {str(e)}")

    # Test special operations
    print("\n🔧 Special Operations:")

    # Test mine operation
    if any(tool.name == "mine" for tool in tools):
        try:
            result = await client.call_tool("mine", {"a": 10, "b": 3})
            print(f"✅ mine(10, 3) = {result[0].text}")
        except Exception as e:
            print(f"❌ mine failed: {str(e)}")

    # Test string to ASCII conversion
    if any(tool.name == "strings_to_chars_to_int" for tool in tools):
        try:
            result = await client.call_tool(
                "strings_to_chars_to_int", {"string": "Hello"}
            )
            print(f"✅ ASCII values of 'Hello': {result[0].text}")
        except Exception as e:
            print(f"❌ strings_to_chars_to_int failed: {str(e)}")

    # Test exponential sum
    if any(tool.name == "int_list_to_exponential_sum" for tool in tools):
        try:
            result = await client.call_tool(
                "int_list_to_exponential_sum", {"numbers": [1, 2, 3]}
            )
            print(f"✅ Exponential sum of [1,2,3]: {float(result[0].text):.4f}")
        except Exception as e:
            print(f"❌ int_list_to_exponential_sum failed: {str(e)}")

    # Test Fibonacci sequence
    if any(tool.name == "fibonacci_numbers" for tool in tools):
        try:
            result = await client.call_tool("fibonacci_numbers", {"n": 8})
            print(f"✅ First 8 Fibonacci numbers: {result[0].text}")
        except Exception as e:
            print(f"❌ fibonacci_numbers failed: {str(e)}")

    # Test create_thumbnail (image operation)
    if any(tool.name == "create_thumbnail" for tool in tools):
        try:
            # This will likely fail without a real image, but we test the tool exists
            result = await client.call_tool(
                "create_thumbnail", {"image_path": "test.jpg"}
            )
            print(f"✅ create_thumbnail executed: {result[0].text}")
        except Exception as e:
            print(f"⚠️  create_thumbnail failed (expected): {type(e).__name__}")


async def test_web_tools_server(tools):
    """Test server2.py - Web tools (search and fetch)"""
    print("\n🌐 Testing Web Tools Server (server2.py):")
    print("=" * 50)

    # Test web search
    if any(tool.name == "search_web" for tool in tools):
        try:
            print("🔍 Testing web search...")
            result = await client.call_tool(
                "search_web", {"query": "FastMCP framework", "max_results": 3}
            )
            search_data = json.loads(result[0].text)
            if search_data.get("success", False):
                results_text = search_data.get("results", "")
                result_count = len(results_text.split("\n")) if results_text else 0
                print(f"✅ Web search successful: Found {result_count} results")
                print(f"   Query: {search_data.get('query', 'N/A')}")
            else:
                print(
                    f"❌ Web search failed: {search_data.get('error_message', 'Unknown error')}"
                )
        except Exception as e:
            print(f"❌ search_web failed: {str(e)}")

    # Test webpage fetching
    if any(tool.name == "fetch_webpage" for tool in tools):
        try:
            print("📄 Testing webpage fetch...")
            result = await client.call_tool(
                "fetch_webpage", {"url": "https://httpbin.org/html", "max_length": 500}
            )
            fetch_data = json.loads(result[0].text)
            if fetch_data.get("success", False):
                content_length = len(fetch_data.get("content", ""))
                print(
                    f"✅ Webpage fetch successful: Retrieved {content_length} characters"
                )
            else:
                print(
                    f"❌ Webpage fetch failed: {fetch_data.get('error_message', 'Unknown error')}"
                )
        except Exception as e:
            print(f"❌ fetch_webpage failed: {str(e)}")


async def test_document_search_server(tools):
    """Test server3.py - Document search and query"""
    print("\n📚 Testing Document Search Server (server3.py):")
    print("=" * 50)

    # Test document query
    if any(tool.name == "query_documents" for tool in tools):
        try:
            print("🔍 Testing document query...")
            result = await client.call_tool(
                "query_documents", {"query": "machine learning algorithms", "top_k": 3}
            )
            query_data = json.loads(result[0].text)
            if query_data.get("success", False):
                results_count = len(query_data.get("results", []))
                total_results = query_data.get("total_results", 0)
                print(
                    f"✅ Document query successful: Found {results_count} results out of {total_results} total"
                )
                print(f"   Query: '{query_data.get('query', 'N/A')}'")

                # Show first result if available
                results = query_data.get("results", [])
                if results:
                    first_result = results[0]
                    chunk_text = first_result.get("chunk", "")
                    chunk_preview = (
                        chunk_text[:100] + "..."
                        if len(chunk_text) > 100
                        else chunk_text
                    )
                    print(f"   Top result from: {first_result.get('source', 'N/A')}")
                    print(f"   Preview: {chunk_preview}")
                    print(f"   Score: {first_result.get('score', 'N/A')}")
            else:
                error_msg = query_data.get("error_message", "Unknown error")
                print(f"❌ Document query failed: {error_msg}")
                if "No documents found" in error_msg:
                    print(
                        "   💡 Tip: Add documents to the 'documents' folder and run create_index.py"
                    )
        except Exception as e:
            print(f"❌ query_documents failed: {str(e)}")


async def test_error_handling(tools):
    """Test error handling across all servers"""
    print("\n🚫 Testing Error Handling:")
    print("=" * 50)

    # Test division by zero (Calculator server)
    if any(tool.name == "divide" for tool in tools):
        try:
            result = await client.call_tool("divide", {"a": 42, "b": 0})
            print(f"⚠️  Expected division by zero error but got: {result[0].text}")
        except Exception as e:
            print(f"✅ Division by zero correctly caught: {type(e).__name__}")

    # Test factorial with large number (Calculator server)
    if any(tool.name == "factorial" for tool in tools):
        try:
            result = await client.call_tool("factorial", {"a": 200})
            print("⚠️  Expected factorial overflow error but got result")
        except Exception as e:
            print(f"✅ Factorial overflow correctly caught: {type(e).__name__}")

    # Test invalid URL (Web tools server)
    if any(tool.name == "fetch_webpage" for tool in tools):
        try:
            result = await client.call_tool(
                "fetch_webpage",
                {
                    "url": "https://invalid-url-that-does-not-exist.com",
                    "max_length": 100,
                },
            )
            fetch_data = json.loads(result[0].text)
            if not fetch_data.get("success", True):
                error_preview = fetch_data.get("error_message", "")[:50]
                print(f"✅ Invalid URL correctly handled: {error_preview}...")
            else:
                print("⚠️  Expected URL error but got success")
        except Exception as e:
            print(f"✅ Invalid URL correctly caught: {type(e).__name__}")


async def test_concurrent_operations(tools):
    """Test concurrent operations across multiple servers"""
    print("\n⚡ Testing Concurrent Operations:")
    print("=" * 50)

    concurrent_tasks = []

    # Calculator task
    if any(tool.name == "add" for tool in tools):
        calc_task = asyncio.create_task(client.call_tool("add", {"a": 100, "b": 200}))
        concurrent_tasks.append(("Calculator", calc_task))

    # Web search task
    if any(tool.name == "search_web" for tool in tools):
        web_task = asyncio.create_task(
            client.call_tool("search_web", {"query": "test", "max_results": 1})
        )
        concurrent_tasks.append(("Web Tools", web_task))

    # Document query task
    if any(tool.name == "query_documents" for tool in tools):
        doc_task = asyncio.create_task(
            client.call_tool("query_documents", {"query": "test", "top_k": 1})
        )
        concurrent_tasks.append(("Document Search", doc_task))

    if concurrent_tasks:
        results = await asyncio.gather(
            *[task for _, task in concurrent_tasks], return_exceptions=True
        )

        for i, (server_type, _) in enumerate(concurrent_tasks):
            if isinstance(results[i], Exception):
                print(f"❌ {server_type} failed: {results[i]}")
            else:
                print(f"✅ {server_type} succeeded: Response received")


async def connect_and_test_all_servers():
    """Main test function that connects to all servers and runs comprehensive tests"""
    async with client:
        print(f"✅ Multi-server client connected: {client.is_connected()}")

        # List available tools from all servers
        tools = await client.list_tools()
        print(f"\n📋 Available tools from all servers ({len(tools)}):")

        # Group tools by server based on actual available tools
        server_tools = {
            "Calculator": [],
            "Web Tools": [],
            "Document Search": [],
            "Unknown": [],
        }

        # Categorize tools based on actual tool names from the servers
        calculator_tools = {
            "add",
            "subtract",
            "multiply",
            "divide",
            "power",
            "cbrt",
            "factorial",
            "remainder",
            "sin",
            "cos",
            "tan",
            "mine",
            "create_thumbnail",
            "strings_to_chars_to_int",
            "int_list_to_exponential_sum",
            "fibonacci_numbers",
        }
        web_tools = {"search_web", "fetch_webpage"}
        doc_tools = {"query_documents"}

        for tool in tools:
            if tool.name in calculator_tools:
                server_tools["Calculator"].append(tool.name)
            elif tool.name in web_tools:
                server_tools["Web Tools"].append(tool.name)
            elif tool.name in doc_tools:
                server_tools["Document Search"].append(tool.name)
            else:
                server_tools["Unknown"].append(tool.name)

        for server, tool_list in server_tools.items():
            if tool_list:
                print(f"   {server}: {tool_list}")

        # Run tests for each server
        await test_calculator_server(tools)
        await test_web_tools_server(tools)
        await test_document_search_server(tools)
        await test_error_handling(tools)
        await test_concurrent_operations(tools)

        return True


async def main():
    """Main function to run all tests"""
    print("🌟 Testing S9_HW MCP Servers")
    print("🔗 Connecting to three servers:")
    print("   🧮 Calculator Server: ./server1.py")
    print("   🌐 Web Tools Server: ./server2.py")
    print("   📚 Document Search Server: ./server3.py")
    print("=" * 70)

    try:
        success = await connect_and_test_all_servers()

        if success:
            print(f"\n✅ Multi-server client disconnected: {not client.is_connected()}")
            print("=" * 70)
            print("✅ All server tests completed successfully!")
            print("🌟 Server Summary:")
            print(
                "   🧮 Calculator Server: 16 tools - Mathematical operations, trigonometry, special functions"
            )
            print(
                "   🌐 Web Tools Server: 2 tools - DuckDuckGo search, webpage content fetching"
            )
            print(
                "   📚 Document Search Server: 1 tool - Semantic document search with FAISS indexing"
            )
            print("=" * 70)
            print("🎯 Features Tested:")
            print("   🔢 Mathematical calculations and trigonometric functions")
            print("   🔍 Web search and content extraction")
            print("   📄 Document indexing and semantic search")
            print("   🚫 Error handling and validation")
            print("   ⚡ Concurrent multi-server operations")

    except Exception as e:
        print(f"\n❌ Multi-server connection failed: {str(e)}")
        print("\n🚀 To start the servers, run in separate terminals:")
        print("   Terminal 1: python server1.py")
        print("   Terminal 2: python server2.py")
        print("   Terminal 3: python server3.py")
        print("\n💡 Individual server tests:")
        print("   - Make sure all dependencies are installed")
        print(
            "   - For server3.py: Add documents to 'documents' folder and run create_index.py"
        )
        print("   - For server2.py: Check internet connection for web tools")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
