from tools import search_flights, search_hotels
from typing import Dict, Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("eag_agentic_arch")


@mcp.tool()
def search_flights_tool(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    currency: str = "USD",
) -> str:
    """
    Search for flights between two airports and return a summary of available options.

    Args:
        departure_id: The IATA code of the departure airport (e.g., 'BLR', 'JFK')
        arrival_id: The IATA code of the arrival airport (e.g., 'LHR', 'SFO')
        outbound_date: The date of the outbound flight in YYYY-MM-DD format
        return_date: date of the return flight in YYYY-MM-DD format
        currency: The currency for pricing (USD, EUR, GBP, etc.)

    Returns:
        A dictionary containing a summary of available flights
    """
    result = search_flights(
        departure_id,
        arrival_id,
        outbound_date,
        return_date,
        currency,
    )
    return result


@mcp.tool()
def search_hotels_tool(
    location: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 1,
    currency: str = "USD",
) -> str:
    """
    Search for hotels in a location for a specified date range.

    Args:
        location: The city or area to search for hotels
        check_in_date: The check-in date in YYYY-MM-DD format
        check_out_date: The check-out date in YYYY-MM-DD format
        adults: Number of adult guests
        currency: The currency for pricing (USD, EUR, GBP, etc.)

    Returns:
        A dictionary containing a summary of available hotels
    """
    result = search_hotels(
        location,
        check_in_date,
        check_out_date,
        adults,
        currency,
    )
    return result


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
