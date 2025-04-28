from tools import search_flights, search_hotels
from pydantic import BaseModel, Field
from typing import Literal, Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("eag_agentic_arch")


class TravelSearch(BaseModel):
    search_type: Literal["flight", "hotel"] = Field(
        ..., description="Type of search to perform"
    )
    # Common fields
    currency: str = Field(
        "USD", description="The currency of the prices (USD, EUR, GBP, etc.)"
    )
    start_date: str = Field(
        ...,
        description="The start date in YYYY-MM-DD format (outbound flight or check-in date)",
    )
    end_date: Optional[str] = Field(
        None,
        description="The end date in YYYY-MM-DD format (return flight or check-out date)",
    )
    # Flight specific fields
    departure_id: Optional[str] = Field(
        None, description="The IATA code of the departure airport"
    )
    arrival_id: Optional[str] = Field(
        None, description="The IATA code of the arrival airport"
    )
    # Hotel specific fields
    location: Optional[str] = Field(None, description="The location of the hotel")
    adults: Optional[int] = Field(1, description="The number of adults")


class TravelSearchResponse(BaseModel):
    summary: str = Field(..., description="A summary of the travel search")


@mcp.tool()
def search_flights_tool(search: TravelSearch) -> TravelSearchResponse:
    """
    Search for flights between two airports on a given date and return a summary of the flight search.

    Args:
        search: The search parameters for the flight search in the format of TravelSearch pydantic model

    Returns:
        A summary of the flight search in the format of TravelSearchResponse pydantic model
    """
    if not all([search.departure_id, search.arrival_id, search.start_date]):
        raise ValueError(
            "Flight search requires departure_id, arrival_id, and start_date"
        )

    result = search_flights(
        search.departure_id,
        search.arrival_id,
        search.start_date,  # outbound_date
        search.end_date,  # return_date
        search.currency,
    )

    return TravelSearchResponse(summary=result)


@mcp.tool()
def search_hotels_tool(search: TravelSearch) -> TravelSearchResponse:
    """
    Search for hotels in a given location for a given date range and number of adults.

    Args:
        search: The search parameters for the hotel search in the format of TravelSearch pydantic model

    Returns:
        A summary of the hotel search in the format of TravelSearchResponse pydantic model
    """
    if not all([search.location, search.start_date, search.end_date]):
        raise ValueError("Hotel search requires location, start_date, and end_date")

    result = search_hotels(
        search.location,
        search.start_date,  # check_in_date
        search.end_date,  # check_out_date
        search.adults,
        search.currency,
    )

    return TravelSearchResponse(summary=result)


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="stdio")
