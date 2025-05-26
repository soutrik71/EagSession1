from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import asyncio
import json
import math
import logging
import sys
import os
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

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

streaming_server_url = "http://127.0.0.1:4200/mcp/"

try:
    transport = StreamableHttpTransport(url=streaming_server_url)
    client = Client(transport)
except Exception as e:
    print(f"Error with StreamableHttpTransport: {e}")
    raise e


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((ConnectionError, RuntimeError, Exception)),
    reraise=True,
)
async def connect_and_test():
    """Attempt to connect and run tests with retry logic."""
    async with client:
        print(f"✅ Client connected: {client.is_connected()}")

        # List available tools
        tools = await client.list_tools()
        print(f"\n📋 Available tools ({len(tools)}): {[tool.name for tool in tools]}")

        # Test basic math operations
        print("\n🔢 Testing Basic Math Operations:")
        print("-" * 40)

        math_tools = ["add", "subtract", "multiply", "divide"]
        for tool_name in math_tools:
            if any(tool.name == tool_name for tool in tools):
                try:
                    if tool_name == "add":
                        result = await client.call_tool(tool_name, {"a": 25, "b": 35})
                        print(f"🧮 25 + 35 = {result[0].text}")
                    elif tool_name == "subtract":
                        result = await client.call_tool(tool_name, {"a": 50, "b": 18})
                        print(f"🧮 50 - 18 = {result[0].text}")
                    elif tool_name == "multiply":
                        result = await client.call_tool(tool_name, {"a": 9, "b": 7})
                        print(f"🧮 9 × 7 = {result[0].text}")
                    elif tool_name == "divide":
                        result = await client.call_tool(tool_name, {"a": 144, "b": 12})
                        print(f"🧮 144 ÷ 12 = {result[0].text}")
                except Exception as e:
                    print(f"❌ {tool_name} failed: {str(e)}")

        # Test trigonometric functions
        print("\n📐 Testing Trigonometric Functions:")
        print("-" * 35)

        angle = math.pi / 6  # 30 degrees in radians
        trig_tools = ["get_sine_value", "get_cosine_value", "get_tangent_value"]

        for tool_name in trig_tools:
            if any(tool.name == tool_name for tool in tools):
                try:
                    result = await client.call_tool(tool_name, {"x": angle})
                    func_name = tool_name.replace("get_", "").replace("_value", "")
                    print(f"🧮 {func_name}(π/6) = {float(result[0].text):.6f}")
                except Exception as e:
                    print(f"❌ {tool_name} failed: {str(e)}")

        # Test logarithm functions
        print("\n📊 Testing Logarithm Functions:")
        print("-" * 30)

        if any(tool.name == "get_log_value" for tool in tools):
            try:
                # Test log base 10
                log_result = await client.call_tool("get_log_value", {"x": 1000})
                print(f"🧮 log₁₀(1000) = {log_result[0].text}")

                # Test log base 2
                log_result_custom = await client.call_tool(
                    "get_log_value", {"x": 16, "base": 2}
                )
                print(f"🧮 log₂(16) = {log_result_custom[0].text}")
            except Exception as e:
                print(f"❌ Logarithm test failed: {str(e)}")

        # Test distance calculation
        print("\n🌍 Testing Distance Calculation:")
        print("-" * 35)

        if any(tool.name == "calculate_distance_between_places" for tool in tools):
            try:
                distance_result = await client.call_tool(
                    "calculate_distance_between_places",
                    {
                        "place1": "Los Angeles, CA",
                        "place2": "San Francisco, CA",
                        "unit": "km",
                    },
                )
                print("📍 Distance LA to SF:")
                print(distance_result[0].text)
            except Exception as e:
                print(f"❌ Distance calculation failed: {str(e)}")

        # Test weather functionality
        print("\n🌤️ Testing Weather Information:")
        print("-" * 30)

        if any(tool.name == "get_weather" for tool in tools):
            try:
                weather_result = await client.call_tool(
                    "get_weather",
                    {"input": {"location": "San Francisco, CA", "days": 1}},
                )
                weather_text = weather_result[0].text
                try:
                    weather_data = json.loads(weather_text)
                    if weather_data.get("success", False):
                        print("✅ Weather data retrieved successfully:")
                        print(weather_data["weather_info"])
                    else:
                        print(
                            f"❌ Weather Error: {weather_data.get('error_message', 'Unknown error')}"
                        )
                        if "SERP_API_KEY" in weather_data.get("error_message", ""):
                            print(
                                "💡 Tip: Set your SERP_API_KEY in a .env file to enable weather functionality"
                            )
                except json.JSONDecodeError:
                    print(f"Raw weather response: {weather_text}")
            except Exception as e:
                print(f"❌ Weather test failed: {str(e)}")

        # Test string operations if available
        if any(tool.name == "reverse_string" for tool in tools):
            print("\n🔤 Testing String Operations:")
            print("-" * 25)
            try:
                result = await client.call_tool(
                    "reverse_string", {"text": "Hello, World!"}
                )
                print(f"🧮 Reverse 'Hello, World!' = {result[0].text}")
            except Exception as e:
                print(f"❌ String reverse failed: {str(e)}")

        # Test HTTP-specific functionality
        print("\n🌐 Testing HTTP Stream Specific Features:")
        print("-" * 45)

        print("🔗 Testing multiple rapid requests (HTTP stream performance)...")
        rapid_results = []
        for i in range(5):
            if any(tool.name == "add" for tool in tools):
                try:
                    result = await client.call_tool("add", {"a": i, "b": i * 2})
                    rapid_results.append(f"{i} + {i * 2} = {result[0].text}")
                except Exception as e:
                    rapid_results.append(f"Error in rapid test {i}: {str(e)}")

        print("✅ Rapid requests completed:")
        for result in rapid_results:
            print(f"   {result}")

        # Test error handling
        print("\n🚫 Testing Error Handling (HTTP Stream):")
        print("-" * 40)

        if any(tool.name == "divide" for tool in tools):
            try:
                print("🧮 Testing 42 ÷ 0 (should trigger error)...")
                divide_zero_result = await client.call_tool("divide", {"a": 42, "b": 0})
                print(f"42 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

        return True


async def main():
    """Test the HTTP stream server with various mathematical operations, distance calculation, and weather."""

    print("🌐 Testing FastMCP HTTP Stream Server")
    print(f"🔗 Connecting to: {streaming_server_url}")
    print("=" * 60)

    try:
        # Attempt to connect and run tests with retry logic
        success = await connect_and_test()

        if success:
            print(f"\n✅ Client disconnected: {not client.is_connected()}")
            print("=" * 60)
            print("✅ All HTTP stream tests completed successfully!")
            print("🌐 HTTP Transport: Connected to http://127.0.0.1:4200/mcp/")
            print(
                "📝 Note: Context logging and progress reporting sent through HTTP stream"
            )
            print("=" * 60)

    except Exception as e:
        print("\n❌ Connection failed after 2 retry attempts")
        print(f"🔌 Server may not be running at: {streaming_server_url}")
        print(f"💡 Error details: {str(e)}")
        print("\n🚀 To start the server, run:")
        print("   python tools_server_stream.py")
        print("   Server should be available at http://127.0.0.1:4200/mcp/")
        print("\n📋 Troubleshooting:")
        print("   1. Check if the server is running on the correct port (4200)")
        print("   2. Verify the server URL is accessible")
        print("   3. Check firewall settings")
        print("   4. Ensure no other service is using port 4200")
        print("=" * 60)
        print("❌ Test execution failed gracefully - server connection unavailable")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
