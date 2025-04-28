from server import TravelSearch, search_flights_tool, search_hotels_tool


def test_flight_search():
    """Test the flight search tool with standard inputs."""
    print("Testing flight search tool...")

    # Create a flight search with standard inputs
    flight_search = TravelSearch(
        search_type="flight",
        departure_id="PEK",
        arrival_id="JFK",
        start_date="2025-05-07",
        end_date="2025-05-10",
        currency="USD",
    )

    try:
        # Call the flight search tool
        result = search_flights_tool(flight_search)
        print(f"Flight search successful: {result.summary}")
    except Exception as e:
        print(f"Flight search failed: {str(e)}")


def test_hotel_search():
    """Test the hotel search tool with standard inputs."""
    print("Testing hotel search tool...")

    # Create a hotel search with standard inputs
    hotel_search = TravelSearch(
        search_type="hotel",
        location="New York",
        start_date="2025-05-07",
        end_date="2025-05-10",
        adults=1,
        currency="USD",
    )

    try:
        # Call the hotel search tool
        result = search_hotels_tool(hotel_search)
        print(f"Hotel search successful: {result.summary}")
    except Exception as e:
        print(f"Hotel search failed: {str(e)}")


if __name__ == "__main__":
    test_flight_search()
    print("\n" + "-" * 50 + "\n")
    test_hotel_search()
