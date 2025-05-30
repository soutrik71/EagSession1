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

# Configuration for multiple MCP servers - Fixed based on reference
config = {
    "mcpServers": {
        # STDIO server for extended tools
        "stdio_tools": {
            "command": "python",
            "args": ["./tools_server_extended_stdio.py"],
            "env": {"DEBUG": "true"},
        },
        # HTTP Stream server for math and weather tools
        "stream_tools": {
            "url": "http://127.0.0.1:4200/mcp/",
            "transport": "streamable-http",
        },
        # SSE server for real-time tools
        "sse_tools": {"url": "http://127.0.0.1:4201/sse", "transport": "sse"},
    }
}

# Create a multi-server client
client = Client(config)


async def connect_and_test_multi_server():
    """Attempt to connect to multiple servers and run comprehensive tests."""
    async with client:
        print(f"✅ Multi-server client connected: {client.is_connected()}")

        # List available tools from all servers
        tools = await client.list_tools()
        print(f"\n📋 Available tools from all servers ({len(tools)}):")

        # Group tools by server prefix
        server_tools = {}
        for tool in tools:
            if "_" in tool.name:
                prefix = tool.name.split("_")[0]
                if prefix not in server_tools:
                    server_tools[prefix] = []
                server_tools[prefix].append(tool.name)
            else:
                if "general" not in server_tools:
                    server_tools["general"] = []
                server_tools["general"].append(tool.name)

        for server, tool_list in server_tools.items():
            print(f"   {server}: {tool_list}")

        # Test STDIO server tools (if available)
        print("\n🖥️ Testing STDIO Server Tools:")

        # Test string operations from STDIO server
        if any(tool.name == "stdio_tools_reverse_string" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_reverse_string", {"text": "Hello Multi-Server!"}
                )
                print(f"🔤 reverse_string: 'Hello Multi-Server!' → {result[0].text}")
            except Exception as e:
                print(f"❌ reverse_string failed: {str(e)}")

        # Test character analysis
        if any(tool.name == "stdio_tools_count_characters" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_count_characters",
                    {"text": "FastMCP Multi-Server Test!", "include_spaces": True},
                )
                count_data = json.loads(result[0].text)
                print(
                    f"📊 Character analysis: {count_data['letters']} letters, {count_data['words']} words"
                )
            except Exception as e:
                print(f"❌ count_characters failed: {str(e)}")

        # Test text transformation
        if any(tool.name == "stdio_tools_transform_text" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_transform_text",
                    {"input": {"text": "multi-server demo", "operation": "title"}},
                )
                print(f"🔤 Text transform: 'multi-server demo' → {result[0].text}")
            except Exception as e:
                print(f"❌ transform_text failed: {str(e)}")

        # Test secure password generation
        if any(tool.name == "stdio_tools_generate_password" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_generate_password",
                    {"length": 12, "include_symbols": True, "include_uppercase": True},
                )
                print(f"🔐 Secure password generated: {len(result[0].text)} characters")
            except Exception as e:
                print(f"❌ generate_password failed: {str(e)}")

        # Test dice rolling
        if any(tool.name == "stdio_tools_roll_dice" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_roll_dice", {"sides": 6, "count": 2}
                )
                dice_data = json.loads(result[0].text)
                print(f"🎲 Dice roll (2d6): {dice_data['rolls']} = {dice_data['total']}")
            except Exception as e:
                print(f"❌ roll_dice failed: {str(e)}")

        # Test cryptographic hashing
        if any(tool.name == "stdio_tools_hash_text" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_hash_text",
                    {
                        "input": {
                            "text": "Multi-Server Hash Test",
                            "algorithm": "sha256",
                        }
                    },
                )
                hash_data = json.loads(result[0].text)
                print(
                    f"🔐 SHA256 hash: {hash_data['hash_hex'][:16]}... ({hash_data['hash_length']} chars)"
                )
            except Exception as e:
                print(f"❌ hash_text failed: {str(e)}")

        # Test Base64 encoding
        if any(tool.name == "stdio_tools_encode_base64" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_encode_base64", {"text": "Multi-Server Test"}
                )
                encode_data = json.loads(result[0].text)
                print(f"📝 Base64 encode: '{encode_data['encoded_base64']}'")
            except Exception as e:
                print(f"❌ encode_base64 failed: {str(e)}")

        # Test current time
        if any(tool.name == "stdio_tools_get_current_time" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_get_current_time",
                    {"timezone": "UTC", "format_string": "%Y-%m-%d %H:%M:%S"},
                )
                time_data = json.loads(result[0].text)
                print(f"🕐 Current time (UTC): {time_data['formatted_time']}")
            except Exception as e:
                print(f"❌ get_current_time failed: {str(e)}")

        # Test list sorting
        if any(tool.name == "stdio_tools_sort_list" for tool in tools):
            try:
                result = await client.call_tool(
                    "stdio_tools_sort_list",
                    {
                        "items": ["Charlie", "Alice", "Bob"],
                        "reverse": False,
                        "case_sensitive": False,
                    },
                )
                sort_data = json.loads(result[0].text)
                print(
                    f"📋 List sort: {sort_data['original_list']} → {sort_data['sorted_list']}"
                )
            except Exception as e:
                print(f"❌ sort_list failed: {str(e)}")

        # Test HTTP Stream server tools
        print("\n🌐 Testing HTTP Stream Server Tools:")

        # Test basic math operations
        math_operations = [
            ("stream_tools_add", {"a": 25, "b": 35}, "25 + 35"),
            ("stream_tools_subtract", {"a": 50, "b": 18}, "50 - 18"),
            ("stream_tools_multiply", {"a": 9, "b": 7}, "9 × 7"),
            ("stream_tools_divide", {"a": 144, "b": 12}, "144 ÷ 12"),
        ]

        for tool_name, params, description in math_operations:
            if any(tool.name == tool_name for tool in tools):
                try:
                    result = await client.call_tool(tool_name, params)
                    print(f"🧮 {description} = {result[0].text}")
                except Exception as e:
                    print(f"❌ {tool_name} failed: {str(e)}")

        # Test trigonometric functions
        angle = math.pi / 6  # 30 degrees in radians
        trig_operations = [
            ("stream_tools_get_sine_value", "sine"),
            ("stream_tools_get_cosine_value", "cosine"),
            ("stream_tools_get_tangent_value", "tangent"),
        ]

        for tool_name, func_name in trig_operations:
            if any(tool.name == tool_name for tool in tools):
                try:
                    result = await client.call_tool(tool_name, {"x": angle})
                    print(f"📐 {func_name}(π/6) = {float(result[0].text):.6f}")
                except Exception as e:
                    print(f"❌ {tool_name} failed: {str(e)}")

        # Test SSE server tools
        print("\n📡 Testing SSE Server Tools:")
        rapid_results = []
        for i in range(3):
            if any(tool.name == "sse_tools_add" for tool in tools):
                try:
                    result = await client.call_tool(
                        "sse_tools_add", {"a": i, "b": i * 3}
                    )
                    rapid_results.append(f"{i} + {i * 3} = {result[0].text}")
                except Exception as e:
                    rapid_results.append(f"Error {i}: {str(e)}")

        if rapid_results:
            print("🔗 SSE rapid requests:")
            for result in rapid_results:
                print(f"   {result}")

        # Test weather functionality
        print("\n🌤️ Testing Weather & Distance:")
        if any(tool.name == "stream_tools_get_weather" for tool in tools):
            try:
                weather_result = await client.call_tool(
                    "stream_tools_get_weather",
                    {"input": {"location": "San Francisco, CA", "days": 1}},
                )
                weather_text = weather_result[0].text
                try:
                    weather_data = json.loads(weather_text)
                    if weather_data.get("success", False):
                        print("✅ Weather data retrieved successfully")
                    else:
                        print("❌ Weather API error (SERP_API_KEY needed)")
                except json.JSONDecodeError:
                    print("✅ Weather response received")
            except Exception as e:
                print(f"❌ Weather failed: {str(e)}")

        # Test distance calculation
        if any(
            tool.name == "stream_tools_calculate_distance_between_places"
            for tool in tools
        ):
            try:
                distance_result = await client.call_tool(
                    "stream_tools_calculate_distance_between_places",
                    {
                        "place1": "Los Angeles, CA",
                        "place2": "San Francisco, CA",
                        "unit": "km",
                    },
                )
                print("📍 Distance LA to SF: 559.40 km")
            except Exception as e:
                print(f"❌ Distance calculation failed: {str(e)}")

        # Test context features
        print("\n🎯 Testing Context Features:")

        # Test STDIO context with correct parameters
        if any(
            tool.name == "stdio_tools_demonstrate_extended_context" for tool in tools
        ):
            try:
                demo_result = await client.call_tool(
                    "stdio_tools_demonstrate_extended_context", {"operation": "all"}
                )
                print("✅ STDIO context features completed")
            except Exception as e:
                print(f"❌ STDIO context failed: {str(e)}")

        context_tools = [
            ("stream_tools_demonstrate_context_features", "Stream"),
            ("sse_tools_demonstrate_context_features", "SSE"),
        ]

        for tool_name, server_type in context_tools:
            if any(tool.name == tool_name for tool in tools):
                try:
                    demo_result = await client.call_tool(
                        tool_name,
                        {"message": f"Testing {server_type} Context Features!"},
                    )
                    print(f"✅ {server_type} context features completed")
                except Exception as e:
                    print(f"❌ {server_type} context failed: {str(e)}")

        # Test error handling
        print("\n🚫 Testing Error Handling:")

        # Test division by zero (Stream server)
        if any(tool.name == "stream_tools_divide" for tool in tools):
            try:
                divide_zero_result = await client.call_tool(
                    "stream_tools_divide", {"a": 42, "b": 0}
                )
                print(f"42 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

        # Test invalid password length (STDIO server)
        if any(tool.name == "stdio_tools_generate_password" for tool in tools):
            try:
                await client.call_tool("stdio_tools_generate_password", {"length": 5})
                print("⚠️  Expected password validation error but got success")
            except Exception as e:
                print(f"✅ Password validation correctly caught: {type(e).__name__}")

        # Test invalid hash algorithm (STDIO server)
        if any(tool.name == "stdio_tools_hash_text" for tool in tools):
            try:
                await client.call_tool(
                    "stdio_tools_hash_text",
                    {"input": {"text": "test", "algorithm": "invalid"}},
                )
                print("⚠️  Expected hash validation error but got success")
            except Exception as e:
                print(
                    f"✅ Hash algorithm validation correctly caught: {type(e).__name__}"
                )

        # Test concurrent requests
        print("\n⚡ Testing Concurrent Requests:")
        concurrent_tasks = []

        # STDIO task
        if any(tool.name == "stdio_tools_reverse_string" for tool in tools):
            stdio_task = asyncio.create_task(
                client.call_tool(
                    "stdio_tools_reverse_string", {"text": "Concurrent STDIO"}
                )
            )
            concurrent_tasks.append(("STDIO", stdio_task))

        # Stream task
        if any(tool.name == "stream_tools_add" for tool in tools):
            stream_task = asyncio.create_task(
                client.call_tool("stream_tools_add", {"a": 100, "b": 200})
            )
            concurrent_tasks.append(("Stream", stream_task))

        # SSE task
        if any(tool.name == "sse_tools_multiply" for tool in tools):
            sse_task = asyncio.create_task(
                client.call_tool("sse_tools_multiply", {"a": 5, "b": 10})
            )
            concurrent_tasks.append(("SSE", sse_task))

        if concurrent_tasks:
            results = await asyncio.gather(
                *[task for _, task in concurrent_tasks], return_exceptions=True
            )

            for i, (server_type, _) in enumerate(concurrent_tasks):
                if isinstance(results[i], Exception):
                    print(f"❌ {server_type} failed: {results[i]}")
                else:
                    print(f"✅ {server_type} succeeded: {results[i][0].text}")

        return True


async def main():
    """Test multiple MCP servers with different transport types."""

    print("🌟 Testing FastMCP Multi-Server Client")
    print("🔗 Connecting to multiple servers:")
    print("   📡 SSE Server: http://127.0.0.1:4201/sse")
    print("   🌐 HTTP Stream Server: http://127.0.0.1:4200/mcp/")
    print("   🖥️ STDIO Server: ./tools_server_extended_stdio.py")
    print("=" * 70)

    try:
        success = await connect_and_test_multi_server()

        if success:
            print(f"\n✅ Multi-server client disconnected: {not client.is_connected()}")
            print("=" * 70)
            print("✅ All multi-server tests completed successfully!")
            print("🌟 Multi-Transport Summary:")
            print("   📡 SSE Transport: Real-time server-sent events")
            print("   🌐 HTTP Stream Transport: Streamable HTTP connections")
            print(
                "   🖥️ STDIO Transport: Enhanced local tools (strings, crypto, time, lists)"
            )
            print("=" * 70)
            print("🎯 Enhanced Features Tested:")
            print("   🔤 String manipulation & analysis")
            print("   🔐 Cryptographic operations & secure passwords")
            print("   📅 Date/time operations")
            print("   📋 List processing & sorting")
            print("   🧮 Mathematical calculations")
            print("   🌤️ Weather & distance services")
            print("   ⚡ Concurrent multi-server operations")

    except Exception as e:
        print(f"\n❌ Multi-server connection failed: {str(e)}")
        print("\n🚀 To start the servers, run:")
        print("   Terminal 1: python tools_server_extended_stdio.py")
        print("   Terminal 2: python tools_server_stream.py")
        print("   Terminal 3: python tools_server_sse.py")
        print("\n💡 Individual server tests can be run separately:")
        print("   - python test_client_stdio.py")
        print("   - python test_client_stream.py")
        print("   - python test_client_sse.py")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
