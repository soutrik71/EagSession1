from fastmcp import FastMCP
from typing import Annotated
import math
import requests
from fastmcp.exceptions import ToolError
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

mcp = FastMCP(name="CalculatorServer")


# standard way to define tools
@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
async def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b


@mcp.tool()
async def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


@mcp.tool()
async def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b


# better way to define tools using pydantic Field and Annotated
@mcp.tool()
async def get_sine_value(
    x: Annotated[float, Field(description="The angle in radians")],
) -> float:
    """Get the sine value of an angle"""
    return math.sin(x)


@mcp.tool()
async def get_cosine_value(
    x: Annotated[float, Field(description="The angle in radians")],
) -> float:
    """Get the cosine value of an angle"""
    return math.cos(x)


@mcp.tool()
async def get_tangent_value(
    x: Annotated[float, Field(description="The angle in radians")],
) -> float:
    """Get the tangent value of an angle"""
    return math.tan(x)


# using default value with direct field
@mcp.tool()
async def get_log_value(
    x: float = Field(description="The number to get the log of"),
    base: float = Field(description="The base of the log", default=10.0),
) -> float:
    """Get the log value of a number"""
    if x <= 0:
        raise ToolError("Cannot calculate log of non-positive number")
    if base <= 0 or base == 1:
        raise ToolError("Log base must be positive and not equal to 1")
    return math.log(x, base)


# one tool to calculate the distance between 2 places => using openstreetmap api


# Helper function to get coordinates from place name
async def get_coordinates(place_name: str) -> tuple[float, float]:
    """Get latitude and longitude for a place name using OpenStreetMap Nominatim API"""
    try:
        # Use OpenStreetMap Nominatim API (free, no API key required)
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "FastMCP-Distance-Calculator/1.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            raise ValueError(f"Place '{place_name}' not found")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return lat, lon

    except requests.RequestException as e:
        raise ValueError(f"Error fetching coordinates for '{place_name}': {e}")
    except (KeyError, IndexError, ValueError) as e:
        raise ValueError(f"Invalid response for '{place_name}': {e}")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371

    return c * r


# Tool to calculate distance between two places
@mcp.tool()
async def calculate_distance_between_places(
    place1: Annotated[
        str, Field(description="Name of the first place (city, country, address, etc.)")
    ],
    place2: Annotated[
        str,
        Field(description="Name of the second place (city, country, address, etc.)"),
    ],
    unit: Annotated[
        str, Field(description="Unit for distance result", default="km")
    ] = "km",
) -> str:
    """
    Calculate the distance between two places by name.

    This tool:
    1. Geocodes the place names to get their latitude and longitude coordinates
    2. Calculates the great circle distance using the Haversine formula
    3. Returns the distance in the specified unit (km or miles)

    Args:
        place1: Name of the first place
        place2: Name of the second place
        unit: Unit for the result ("km" for kilometers or "miles" for miles)

    Returns:
        A formatted string with the distance and coordinates information
    """
    try:
        # Validate inputs
        if not place1.strip() or not place2.strip():
            return "Error: Place names cannot be empty"

        if unit.lower() not in ["km", "miles"]:
            return "Error: Unit must be 'km' or 'miles'"

        # Get coordinates for both places
        lat1, lon1 = await get_coordinates(place1)
        lat2, lon2 = await get_coordinates(place2)

        # Calculate distance in kilometers
        distance_km = haversine_distance(lat1, lon1, lat2, lon2)

        # Convert to miles if requested
        if unit.lower() == "miles":
            distance = distance_km * 0.621371
            unit_str = "miles"
        else:
            distance = distance_km
            unit_str = "km"

        # Format the result
        result = f"""Distance between '{place1}' and '{place2}':

            {place1}: {lat1:.4f}°, {lon1:.4f}°
            {place2}: {lat2:.4f}°, {lon2:.4f}°

            Distance: {distance:.2f} {unit_str}
        """

        return result

    except Exception as e:
        return f"Error calculating distance: {str(e)}"


# Define weather tool using serpapi and pydantic
class WeatherInput(BaseModel):
    location: str = Field(
        description="Location to get weather for (city, country, etc.)"
    )
    days: int = Field(description="Number of days for forecast (1-7)", default=1)


class WeatherOutput(BaseModel):
    weather_info: str = Field(
        description="Weather information including current conditions and forecast"
    )
    success: bool = Field(description="Whether the weather request was successful")
    error_message: str = Field(
        description="Error message if request failed", default=""
    )


@mcp.tool()
async def get_weather(input: WeatherInput) -> WeatherOutput:
    """
    Get current weather and forecast for a location using SerpAPI.

    Args:
        input: WeatherInput containing location and number of forecast days

    Returns:
        WeatherOutput with weather information and success status
    """
    try:
        # Validate inputs
        if not input.location.strip():
            return WeatherOutput(
                weather_info="", success=False, error_message="Location cannot be empty"
            )

        if input.days < 1 or input.days > 7:
            return WeatherOutput(
                weather_info="",
                success=False,
                error_message="Days must be between 1 and 7",
            )

        # Get API key from environment
        api_key = os.getenv("SERP_API_KEY")
        if not api_key:
            return WeatherOutput(
                weather_info="",
                success=False,
                error_message="SERP_API_KEY not found in environment variables. Please set it in your .env file.",
            )

        # SerpAPI weather search with simplified parameters
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": f"weather {input.location}",
            "api_key": api_key,
            "hl": "en",
            "gl": "us",
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        # Check if response is valid JSON
        try:
            data = response.json()
        except ValueError as e:
            return WeatherOutput(
                weather_info="",
                success=False,
                error_message=f"Invalid JSON response from weather API: {str(e)}",
            )

        # Check for API errors in response
        if isinstance(data, dict) and "error" in data:
            error_msg = data.get("error", "Unknown error")
            return WeatherOutput(
                weather_info="",
                success=False,
                error_message=(
                    f"Weather API error: {error_msg}. "
                    "Please check your API key and try again."
                ),
            )

        # Check for search information and credits
        if isinstance(data, dict) and "search_information" in data:
            search_info = data["search_information"]
            if search_info.get("total_results", 0) == 0:
                return WeatherOutput(
                    weather_info="",
                    success=False,
                    error_message=(
                        f"No search results found for weather in '{input.location}'. "
                        "Try a different location."
                    ),
                )

        # Ensure data is a dictionary
        if not isinstance(data, dict):
            return WeatherOutput(
                weather_info="",
                success=False,
                error_message=(
                    f"Unexpected response format from weather API. "
                    f"Expected JSON object, got: {type(data).__name__}"
                ),
            )

        # Extract weather information from the response
        weather_info = []

        # Check for weather result in answer box (Google's weather widget)
        if "answer_box" in data and isinstance(data["answer_box"], dict):
            answer_box = data["answer_box"]

            # Look for weather data in answer box
            if "weather" in answer_box:
                weather = answer_box["weather"]
                if isinstance(weather, dict):
                    weather_info.append(f"🌤️ Current Weather in {input.location}:")

                    # Extract current conditions
                    if "temperature" in weather:
                        weather_info.append(f"Temperature: {weather['temperature']}")
                    if "precipitation" in weather:
                        weather_info.append(f"Condition: {weather['precipitation']}")
                    if "humidity" in weather:
                        weather_info.append(f"Humidity: {weather['humidity']}")
                    if "wind" in weather:
                        weather_info.append(f"Wind: {weather['wind']}")

                    # Add forecast if available and requested
                    if (
                        "forecast" in weather
                        and isinstance(weather["forecast"], list)
                        and input.days > 1
                    ):
                        weather_info.append(
                            f"\n📅 {min(input.days, len(weather['forecast']))} Day Forecast:"
                        )
                        for i, day in enumerate(weather["forecast"][: input.days]):
                            if isinstance(day, dict):
                                day_name = day.get("day", f"Day {i+1}")
                                high = day.get("high", "N/A")
                                low = day.get("low", "N/A")
                                condition = day.get("weather", "N/A")
                                weather_info.append(
                                    f"{day_name}: {high}/{low}, {condition}"
                                )

            # Also check for direct weather information in answer box
            elif (
                "title" in answer_box
                and "weather" in answer_box.get("title", "").lower()
            ):
                weather_info.append(f"🌤️ Weather for {input.location}:")
                if "snippet" in answer_box:
                    weather_info.append(answer_box["snippet"])

        # Check knowledge graph for weather information
        if not weather_info and "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            if isinstance(kg, dict) and "weather" in kg.get("title", "").lower():
                weather_info.append(f"🌤️ Weather Information for {input.location}:")
                if "description" in kg:
                    weather_info.append(kg["description"])

        # Primary fallback: check organic results for weather information
        if not weather_info and "organic_results" in data:
            for result in data["organic_results"][:5]:  # Check more results
                if isinstance(result, dict):
                    title = result.get("title", "").lower()
                    snippet = result.get("snippet", "").lower()

                    # Look for weather-related keywords
                    weather_keywords = [
                        "weather",
                        "temperature",
                        "forecast",
                        "climate",
                        "°f",
                        "°c",
                        "humidity",
                        "wind",
                    ]
                    if any(
                        keyword in title or keyword in snippet
                        for keyword in weather_keywords
                    ):
                        weather_info.append(f"🌤️ Weather for {input.location}:")
                        weather_info.append(f"Source: {result.get('title', 'N/A')}")
                        weather_info.append(f"Info: {result.get('snippet', 'N/A')}")
                        break

        # Secondary fallback: look for any weather-related content in the response
        if not weather_info:
            # Check if there's any weather-related content anywhere in the response
            response_str = str(data).lower()
            if any(
                keyword in response_str
                for keyword in ["weather", "temperature", "forecast", "°f", "°c"]
            ):
                weather_info.append(
                    f"🌤️ Weather information found for {input.location}:"
                )
                weather_info.append(
                    "Weather data is available but in an unexpected format."
                )
                weather_info.append(
                    "Please try a more specific location or check the API response manually."
                )
            else:
                # If still no weather info, provide a helpful message
                return WeatherOutput(
                    weather_info="",
                    success=False,
                    error_message=(
                        f"No weather information found for '{input.location}'. "
                        "Please try a more specific location like 'New York, NY' or 'London, UK'."
                    ),
                )

        return WeatherOutput(
            weather_info="\n".join(weather_info), success=True, error_message=""
        )

    except requests.RequestException as e:
        return WeatherOutput(
            weather_info="",
            success=False,
            error_message=f"Error fetching weather data: {str(e)}",
        )
    except Exception as e:
        return WeatherOutput(
            weather_info="",
            success=False,
            error_message=f"Error processing weather information: {str(e)}",
        )


if __name__ == "__main__":
    mcp.run()
