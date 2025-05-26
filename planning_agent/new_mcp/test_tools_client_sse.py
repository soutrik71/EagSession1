import asyncio
from fastmcp import Client
import logging
import sys
import json
import os

# Disable SSL verification for local testing
os.environ.pop("SSL_CERT_FILE", None)

# ADDED: Set up logging to capture context messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ADDED: Create a logger for MCP context messages
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)


async def main():
    """Test the SSE tools server with various mathematical operations, distance calculation, and weather."""

    print("📡 Testing FastMCP SSE (Server-Sent Events) Tools Server")
    print("🔗 Connecting to: http://127.0.0.1:4201/sse")
    print("=" * 65)

    # Create client using SSE transport to the server
    # Use 127.0.0.1 instead of localhost and disable SSL verification for local testing
    client = Client("http://127.0.0.1:4201/sse")

    try:
        async with client:
            print(f"✅ Connected to SSE server: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(
                f"\n📋 Available tools ({len(tools)}): {[tool.name for tool in tools]}"
            )

            # ADDED: Test the context demonstration tool first
            print("\n🎯 Testing Context Features Demonstration:")
            print("-" * 50)

            print("🧮 Running context demonstration tool...")
            print("   (This tool explicitly showcases all context features)")
            try:
                demo_result = await client.call_tool(
                    "demonstrate_context_features",
                    {"message": "Testing FastMCP SSE Context Features!"},
                )
                print("✅ Context demonstration completed:")
                print(demo_result[0].text)
            except Exception as e:
                print(f"❌ Context demonstration failed: {str(e)}")

            print("\n🧮 Running context demonstration with a long message...")
            print("   (This should trigger a warning in the context logging)")
            try:
                long_message = (
                    "This is a very long message for SSE testing with Server-Sent Events "
                    * 4
                )  # Make it > 100 chars
                demo_result_long = await client.call_tool(
                    "demonstrate_context_features", {"message": long_message}
                )
                print("✅ Long message demonstration completed:")
                print(demo_result_long[0].text)
            except Exception as e:
                print(f"❌ Long message demonstration failed: {str(e)}")

            # Test basic math operations with context logging
            print("\n🔢 Testing Basic Math Operations (SSE with Context):")
            print("-" * 55)

            print("🧮 Testing 30 + 45...")
            add_result = await client.call_tool("add", {"a": 30, "b": 45})
            print(f"Result: 30 + 45 = {add_result[0].text}")

            print("\n🧮 Testing 80 - 23...")
            subtract_result = await client.call_tool("subtract", {"a": 80, "b": 23})
            print(f"Result: 80 - 23 = {subtract_result[0].text}")

            print("\n🧮 Testing 12 × 8...")
            multiply_result = await client.call_tool("multiply", {"a": 12, "b": 8})
            print(f"Result: 12 × 8 = {multiply_result[0].text}")

            print("\n🧮 Testing 200 ÷ 8...")
            divide_result = await client.call_tool("divide", {"a": 200, "b": 8})
            print(f"Result: 200 ÷ 8 = {divide_result[0].text}")

            # Test division by zero error handling
            print("\n🚫 Testing Error Handling (SSE with Context):")
            print("-" * 50)
            try:
                print("🧮 Testing 99 ÷ 0 (should trigger context error logging)...")
                divide_zero_result = await client.call_tool("divide", {"a": 99, "b": 0})
                print(f"99 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

            # Test log with invalid inputs
            try:
                print("\n🧮 Testing log(-15) (should trigger context error logging)...")
                log_negative = await client.call_tool("get_log_value", {"x": -15})
                print(f"log(-15) = {log_negative[0].text}")
            except Exception as e:
                print(f"✅ Negative log correctly caught: {type(e).__name__}")

            # Test trigonometric functions with context logging
            print("\n📐 Testing Trigonometric Functions (SSE):")
            print("-" * 45)

            import math

            angle = math.pi / 3  # 60 degrees in radians

            print(f"🧮 Testing sin(π/3) = sin({angle:.6f})...")
            sine_result = await client.call_tool("get_sine_value", {"x": angle})
            print(f"Result: sin(π/3) = {float(sine_result[0].text):.6f}")

            print(f"\n🧮 Testing cos(π/3) = cos({angle:.6f})...")
            cosine_result = await client.call_tool("get_cosine_value", {"x": angle})
            print(f"Result: cos(π/3) = {float(cosine_result[0].text):.6f}")

            print(f"\n🧮 Testing tan(π/3) = tan({angle:.6f})...")
            tangent_result = await client.call_tool("get_tangent_value", {"x": angle})
            print(f"Result: tan(π/3) = {float(tangent_result[0].text):.6f}")

            # Test logarithm with default and custom base
            print("\n📊 Testing Logarithm Functions (SSE):")
            print("-" * 40)

            print("🧮 Testing log₁₀(10000)...")
            log_result = await client.call_tool("get_log_value", {"x": 10000})
            print(f"Result: log₁₀(10000) = {log_result[0].text}")

            print("\n🧮 Testing log₂(32)...")
            log_result_custom = await client.call_tool(
                "get_log_value", {"x": 32, "base": 2}
            )
            print(f"Result: log₂(32) = {log_result_custom[0].text}")

            print(f"\n🧮 Testing ln(e³) = log_e({math.e**3:.6f})...")
            log_result_natural = await client.call_tool(
                "get_log_value", {"x": math.e**3, "base": math.e}
            )
            print(f"Result: ln(e³) = {float(log_result_natural[0].text):.6f}")

            # Test distance calculation between places with progress reporting
            print("\n🌍 Testing Distance Calculation (SSE with Progress):")
            print("-" * 60)

            print("📍 Calculating distance between Boston and Washington DC...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result = await client.call_tool(
                "calculate_distance_between_places",
                {
                    "place1": "Boston, MA",
                    "place2": "Washington, DC",
                    "unit": "km",
                },
            )
            print("Result:")
            print(distance_result[0].text)

            print("\n📍 Calculating distance between Rome and Milan (in miles)...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_miles = await client.call_tool(
                "calculate_distance_between_places",
                {
                    "place1": "Rome, Italy",
                    "place2": "Milan, Italy",
                    "unit": "miles",
                },
            )
            print("Result:")
            print(distance_result_miles[0].text)

            print("\n📍 Calculating distance between Seoul and Busan...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_kr = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Seoul, South Korea", "place2": "Busan, South Korea"},
            )
            print("Result:")
            print(distance_result_kr[0].text)

            # Test distance calculation error handling
            print("\n🚫 Testing Distance Calculation Error Handling (SSE):")
            print("-" * 55)

            print(
                "🧮 Testing empty place name (should trigger context error logging)..."
            )
            invalid_distance = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "", "place2": "Tokyo, Japan"},
            )
            print(f"Empty place name result: {invalid_distance[0].text}")

            print("\n🧮 Testing invalid unit (should trigger context error logging)...")
            invalid_unit = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Amsterdam", "place2": "Brussels", "unit": "parsecs"},
            )
            print(f"Invalid unit result: {invalid_unit[0].text}")

            # Test weather functionality with comprehensive context logging
            print("\n🌤️ Testing Weather Information (SSE with Context):")
            print("-" * 60)

            # Test with a well-known location
            print("🌡️ Getting current weather for Seattle...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_result = await client.call_tool(
                    "get_weather",
                    {"input": {"location": "Seattle, WA", "days": 1}},
                )
                # Parse the weather result (it's now a WeatherOutput object)
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

            # Test forecast only if the first test was successful
            print("\n🌡️ Getting 4-day weather forecast for Denver...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_forecast = await client.call_tool(
                    "get_weather", {"input": {"location": "Denver, CO", "days": 4}}
                )
                weather_forecast_text = weather_forecast[0].text
                try:
                    forecast_data = json.loads(weather_forecast_text)
                    if forecast_data.get("success", False):
                        print("✅ Weather forecast retrieved successfully:")
                        print(forecast_data["weather_info"])
                    else:
                        print(
                            f"❌ Forecast Error: {forecast_data.get('error_message', 'Unknown error')}"
                        )
                except json.JSONDecodeError:
                    print(f"Raw forecast response: {weather_forecast_text}")
            except Exception as e:
                print(f"❌ Forecast test failed: {str(e)}")

            # Test error handling
            print("\n🧪 Testing Weather Error Handling (SSE):")
            print("-" * 45)

            # Test empty location
            print("🧮 Testing empty location (should trigger context error logging)...")
            try:
                empty_location = await client.call_tool(
                    "get_weather", {"input": {"location": "", "days": 1}}
                )
                empty_text = empty_location[0].text
                try:
                    empty_data = json.loads(empty_text)
                    if not empty_data.get("success", True):
                        print(
                            f"✅ Correctly handled empty location: {empty_data.get('error_message')}"
                        )
                    else:
                        print("❌ Should have failed for empty location")
                except json.JSONDecodeError:
                    print(f"Raw empty location response: {empty_text}")
            except Exception as e:
                print(f"❌ Empty location test failed: {str(e)}")

            # Test invalid days
            print(
                "\n🧮 Testing invalid days (20 days, should trigger context error logging)..."
            )
            try:
                invalid_days = await client.call_tool(
                    "get_weather", {"input": {"location": "Phoenix, AZ", "days": 20}}
                )
                invalid_text = invalid_days[0].text
                try:
                    invalid_data = json.loads(invalid_text)
                    if not invalid_data.get("success", True):
                        print(
                            f"✅ Correctly handled invalid days: {invalid_data.get('error_message')}"
                        )
                    else:
                        print("❌ Should have failed for invalid days")
                except json.JSONDecodeError:
                    print(f"Raw invalid days response: {invalid_text}")
            except Exception as e:
                print(f"❌ Invalid days test failed: {str(e)}")

            # Test SSE-specific functionality
            print("\n📡 Testing SSE Specific Features:")
            print("-" * 40)

            print("🔄 Testing multiple rapid requests (SSE performance)...")
            rapid_results = []
            for i in range(6):
                result = await client.call_tool("add", {"a": i * 3, "b": i * 5})
                rapid_results.append(f"{i * 3} + {i * 5} = {result[0].text}")

            print("✅ Rapid requests completed:")
            for result in rapid_results:
                print(f"   {result}")

            print("\n🔄 Testing concurrent requests (SSE concurrency)...")
            # Test concurrent requests
            concurrent_tasks = []
            for i in range(3):
                task = client.call_tool("multiply", {"a": i + 1, "b": (i + 1) * 10})
                concurrent_tasks.append(task)

            concurrent_results = await asyncio.gather(*concurrent_tasks)
            print("✅ Concurrent requests completed:")
            for i, result in enumerate(concurrent_results):
                print(f"   {i + 1} × {(i + 1) * 10} = {result[0].text}")

        print("\n" + "=" * 65)
        print("✅ All SSE tests completed successfully!")
        print("📡 SSE Transport: Connected to http://127.0.0.1:4201/sse")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent through SSE (Server-Sent Events) to the MCP client")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 65)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the SSE server is running:")
        print("   python tools_server_sse.py")
        print("   or python start_sse_server.py")
        print("   Server should be available at http://127.0.0.1:4201/sse")
    except Exception as e:
        print(f"\n❌ Error during SSE testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
