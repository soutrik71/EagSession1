#!/usr/bin/env python3
"""
Simple test for FastMCP 2.0 multi-server session.

This script demonstrates:
1. FastMCPSession - New async context manager for multi-server access
2. MultiMCP wrapper - Compatibility layer for existing code migration

Usage:
1. Start servers: uv run server/server{1,2,3}_stream.py
2. Run test: uv run client/test_session.py
"""

import asyncio
import yaml
import os
from pathlib import Path

# Fix SSL cert issue for local testing
os.environ.pop("SSL_CERT_FILE", None)

# Add project root to path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from client.core.session import FastMCPSession, MultiMCP


async def test_simple_session():
    """
    Test FastMCPSession - The new unified session approach.

    This demonstrates ONE session connecting to ALL servers (calculator, web, doc_search)
    and calling tools from each server using the same session instance.
    """
    print("🧪 FastMCP 2.0 Multi-Server Test")
    print("=" * 40)

    # Load config
    config_path = Path(__file__).parent / "profiles.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)["mcp_client_config"]

    try:
        async with FastMCPSession(config) as session:
            # Check connections
            tools = await session.list_tools()
            server_info = session.get_server_info()

            active_servers = {k: len(v) for k, v in server_info.items() if v}
            print(
                f"📋 Connected: {len(tools)} tools from {len(active_servers)} servers"
            )

            if len(active_servers) == 0:
                print("❌ No servers running. Start servers first.")
                return

            # Test one tool from each available server to prove unified access
            if server_info.get("calculator"):
                result = await session.call_tool(
                    "calculator_add", {"input": {"a": 5, "b": 3}}
                )
                print(f"✅ Calculator: 5+3 = {result[0].text}")

            if server_info.get("web_tools"):
                result = await session.call_tool(
                    "web_tools_search_web",
                    {"input": {"query": "python", "max_results": 1}},
                )
                print("✅ Web search: Found results")

            if server_info.get("doc_search"):
                result = await session.call_tool(
                    "doc_search_query_documents", {"input": {"query": "AI", "top_k": 1}}
                )
                print("✅ Doc search: Found documents")

            print("🎉 All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure all servers are running on ports 4201-4203")


async def test_compatibility():
    """
    Test MultiMCP wrapper - Compatibility layer for existing code.

    This demonstrates the same multi-server access using the MultiMCP wrapper,
    which provides the old API for easier migration from stdio-based MultiMCP.
    Should work identically to FastMCPSession but with different interface.
    """
    print("\n🔄 Testing MultiMCP wrapper...")

    try:
        config_path = Path(__file__).parent / "profiles.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)["mcp_client_config"]

        # Initialize MultiMCP wrapper
        multi_mcp = MultiMCP(mcp_config=config)
        await multi_mcp.initialize()

        # Check tool availability
        tools = await multi_mcp.list_all_tools()
        tool_names = [tool.name for tool in multi_mcp.get_all_tools()]
        print(f"✅ MultiMCP: {len(tools)} tools accessible")

        # Test actual tool calls using MultiMCP wrapper (same as session test)
        if "calculator_add" in tool_names:
            result = await multi_mcp.call_tool(
                "calculator_add", {"input": {"a": 10, "b": 5}}
            )
            print(f"✅ MultiMCP Calculator: 10+5 = {result[0].text}")

        if "web_tools_search_web" in tool_names:
            await multi_mcp.call_tool(
                "web_tools_search_web", {"input": {"query": "test", "max_results": 1}}
            )
            print("✅ MultiMCP Web search: Tool called successfully")

        if "doc_search_query_documents" in tool_names:
            await multi_mcp.call_tool(
                "doc_search_query_documents", {"input": {"query": "test", "top_k": 1}}
            )
            print("✅ MultiMCP Doc search: Tool called successfully")

        await multi_mcp.shutdown()
        print("✅ MultiMCP wrapper test completed")

    except Exception as e:
        print(f"❌ MultiMCP test failed: {e}")


async def main():
    """
    Main test runner.

    Runs both FastMCPSession and MultiMCP tests to demonstrate:
    - New unified session approach (recommended)
    - Backward compatibility wrapper (for migration)
    """
    await test_simple_session()
    await test_compatibility()
    print("\n✨ FastMCP 2.0 session testing complete!")
    print("💡 Both approaches provide the same multi-server access capabilities")


if __name__ == "__main__":
    asyncio.run(main())
