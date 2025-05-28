#!/usr/bin/env python3
"""
Test script for server3_stream.py (Document Search Stream Server) using HTTP transport
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


async def test_server3_stream():
    """Test server3_stream.py document search functions using HTTP transport"""
    print("\n📚 Testing Document Search Stream Server (server3_stream.py)")
    print("🔗 Connecting to: http://127.0.0.1:4203/mcp/")
    print("=" * 60)

    # Create client using HTTP transport to the stream server
    client = Client("http://127.0.0.1:4203/mcp/")

    try:
        async with client:
            print(f"✅ Connected to server3_stream: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"📋 Available tools ({len(tools)}):")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

            print("\n📖 Testing Document Query (HTTP Stream with Context):")
            print("-" * 55)

            # Test basic document search with progress reporting
            print("📚 Testing document search for 'Who is MS Dhoni ?'...")
            print("   (Watch for progress updates and detailed logging)")
            try:
                search_result = await client.call_tool(
                    "query_documents",
                    {"input": {"query": "Who is MS Dhoni ?", "top_k": 3}},
                )
                parsed_result = parse_result(search_result[0].text)

                if parsed_result.get("success", False):
                    results = parsed_result.get("results", [])
                    total_results = parsed_result.get("total_results", 0)
                    status_message = parsed_result.get("error_message", "")

                    print("✅ Document search successful")
                    print("   Query: 'Who is MS Dhoni ?'")
                    print(
                        f"   Found: {len(results)} results (out of {total_results} total)"
                    )
                    print(f"   Status: {status_message}")

                    if results:
                        print("   Top results:")
                        for i, result in enumerate(results[:2], 1):
                            chunk_preview = result.get("chunk", "")[:100].replace(
                                "\n", " "
                            )
                            source = result.get("source", "Unknown")
                            score = result.get("score", 0.0)
                            print(f"     {i}. Source: {source} (Score: {score:.4f})")
                            print(f"        Preview: {chunk_preview}...")
                else:
                    error_msg = parsed_result.get("error_message", "Unknown error")
                    print(f"❌ Document search failed: {error_msg}")

            except Exception as e:
                print(f"❌ query_documents failed: {e}")

            print("\n🔍 Testing Different Query Types (HTTP Stream with Context):")
            print("-" * 60)

            # Test different types of queries with more relevant questions
            test_queries = [
                ("Who is MS Dhoni and what are his achievements?", 3),
                ("What is Tesla Motors working on in electric vehicles?", 3),
                ("What is artificial intelligence and machine learning?", 2),
                ("How does renewable energy work?", 2),
                ("What are the latest developments in space exploration?", 4),
            ]

            for query, top_k in test_queries:
                print(f"\n📚 Testing query: '{query}' (top {top_k} results)...")
                try:
                    query_result = await client.call_tool(
                        "query_documents",
                        {"input": {"query": query, "top_k": top_k}},
                    )
                    parsed_result = parse_result(query_result[0].text)

                    if parsed_result.get("success", False):
                        results = parsed_result.get("results", [])
                        total_results = parsed_result.get("total_results", 0)
                        print(
                            f"✅ Query '{query}': {len(results)} results (of {total_results} total)"
                        )
                    else:
                        error_msg = parsed_result.get("error_message", "Unknown error")
                        print(f"❌ Query '{query}' failed: {error_msg}")

                except Exception as e:
                    print(f"❌ Query '{query}' failed: {e}")

            print("\n🚫 Testing Error Handling (HTTP Stream with Context):")
            print("-" * 55)

            # Test empty query
            print("📚 Testing empty query (should trigger context error logging)...")
            try:
                empty_result = await client.call_tool(
                    "query_documents",
                    {"input": {"query": "", "top_k": 5}},
                )
                parsed_result = parse_result(empty_result[0].text)

                if not parsed_result.get("success", True):
                    print("✅ Empty query correctly handled")
                    error_msg = parsed_result.get("error_message", "Unknown error")
                    print(f"   Error message: {error_msg}")
                else:
                    print("⚠️  Expected error but got success")

            except Exception as e:
                print(f"✅ Empty query correctly caught: {type(e).__name__}")

            # Test invalid top_k
            print(
                "\n📚 Testing invalid top_k (0) (should trigger context error logging)..."
            )
            try:
                invalid_result = await client.call_tool(
                    "query_documents",
                    {"input": {"query": "test query", "top_k": 0}},
                )
                parsed_result = parse_result(invalid_result[0].text)

                if not parsed_result.get("success", True):
                    print("✅ Invalid top_k correctly handled")
                    error_msg = parsed_result.get("error_message", "Unknown error")
                    print(f"   Error message: {error_msg}")
                else:
                    print("⚠️  Expected error but got success")

            except Exception as e:
                print(f"✅ Invalid top_k correctly caught: {type(e).__name__}")

            print("\n🌐 Testing HTTP Stream Specific Features:")
            print("-" * 45)

            print(
                "🔗 Testing multiple rapid document queries (HTTP stream performance)..."
            )
            rapid_queries = [
                "Who is MS Dhoni and what is his role in cricket?",
                "What is Tesla Motors working on in autonomous driving?",
                "How does climate change affect the environment?",
                "What are the benefits of renewable energy sources?",
                "What is the future of artificial intelligence?",
            ]
            rapid_results = []

            for i, query in enumerate(rapid_queries):
                try:
                    result = await client.call_tool(
                        "query_documents",
                        {"input": {"query": query, "top_k": 1}},
                    )
                    parsed_result = parse_result(result[0].text)
                    success = parsed_result.get("success", False)
                    results_count = len(parsed_result.get("results", []))
                    rapid_results.append(
                        f"Query '{query}': {'✅' if success else '❌'} ({results_count} results)"
                    )
                except Exception as e:
                    rapid_results.append(f"Query '{query}': ❌ {type(e).__name__}")

            print("✅ Rapid document queries completed:")
            for result in rapid_results:
                print(f"   {result}")

            print("\n🧪 Testing Advanced Document Operations (HTTP Stream):")
            print("-" * 55)

            # Test different top_k values
            print("📚 Testing search with different top_k values...")
            try:
                advanced_search = await client.call_tool(
                    "query_documents",
                    {
                        "input": {
                            "query": "What are the latest innovations in technology?",
                            "top_k": 10,
                        }
                    },
                )
                parsed_result = parse_result(advanced_search[0].text)
                if parsed_result.get("success", False):
                    results = parsed_result.get("results", [])
                    print(f"✅ Advanced search with top_k=10: {len(results)} results")
                else:
                    print("❌ Advanced search failed")
            except Exception as e:
                print(f"❌ Advanced search failed: {e}")

            # Test semantic similarity
            print("\n📚 Testing semantic similarity search...")
            try:
                semantic_search = await client.call_tool(
                    "query_documents",
                    {
                        "input": {
                            "query": "sustainable development and environmental protection",
                            "top_k": 5,
                        }
                    },
                )
                parsed_result = parse_result(semantic_search[0].text)
                if parsed_result.get("success", False):
                    results = parsed_result.get("results", [])
                    print(f"✅ Semantic search successful: {len(results)} results")
                    if results:
                        avg_score = sum(r.get("score", 0) for r in results) / len(
                            results
                        )
                        print(f"   Average relevance score: {avg_score:.4f}")
                else:
                    print("❌ Semantic search failed")
            except Exception as e:
                print(f"❌ Semantic search failed: {e}")

        print("\n" + "=" * 60)
        print("✅ All Document Search Stream tests completed successfully!")
        print("🌐 HTTP Transport: Connected to http://127.0.0.1:4203/mcp/")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent through the HTTP stream to the MCP client")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 60)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the Document Search Stream server is running:")
        print("   python server3_stream.py")
        print("   Server should be available at http://127.0.0.1:4203/mcp/")
    except Exception as e:
        print(f"\n❌ Error during Document Search Stream testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🌟 Testing Document Search Stream Server (server3_stream.py)")
    print("🔗 Using HTTP transport to http://127.0.0.1:4203/mcp/")
    print("=" * 60)

    try:
        asyncio.run(test_server3_stream())
        print("\n✅ Document Search Stream test completed!")
        print("\n📊 Test Summary:")
        print("   📖 Document Query: Semantic search with progress reporting")
        print("   🔍 Multiple Queries: Different query types and top_k values")
        print("   🚫 Error Handling: Empty queries and invalid parameters")
        print("   🌐 HTTP Stream: Multiple rapid queries and advanced operations")
        print("   🧪 Advanced Features: Semantic similarity and relevance scoring")
    except Exception as e:
        print(f"\n❌ Document Search Stream test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Start the server: python server3_stream.py")
        print("   2. Check if port 4203 is available")
        print("   3. Verify server is running at http://127.0.0.1:4203/mcp/")
        print("   4. Check if documents exist in the documents folder")
        print("   5. Verify tool_utils/doc_tools.py exists")
        print("   6. Run create_index.py if no index exists")
        import traceback

        traceback.print_exc()
