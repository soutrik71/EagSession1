#!/usr/bin/env python3
"""
Test script for server1.py (Calculator Server) only
"""

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
import asyncio
import math
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
    os.path.join(os.path.dirname(__file__), "server1.py")
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
    """Parse JSON result and extract the result value"""
    try:
        data = json.loads(result_text)
        return data.get("result", result_text)
    except (json.JSONDecodeError, AttributeError):
        return result_text


async def test_server1():
    """Test server1.py calculator functions"""
    print("\n🧮 Testing Calculator Server (server1.py)")
    print("=" * 50)

    async with client:
        print(f"✅ Connected to server1: {client.is_connected()}")

        # List available tools
        tools = await client.list_tools()
        print(f"📋 Available tools ({len(tools)}):")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")

        print("\n🔢 Testing basic math operations:")

        # Test basic operations - using correct input structure
        try:
            result = await client.call_tool("add", {"input": {"a": 15, "b": 25}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ add(15, 25) = {parsed_result}")
        except Exception as e:
            print(f"❌ add failed: {e}")

        try:
            result = await client.call_tool("multiply", {"input": {"a": 7, "b": 8}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ multiply(7, 8) = {parsed_result}")
        except Exception as e:
            print(f"❌ multiply failed: {e}")

        try:
            result = await client.call_tool("factorial", {"input": {"a": 5}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ factorial(5) = {parsed_result}")
        except Exception as e:
            print(f"❌ factorial failed: {e}")

        try:
            result = await client.call_tool("subtract", {"input": {"a": 50, "b": 18}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ subtract(50, 18) = {parsed_result}")
        except Exception as e:
            print(f"❌ subtract failed: {e}")

        try:
            result = await client.call_tool("power", {"input": {"a": 2, "b": 8}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ power(2, 8) = {parsed_result}")
        except Exception as e:
            print(f"❌ power failed: {e}")

        try:
            result = await client.call_tool("cbrt", {"input": {"a": 27}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ cbrt(27) = {parsed_result}")
        except Exception as e:
            print(f"❌ cbrt failed: {e}")

        try:
            result = await client.call_tool("remainder", {"input": {"a": 17, "b": 5}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ remainder(17, 5) = {parsed_result}")
        except Exception as e:
            print(f"❌ remainder failed: {e}")

        print("\n📐 Testing trigonometric functions:")
        angle = math.pi / 6  # 30 degrees

        try:
            result = await client.call_tool("sin", {"input": {"a": angle}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ sin(π/6) = {float(parsed_result):.6f}")
        except Exception as e:
            print(f"❌ sin failed: {e}")

        try:
            result = await client.call_tool("cos", {"input": {"a": angle}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ cos(π/6) = {float(parsed_result):.6f}")
        except Exception as e:
            print(f"❌ cos failed: {e}")

        try:
            result = await client.call_tool("tan", {"input": {"a": angle}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ tan(π/6) = {float(parsed_result):.6f}")
        except Exception as e:
            print(f"❌ tan failed: {e}")

        print("\n🔧 Testing special operations:")

        try:
            result = await client.call_tool("mine", {"input": {"a": 10, "b": 3}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ mine(10, 3) = {parsed_result}")
        except Exception as e:
            print(f"❌ mine failed: {e}")

        try:
            result = await client.call_tool("fibonacci_numbers", {"input": {"n": 8}})
            parsed_result = parse_result(result[0].text)
            print(f"✅ fibonacci(8) = {parsed_result}")
        except Exception as e:
            print(f"❌ fibonacci failed: {e}")

        try:
            result = await client.call_tool(
                "strings_to_chars_to_int", {"input": {"string": "Hello"}}
            )
            parsed_result = parse_result(result[0].text)
            print(f"✅ ASCII values of 'Hello': {parsed_result}")
        except Exception as e:
            print(f"❌ strings_to_chars_to_int failed: {e}")

        try:
            result = await client.call_tool(
                "int_list_to_exponential_sum", {"input": {"numbers": [1, 2, 3]}}
            )
            parsed_result = parse_result(result[0].text)
            print(f"✅ Exponential sum of [1,2,3]: {float(parsed_result):.4f}")
        except Exception as e:
            print(f"❌ int_list_to_exponential_sum failed: {e}")

        print("\n🖼️ Testing image operations:")

        try:
            # This will likely fail without a real image, but we test the tool exists
            result = await client.call_tool(
                "create_thumbnail", {"input": {"image_path": "test.jpg"}}
            )
            parsed_result = parse_result(result[0].text)
            print(f"✅ create_thumbnail executed: {parsed_result}")
        except Exception as e:
            print(f"⚠️  create_thumbnail failed (expected): {type(e).__name__}")

        print("\n🚫 Testing error handling:")

        try:
            result = await client.call_tool("divide", {"input": {"a": 42, "b": 0}})
            parsed_result = parse_result(result[0].text)
            print(f"⚠️  Expected error but got: {parsed_result}")
        except Exception as e:
            print(f"✅ Division by zero correctly caught: {type(e).__name__}")

        try:
            result = await client.call_tool("factorial", {"input": {"a": 200}})
            parsed_result = parse_result(result[0].text)
            print(f"⚠️  Expected factorial overflow error but got: {parsed_result}")
        except Exception as e:
            print(f"✅ Factorial overflow correctly caught: {type(e).__name__}")

    print(f"\n✅ Client disconnected: {not client.is_connected()}")


if __name__ == "__main__":
    print("🌟 Testing Server1 (Calculator) Independently")
    print(f"🔗 Using Python command: {successful_python_cmd}")
    print(f"📁 Server script: {server_script_path}")
    print("=" * 50)

    try:
        asyncio.run(test_server1())
        print("\n✅ Server1 test completed!")
        print("\n📊 Test Summary:")
        print(
            "   🔢 Basic Math: add, subtract, multiply, divide, power, cbrt, remainder"
        )
        print("   📐 Trigonometry: sin, cos, tan")
        print("   🔧 Special: mine, fibonacci, ASCII conversion, exponential sum")
        print("   🖼️ Image: create_thumbnail (expected to fail without image)")
        print("   🚫 Error Handling: division by zero, factorial overflow")
    except Exception as e:
        print(f"\n❌ Server1 test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if server1.py exists and is executable")
        print("   2. Verify Python installation and PATH")
        print("   3. Try running the server script directly:")
        print(f"      {successful_python_cmd} {server_script_path}")
        print("   4. Check for any import errors in server1.py")
        import traceback

        traceback.print_exc()
