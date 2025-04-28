from tools import search_flights, search_hotels
from pydantic import BaseModel, Field
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("eag_agentic_arch")


class FlightSearch(BaseModel):
    departure_id: str = Field(..., description="The IATA code of the departure airport")
    arrival_id: str = Field(..., description="The IATA code of the arrival airport")
    outbound_date: str = Field(
        ..., description="The date of the outbound flight in YYYY-MM-DD format"
    )
    return_date: str = Field(
        None, description="The date of the return flight in YYYY-MM-DD format"
    )
    currency: str = Field(
        "USD", description="The currency of the flight prices (USD, EUR, GBP, etc.)"
    )


class HotelSearch(BaseModel):
    location: str = Field(..., description="The location of the hotel")
    check_in_date: str = Field(
        ..., description="The date of the check-in in YYYY-MM-DD format"
    )
    check_out_date: str = Field(
        ..., description="The date of the check-out in YYYY-MM-DD format"
    )
    adults: int = Field(1, description="The number of adults")
    currency: str = Field(
        "USD", description="The currency of the hotel prices (USD, EUR, GBP, etc.)"
    )


class FlightSearchResponse(BaseModel):
    summary: str = Field(..., description="A summary of the flight search")


class HotelSearchResponse(BaseModel):
    summary: str = Field(..., description="A summary of the hotel search")


@mcp.tool()
def search_flights_tool(search: FlightSearch) -> FlightSearchResponse:
    """
    Search for flights between two airports on a given date and return a summary of the flight search.

    Args:
        search: The search parameters for the flight search in the format of FlightSearch pydantic model

    Returns:
        A summary of the flight search in the format of FlightSearchResponse pydantic model
    """
    return search_flights(
        search.departure_id,
        search.arrival_id,
        search.outbound_date,
        search.return_date,
        search.currency,
    )


@mcp.tool()
def search_hotels_tool(search: HotelSearch) -> HotelSearchResponse:
    """
    Search for hotels in a given location for a given date range and number of adults and return a summary of the hotel search.

    Args:
        search: The search parameters for the flight search in the format of FlightSearch pydantic model

    Returns:
        A summary of the flight search in the format of FlightSearchResponse pydantic model
    """
    return search_hotels(
        search.location,
        search.check_in_date,
        search.check_out_date,
        search.adults,
        search.currency,
    )


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
