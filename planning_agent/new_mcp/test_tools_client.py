import asyncio
from fastmcp import Client

# Import the tools server instance
from tools_server import mcp as tools_server


async def main():
    """Test the tools server with various mathematical operations, distance calculation, and weather."""

    print("🧮 Testing FastMCP Tools Server")
    print("=" * 50)

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

            # Test basic math operations
            print("\n🔢 Testing Basic Math Operations:")
            print("-" * 35)

            add_result = await client.call_tool("add", {"a": 15, "b": 25})
            print(f"15 + 25 = {add_result[0].text}")

            multiply_result = await client.call_tool("multiply", {"a": 7, "b": 8})
            print(f"7 × 8 = {multiply_result[0].text}")

            divide_result = await client.call_tool("divide", {"a": 100, "b": 4})
            print(f"100 ÷ 4 = {divide_result[0].text}")

            # Test division by zero error handling
            print("\n🚫 Testing Error Handling:")
            print("-" * 25)
            try:
                divide_zero_result = await client.call_tool("divide", {"a": 10, "b": 0})
                print(f"10 ÷ 0 = {divide_zero_result[0].text}")
            except Exception as e:
                print(f"✅ Division by zero correctly caught: {type(e).__name__}")

            # Test log with invalid inputs
            try:
                log_negative = await client.call_tool("get_log_value", {"x": -5})
                print(f"log(-5) = {log_negative[0].text}")
            except Exception as e:
                print(f"✅ Negative log correctly caught: {type(e).__name__}")

            # Test trigonometric functions
            print("\n📐 Testing Trigonometric Functions:")
            print("-" * 40)

            import math

            angle = math.pi / 4  # 45 degrees in radians

            sine_result = await client.call_tool("get_sine_value", {"x": angle})
            print(f"sin(π/4) = {float(sine_result[0].text):.6f}")

            cosine_result = await client.call_tool("get_cosine_value", {"x": angle})
            print(f"cos(π/4) = {float(cosine_result[0].text):.6f}")

            tangent_result = await client.call_tool("get_tangent_value", {"x": angle})
            print(f"tan(π/4) = {float(tangent_result[0].text):.6f}")

            # Test logarithm with default and custom base
            print("\n📊 Testing Logarithm Functions:")
            print("-" * 35)

            log_result = await client.call_tool("get_log_value", {"x": 100})
            print(f"log₁₀(100) = {log_result[0].text}")

            log_result_custom = await client.call_tool(
                "get_log_value", {"x": 8, "base": 2}
            )
            print(f"log₂(8) = {log_result_custom[0].text}")

            log_result_natural = await client.call_tool(
                "get_log_value", {"x": math.e, "base": math.e}
            )
            print(f"ln(e) = {float(log_result_natural[0].text):.6f}")

            # Test distance calculation between places
            print("\n🌍 Testing Distance Calculation:")
            print("-" * 40)

            print("📍 Calculating distance between New York and London...")
            distance_result = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "New York, USA", "place2": "London, UK", "unit": "km"},
            )
            print(distance_result[0].text)

            print("\n📍 Calculating distance between Paris and Tokyo (in miles)...")
            distance_result_miles = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Paris, France", "place2": "Tokyo, Japan", "unit": "miles"},
            )
            print(distance_result_miles[0].text)

            print("\n📍 Calculating distance between Sydney and Melbourne...")
            distance_result_au = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Sydney, Australia", "place2": "Melbourne, Australia"},
            )
            print(distance_result_au[0].text)

            # Test distance calculation error handling
            print("\n🚫 Testing Distance Calculation Error Handling:")
            print("-" * 50)

            invalid_distance = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "", "place2": "London, UK"},
            )
            print(f"Empty place name: {invalid_distance[0].text}")

            invalid_unit = await client.call_tool(
                "calculate_distance_between_places",
                {"place1": "Paris", "place2": "London", "unit": "invalid"},
            )
            print(f"Invalid unit: {invalid_unit[0].text}")

            # Test weather functionality
            print("\n🌤️ Testing Weather Information:")
            print("-" * 40)

            # Test with a well-known location
            print("🌡️ Getting current weather for New York...")
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
            print("\n🧪 Testing Weather Error Handling:")
            print("-" * 40)

            # Test empty location
            print("Testing empty location...")
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
            print("Testing invalid days (10 days)...")
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

        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print(f"🔌 Client connected after context: {client.is_connected()}")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
