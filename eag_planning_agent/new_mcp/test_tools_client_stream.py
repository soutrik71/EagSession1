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
    """Test the HTTP stream tools server with various mathematical operations, distance calculation, and weather."""

    print("🌐 Testing FastMCP HTTP Stream Tools Server")
    print("🔗 Connecting to: http://127.0.0.1:4200/mcp/")
    print("=" * 60)

    # Create client using HTTP transport to the stream server
    # Use 127.0.0.1 instead of localhost and disable SSL verification for local testing
    client = Client("http://127.0.0.1:4200/mcp/")

    try:
        async with client:
            print(f"✅ Connected to HTTP stream server: {client.is_connected()}")

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
                    {"message": "Testing FastMCP HTTP Stream Context Features!"},
                )
                print("✅ Context demonstration completed:")
                print(demo_result[0].text)
            except Exception as e:
                print(f"❌ Context demonstration failed: {str(e)}")

            print("\n🧮 Running context demonstration with a long message...")
            print("   (This should trigger a warning in the context logging)")
            try:
                long_message = (
                    "This is a very long message for HTTP stream testing " * 5
                )  # Make it > 100 chars
                demo_result_long = await client.call_tool(
                    "demonstrate_context_features", {"message": long_message}
                )
                print("✅ Long message demonstration completed:")
                print(demo_result_long[0].text)
            except Exception as e:
                print(f"❌ Long message demonstration failed: {str(e)}")

            # Test basic math operations with context logging
            print("\n🔢 Testing Basic Math Operations (HTTP Stream with Context):")
            print("-" * 60)

            print("🧮 Testing 25 + 35...")
            add_result = await client.call_tool("add", {"a": 25, "b": 35})
            print(f"Result: 25 + 35 = {add_result[0].text}")

            print("\n🧮 Testing 50 - 18...")
            subtract_result = await client.call_tool("subtract", {"a": 50, "b": 18})
            print(f"Result: 50 - 18 = {subtract_result[0].text}")

            print("\n🧮 Testing 9 × 7...")
            multiply_result = await client.call_tool("multiply", {"a": 9, "b": 7})
            print(f"Result: 9 × 7 = {multiply_result[0].text}")

            print("\n🧮 Testing 144 ÷ 12...")
            divide_result = await client.call_tool("divide", {"a": 144, "b": 12})
            print(f"Result: 144 ÷ 12 = {divide_result[0].text}")

            # Test division by zero error handling
            print("\n🚫 Testing Error Handling (HTTP Stream with Context):")
            print("-" * 55)
            try:
                print("🧮 Testing 42 ÷ 0 (should trigger context error logging)...")
                divide_zero_result = await client.call_tool("divide", {"a": 42, "b": 0})
                print(f"42 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

            # Test log with invalid inputs
            try:
                print("\n🧮 Testing log(-10) (should trigger context error logging)...")
                log_negative = await client.call_tool("get_log_value", {"x": -10})
                print(f"log(-10) = {log_negative[0].text}")
            except Exception as e:
                print(f"✅ Negative log correctly caught: {type(e).__name__}")

            # Test trigonometric functions with context logging
            print("\n📐 Testing Trigonometric Functions (HTTP Stream):")
            print("-" * 50)

            import math

            angle = math.pi / 6  # 30 degrees in radians

            print(f"🧮 Testing sin(π/6) = sin({angle:.6f})...")
            sine_result = await client.call_tool("get_sine_value", {"x": angle})
            print(f"Result: sin(π/6) = {float(sine_result[0].text):.6f}")

            print(f"\n🧮 Testing cos(π/6) = cos({angle:.6f})...")
            cosine_result = await client.call_tool("get_cosine_value", {"x": angle})
            print(f"Result: cos(π/6) = {float(cosine_result[0].text):.6f}")

            print(f"\n🧮 Testing tan(π/6) = tan({angle:.6f})...")
            tangent_result = await client.call_tool("get_tangent_value", {"x": angle})
            print(f"Result: tan(π/6) = {float(tangent_result[0].text):.6f}")

            # Test logarithm with default and custom base
            print("\n📊 Testing Logarithm Functions (HTTP Stream):")
            print("-" * 45)

            print("🧮 Testing log₁₀(1000)...")
            log_result = await client.call_tool("get_log_value", {"x": 1000})
            print(f"Result: log₁₀(1000) = {log_result[0].text}")

            print("\n🧮 Testing log₂(16)...")
            log_result_custom = await client.call_tool(
                "get_log_value", {"x": 16, "base": 2}
            )
            print(f"Result: log₂(16) = {log_result_custom[0].text}")

            print(f"\n🧮 Testing ln(e²) = log_e({math.e**2:.6f})...")
            log_result_natural = await client.call_tool(
                "get_log_value", {"x": math.e**2, "base": math.e}
            )
            print(f"Result: ln(e²) = {float(log_result_natural[0].text):.6f}")

            # Test distance calculation between places with progress reporting
            print("\n🌍 Testing Distance Calculation (HTTP Stream with Progress):")
            print("-" * 65)

            print("📍 Calculating distance between Los Angeles and San Francisco...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result = await client.call_tool(
                "calculate_distance_between_places",
                {
                    "place1": "Los Angeles, CA",
                    "place2": "San Francisco, CA",
                    "unit": "km",
                },
            )
            print("Result:")
            print(distance_result[0].text)

            print("\n📍 Calculating distance between Berlin and Munich (in miles)...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_miles = await client.call_tool(
                "calculate_distance_between_places",
                {
                    "place1": "Berlin, Germany",
                    "place2": "Munich, Germany",
                    "unit": "miles",
                },
            )
            print("Result:")
            print(distance_result_miles[0].text)

            print("\n📍 Calculating distance between Toronto and Vancouver...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_ca = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Toronto, Canada", "place2": "Vancouver, Canada"},
            )
            print("Result:")
            print(distance_result_ca[0].text)

            # Test distance calculation error handling
            print("\n🚫 Testing Distance Calculation Error Handling (HTTP Stream):")
            print("-" * 60)

            print(
                "🧮 Testing empty place name (should trigger context error logging)..."
            )
            invalid_distance = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "", "place2": "Paris, France"},
            )
            print(f"Empty place name result: {invalid_distance[0].text}")

            print("\n🧮 Testing invalid unit (should trigger context error logging)...")
            invalid_unit = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Madrid", "place2": "Barcelona", "unit": "lightyears"},
            )
            print(f"Invalid unit result: {invalid_unit[0].text}")

            # Test weather functionality with comprehensive context logging
            print("\n🌤️ Testing Weather Information (HTTP Stream with Context):")
            print("-" * 65)

            # Test with a well-known location
            print("🌡️ Getting current weather for San Francisco...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_result = await client.call_tool(
                    "get_weather",
                    {"input": {"location": "San Francisco, CA", "days": 1}},
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
            print("\n🌡️ Getting 5-day weather forecast for Chicago...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_forecast = await client.call_tool(
                    "get_weather", {"input": {"location": "Chicago, IL", "days": 5}}
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
            print("\n🧪 Testing Weather Error Handling (HTTP Stream):")
            print("-" * 50)

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
                "\n🧮 Testing invalid days (15 days, should trigger context error logging)..."
            )
            try:
                invalid_days = await client.call_tool(
                    "get_weather", {"input": {"location": "Miami, FL", "days": 15}}
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

            # Test HTTP-specific functionality
            print("\n🌐 Testing HTTP Stream Specific Features:")
            print("-" * 45)

            print("🔗 Testing multiple rapid requests (HTTP stream performance)...")
            rapid_results = []
            for i in range(5):
                result = await client.call_tool("add", {"a": i, "b": i * 2})
                rapid_results.append(f"{i} + {i * 2} = {result[0].text}")

            print("✅ Rapid requests completed:")
            for result in rapid_results:
                print(f"   {result}")

        print("\n" + "=" * 60)
        print("✅ All HTTP stream tests completed successfully!")
        print("🌐 HTTP Transport: Connected to http://127.0.0.1:4200/mcp/")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent through the HTTP stream to the MCP client")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 60)

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the HTTP stream server is running:")
        print("   python tools_server_stream.py")
        print("   Server should be available at http://127.0.0.1:4200/mcp/")
    except Exception as e:
        print(f"\n❌ Error during HTTP stream testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
