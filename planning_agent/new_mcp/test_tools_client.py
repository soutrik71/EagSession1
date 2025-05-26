import asyncio
from fastmcp import Client
import logging
import sys

# Import the tools server instance
from tools_server import mcp as tools_server

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
    """Test the tools server with various mathematical operations, distance calculation, and weather."""

    print("🧮 Testing FastMCP Tools Server with Context Logging")
    print("=" * 60)

    # Create client using in-memory transport
    client = Client(tools_server)

    try:
        async with client:
            print(f"✅ Connected to tools server: {client.is_connected()}")

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
                    {"message": "Testing FastMCP Context Features!"},
                )
                print("✅ Context demonstration completed:")
                print(demo_result[0].text)
            except Exception as e:
                print(f"❌ Context demonstration failed: {str(e)}")

            print("\n🧮 Running context demonstration with a long message...")
            print("   (This should trigger a warning in the context logging)")
            try:
                long_message = (
                    "This is a very long message " * 10
                )  # Make it > 100 chars
                demo_result_long = await client.call_tool(
                    "demonstrate_context_features", {"message": long_message}
                )
                print("✅ Long message demonstration completed:")
                print(demo_result_long[0].text)
            except Exception as e:
                print(f"❌ Long message demonstration failed: {str(e)}")

            # Test basic math operations with context logging
            print("\n🔢 Testing Basic Math Operations (with Context Logging):")
            print("-" * 55)

            print("🧮 Testing 15 + 25...")
            add_result = await client.call_tool("add", {"a": 15, "b": 25})
            print(f"Result: 15 + 25 = {add_result[0].text}")

            print("\n🧮 Testing 7 × 8...")
            multiply_result = await client.call_tool("multiply", {"a": 7, "b": 8})
            print(f"Result: 7 × 8 = {multiply_result[0].text}")

            print("\n🧮 Testing 100 ÷ 4...")
            divide_result = await client.call_tool("divide", {"a": 100, "b": 4})
            print(f"Result: 100 ÷ 4 = {divide_result[0].text}")

            # Test division by zero error handling
            print("\n🚫 Testing Error Handling (with Context Logging):")
            print("-" * 50)
            try:
                print("🧮 Testing 10 ÷ 0 (should trigger context error logging)...")
                divide_zero_result = await client.call_tool("divide", {"a": 10, "b": 0})
                print(f"10 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

            # Test log with invalid inputs
            try:
                print("\n🧮 Testing log(-5) (should trigger context error logging)...")
                log_negative = await client.call_tool("get_log_value", {"x": -5})
                print(f"log(-5) = {log_negative[0].text}")
            except Exception as e:
                print(f"✅ Negative log correctly caught: {type(e).__name__}")

            # Test trigonometric functions with context logging
            print("\n📐 Testing Trigonometric Functions (with Context Logging):")
            print("-" * 60)

            import math

            angle = math.pi / 4  # 45 degrees in radians

            print(f"🧮 Testing sin(π/4) = sin({angle:.6f})...")
            sine_result = await client.call_tool("get_sine_value", {"x": angle})
            print(f"Result: sin(π/4) = {float(sine_result[0].text):.6f}")

            print(f"\n🧮 Testing cos(π/4) = cos({angle:.6f})...")
            cosine_result = await client.call_tool("get_cosine_value", {"x": angle})
            print(f"Result: cos(π/4) = {float(cosine_result[0].text):.6f}")

            print(f"\n🧮 Testing tan(π/4) = tan({angle:.6f})...")
            tangent_result = await client.call_tool("get_tangent_value", {"x": angle})
            print(f"Result: tan(π/4) = {float(tangent_result[0].text):.6f}")

            # Test logarithm with default and custom base
            print("\n📊 Testing Logarithm Functions (with Context Logging):")
            print("-" * 55)

            print("🧮 Testing log₁₀(100)...")
            log_result = await client.call_tool("get_log_value", {"x": 100})
            print(f"Result: log₁₀(100) = {log_result[0].text}")

            print("\n🧮 Testing log₂(8)...")
            log_result_custom = await client.call_tool(
                "get_log_value", {"x": 8, "base": 2}
            )
            print(f"Result: log₂(8) = {log_result_custom[0].text}")

            print(f"\n🧮 Testing ln(e) = log_e({math.e:.6f})...")
            log_result_natural = await client.call_tool(
                "get_log_value", {"x": math.e, "base": math.e}
            )
            print(f"Result: ln(e) = {float(log_result_natural[0].text):.6f}")

            # Test distance calculation between places with progress reporting
            print("\n🌍 Testing Distance Calculation (with Progress Reporting):")
            print("-" * 65)

            print("📍 Calculating distance between New York and London...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "New York, USA", "place2": "London, UK", "unit": "km"},
            )
            print("Result:")
            print(distance_result[0].text)

            print("\n📍 Calculating distance between Paris and Tokyo (in miles)...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_miles = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Paris, France", "place2": "Tokyo, Japan", "unit": "miles"},
            )
            print("Result:")
            print(distance_result_miles[0].text)

            print("\n📍 Calculating distance between Sydney and Melbourne...")
            print("   (Watch for progress updates and detailed logging)")
            distance_result_au = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Sydney, Australia", "place2": "Melbourne, Australia"},
            )
            print("Result:")
            print(distance_result_au[0].text)

            # Test distance calculation error handling
            print("\n🚫 Testing Distance Calculation Error Handling:")
            print("-" * 50)

            print(
                "🧮 Testing empty place name (should trigger context error logging)..."
            )
            invalid_distance = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "", "place2": "London, UK"},
            )
            print(f"Empty place name result: {invalid_distance[0].text}")

            print("\n🧮 Testing invalid unit (should trigger context error logging)...")
            invalid_unit = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Paris", "place2": "London", "unit": "invalid"},
            )
            print(f"Invalid unit result: {invalid_unit[0].text}")

            # Test weather functionality with comprehensive context logging
            print("\n🌤️ Testing Weather Information (with Context Logging & Progress):")
            print("-" * 70)

            # Test with a well-known location
            print("🌡️ Getting current weather for New York...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_result = await client.call_tool(
                    "get_weather", {"input": {"location": "New York, NY", "days": 1}}
                )
                # Parse the weather result (it's now a WeatherOutput object)
                weather_text = weather_result[0].text
                try:
                    import json

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
            print("\n🌡️ Getting 3-day weather forecast for London...")
            print("   (Watch for detailed API request logging and progress updates)")
            try:
                weather_forecast = await client.call_tool(
                    "get_weather", {"input": {"location": "London, UK", "days": 3}}
                )
                weather_forecast_text = weather_forecast[0].text
                try:
                    import json

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
            print("\n🧪 Testing Weather Error Handling (with Context Logging):")
            print("-" * 60)

            # Test empty location
            print("🧮 Testing empty location (should trigger context error logging)...")
            try:
                empty_location = await client.call_tool(
                    "get_weather", {"input": {"location": "", "days": 1}}
                )
                empty_text = empty_location[0].text
                try:
                    import json

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
                "\n🧮 Testing invalid days (10 days, should trigger context error logging)..."
            )
            try:
                invalid_days = await client.call_tool(
                    "get_weather", {"input": {"location": "Paris, France", "days": 10}}
                )
                invalid_text = invalid_days[0].text
                try:
                    import json

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

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("📝 Note: Context logging (ctx.info, ctx.error) and progress reporting")
        print("   are sent to the MCP client and may not appear in console output")
        print("   when using in-memory transport for testing.")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
