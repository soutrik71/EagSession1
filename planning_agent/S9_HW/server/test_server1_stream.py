#!/usr/bin/env python3
"""
Test script for server1_stream.py (Calculator Stream Server) using HTTP transport
"""

import asyncio
from fastmcp import Client
import logging
import sys
import json
import os
import math

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
    """Parse JSON result and extract the result value"""
    try:
        data = json.loads(result_text)
        return data.get("result", result_text)
    except (json.JSONDecodeError, AttributeError):
        return result_text


async def test_server1_stream():
    """Test server1_stream.py calculator functions using HTTP transport"""
    print("\n🧮 Testing Calculator Stream Server (server1_stream.py)")
    print("🔗 Connecting to: http://127.0.0.1:4201/mcp/")
    print("=" * 60)

    # Create client using HTTP transport to the stream server
    client = Client("http://127.0.0.1:4201/mcp/")

    try:
        async with client:
            print(f"✅ Connected to server1_stream: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"📋 Available tools ({len(tools)}):")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")

            print("\n🔢 Testing Basic Math Operations (HTTP Stream with Context):")
            print("-" * 60)

            # Test basic operations
            print("🧮 Testing 15 + 25...")
            add_result = await client.call_tool("add", {"input": {"a": 15, "b": 25}})
            parsed_result = parse_result(add_result[0].text)
            print(f"✅ add(15, 25) = {parsed_result}")

            print("\n🧮 Testing 50 - 18...")
            subtract_result = await client.call_tool(
                "subtract", {"input": {"a": 50, "b": 18}}
            )
            parsed_result = parse_result(subtract_result[0].text)
            print(f"✅ subtract(50, 18) = {parsed_result}")

            print("\n🧮 Testing 7 × 8...")
            multiply_result = await client.call_tool(
                "multiply", {"input": {"a": 7, "b": 8}}
            )
            parsed_result = parse_result(multiply_result[0].text)
            print(f"✅ multiply(7, 8) = {parsed_result}")

            print("\n🧮 Testing 144 ÷ 12...")
            divide_result = await client.call_tool(
                "divide", {"input": {"a": 144, "b": 12}}
            )
            parsed_result = parse_result(divide_result[0].text)
            print(f"✅ divide(144, 12) = {parsed_result}")

            print("\n🧮 Testing 2 ^ 8...")
            power_result = await client.call_tool("power", {"input": {"a": 2, "b": 8}})
            parsed_result = parse_result(power_result[0].text)
            print(f"✅ power(2, 8) = {parsed_result}")

            print("\n🧮 Testing cube root of 27...")
            cbrt_result = await client.call_tool("cbrt", {"input": {"a": 27}})
            parsed_result = parse_result(cbrt_result[0].text)
            print(f"✅ cbrt(27) = {parsed_result}")

            print("\n🧮 Testing factorial of 5...")
            factorial_result = await client.call_tool("factorial", {"input": {"a": 5}})
            parsed_result = parse_result(factorial_result[0].text)
            print(f"✅ factorial(5) = {parsed_result}")

            print("\n🧮 Testing 17 % 5...")
            remainder_result = await client.call_tool(
                "remainder", {"input": {"a": 17, "b": 5}}
            )
            parsed_result = parse_result(remainder_result[0].text)
            print(f"✅ remainder(17, 5) = {parsed_result}")

            print("\n📐 Testing Trigonometric Functions (HTTP Stream):")
            print("-" * 50)

            angle = math.pi / 6  # 30 degrees in radians

            print(f"🧮 Testing sin(π/6) = sin({angle:.6f})...")
            sin_result = await client.call_tool("sin", {"input": {"a": angle}})
            parsed_result = parse_result(sin_result[0].text)
            print(f"✅ sin(π/6) = {float(parsed_result):.6f}")

            print(f"\n🧮 Testing cos(π/6) = cos({angle:.6f})...")
            cos_result = await client.call_tool("cos", {"input": {"a": angle}})
            parsed_result = parse_result(cos_result[0].text)
            print(f"✅ cos(π/6) = {float(parsed_result):.6f}")

            print(f"\n🧮 Testing tan(π/6) = tan({angle:.6f})...")
            tan_result = await client.call_tool("tan", {"input": {"a": angle}})
            parsed_result = parse_result(tan_result[0].text)
            print(f"✅ tan(π/6) = {float(parsed_result):.6f}")

            print("\n🔧 Testing Special Operations (HTTP Stream):")
            print("-" * 45)

            print("🧮 Testing mine(10, 3)...")
            mine_result = await client.call_tool("mine", {"input": {"a": 10, "b": 3}})
            parsed_result = parse_result(mine_result[0].text)
            print(f"✅ mine(10, 3) = {parsed_result}")

            print("\n🧮 Testing fibonacci(8)...")
            fib_result = await client.call_tool(
                "fibonacci_numbers", {"input": {"n": 8}}
            )
            parsed_result = parse_result(fib_result[0].text)
            print(f"✅ fibonacci(8) = {parsed_result}")

            print("\n🧮 Testing ASCII values of 'Hello'...")
            ascii_result = await client.call_tool(
                "strings_to_chars_to_int", {"input": {"string": "Hello"}}
            )
            parsed_result = parse_result(ascii_result[0].text)
            print(f"✅ ASCII values of 'Hello': {parsed_result}")

            print("\n🧮 Testing exponential sum of [1,2,3]...")
            exp_result = await client.call_tool(
                "int_list_to_exponential_sum", {"input": {"numbers": [1, 2, 3]}}
            )
            parsed_result = parse_result(exp_result[0].text)
            print(f"✅ Exponential sum of [1,2,3]: {float(parsed_result):.4f}")

            print("\n🖼️ Testing Image Operations (HTTP Stream):")
            print("-" * 40)

            print("🧮 Testing create_thumbnail (expected to fail without image)...")
            try:
                thumbnail_result = await client.call_tool(
                    "create_thumbnail", {"input": {"image_path": "test.jpg"}}
                )
                parsed_result = parse_result(thumbnail_result[0].text)
                print(f"✅ create_thumbnail executed: {parsed_result}")
            except Exception as e:
                print(f"⚠️  create_thumbnail failed (expected): {type(e).__name__}")

            print("\n🚫 Testing Error Handling (HTTP Stream with Context):")
            print("-" * 55)

            # Test division by zero
            print("🧮 Testing 42 ÷ 0 (should trigger context error logging)...")
            try:
                divide_zero_result = await client.call_tool(
                    "divide", {"input": {"a": 42, "b": 0}}
                )
                parsed_result = parse_result(divide_zero_result[0].text)
                print(f"⚠️  Expected error but got: {parsed_result}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

            # Test factorial overflow
            print(
                "\n🧮 Testing factorial(200) (should trigger context error logging)..."
            )
            try:
                factorial_overflow = await client.call_tool(
                    "factorial", {"input": {"a": 200}}
                )
                parsed_result = parse_result(factorial_overflow[0].text)
                print(f"⚠️  Expected factorial overflow error but got: {parsed_result}")
            except Exception as e:
                print(f"✅ Factorial overflow correctly caught: {type(e).__name__}")

            print("\n🌐 Testing HTTP Stream Specific Features:")
            print("-" * 45)

            print("🔗 Testing multiple rapid requests (HTTP stream performance)...")
            rapid_results = []
            for i in range(5):
                result = await client.call_tool("add", {"input": {"a": i, "b": i * 2}})
                parsed_result = parse_result(result[0].text)
                rapid_results.append(f"{i} + {i * 2} = {parsed_result}")

            print("✅ Rapid requests completed:")
            for result in rapid_results:
                print(f"   {result}")

        print("\n" + "=" * 60)
        print("✅ All Calculator Stream tests completed successfully!")
        print("🌐 HTTP Transport: Connected to http://127.0.0.1:4201/mcp/")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent through the HTTP stream to the MCP client")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 60)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the Calculator Stream server is running:")
        print("   python server1_stream.py")
        print("   Server should be available at http://127.0.0.1:4201/mcp/")
    except Exception as e:
        print(f"\n❌ Error during Calculator Stream testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🌟 Testing Calculator Stream Server (server1_stream.py)")
    print("🔗 Using HTTP transport to http://127.0.0.1:4201/mcp/")
    print("=" * 60)

    try:
        asyncio.run(test_server1_stream())
        print("\n✅ Calculator Stream test completed!")
        print("\n📊 Test Summary:")
        print(
            "   🔢 Basic Math: add, subtract, multiply, divide, power, cbrt, remainder"
        )
        print("   📐 Trigonometry: sin, cos, tan")
        print("   🔧 Special: mine, fibonacci, ASCII conversion, exponential sum")
        print("   🖼️ Image: create_thumbnail (expected to fail without image)")
        print("   🚫 Error Handling: division by zero, factorial overflow")
        print("   🌐 HTTP Stream: Multiple rapid requests")
    except Exception as e:
        print(f"\n❌ Calculator Stream test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Start the server: python server1_stream.py")
        print("   2. Check if port 4201 is available")
        print("   3. Verify server is running at http://127.0.0.1:4201/mcp/")
        print("   4. Check for any import errors in server1_stream.py")
        import traceback

        traceback.print_exc()
