import httpx
import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the Server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> Dict[str, Any]:
    """Make a GET request to the NWS API and return JSON, or None if there's an error."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    try:
        logger.debug(f"Making request to {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error accessing {url}: {str(e)}")
        return None


def format_alert(feature: dict) -> str:
    """Convert a single weather alert feature into a readable string."""
    props = feature["properties"]
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No instructions')}"
    )


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Return weather alerts for a US state (two-letter code, e.g. CA)

    Args:
        state: Two-letter state code (e.g., 'CA')

    Returns:
        String containing all active weather alerts for the state
    """
    logger.info(f"Fetching alerts for state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        logger.warning(f"No alerts data available for state: {state}")
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        logger.info(f"No active alerts found for state: {state}")
        return f"No active alerts for {state}."

    alerts = [format_alert(f) for f in data["features"]]
    logger.info(f"Found {len(alerts)} alerts for state: {state}")
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Return a short weather forecast for (latitude, longitude)

    Args:
        latitude: Latitude coordinate (e.g., 37.7749)
        longitude: Longitude coordinate (e.g., -122.4194)

    Returns:
        String containing the short weather forecast for the coordinates
    """
    logger.info(f"Fetching forecast for coordinates: ({latitude}, {longitude})")
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if not points_data or "properties" not in points_data:
        logger.warning(
            f"Unable to fetch forecast data for coordinates: ({latitude}, {longitude})"
        )
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"].get("forecast")
    if not forecast_url:
        logger.warning(
            f"No forecast URL found for coordinates: ({latitude}, {longitude})"
        )
        return "Forecast URL not found for this location."

    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data or "properties" not in forecast_data:
        logger.warning(
            f"Unable to fetch detailed forecast for coordinates: ({latitude}, {longitude})"
        )
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"].get("periods", [])
    if not periods:
        logger.warning(
            f"No forecast periods available for coordinates: ({latitude}, {longitude})"
        )
        return "No forecast periods available."

    lines = []
    for period in periods[:5]:  # Only first 5 periods
        lines.append(
            f"{period['name']}:\n"
            f"  Temp: {period['temperature']}°{period['temperatureUnit']}\n"
            f"  Wind: {period['windSpeed']} {period['windDirection']}\n"
            f"  Forecast: {period['detailedForecast']}"
        )
    logger.info(
        f"Successfully fetched forecast for coordinates: ({latitude}, {longitude})"
    )
    return "\n\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
