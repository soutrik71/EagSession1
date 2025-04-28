from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
from loguru import logger
import math

load_dotenv()

if not os.getenv("SERP_API_KEY"):
    raise ValueError("SERP_API_KEY is not set")


# Function to calculate approximate distance between two airports based on coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


# Dictionary of airport codes to coordinates (latitude, longitude)
# This is a small sample of major airports for demonstration
AIRPORT_COORDS = {
    "PEK": (40.080111, 116.584556),  # Beijing Capital International
    "AUS": (30.197528, -97.666389),  # Austin-Bergstrom
    "SFO": (37.618889, -122.375),  # San Francisco
    "LAX": (33.942536, -118.408075),  # Los Angeles
    "ICN": (37.469075, 126.450517),  # Incheon International
    "HND": (35.553333, 139.781111),  # Tokyo Haneda
    "IAH": (29.984444, -95.341389),  # Houston George Bush
    "SEA": (47.449, -122.309306),  # Seattle-Tacoma
    "TPE": (25.077731, 121.232822),  # Taiwan Taoyuan
    "YVR": (49.193889, -123.184444),  # Vancouver
    "MIA": (25.790654, -80.290556),  # Miami International
    "ORD": (41.978611, -87.904722),  # Chicago O'Hare
    "DEN": (39.861667, -104.673056),  # Denver International
    "MCO": (28.429306, -81.308968),  # Orlando International
    "DEL": (28.566667, 77.103333),  # Delhi International
    "BOM": (19.088611, 72.867778),  # Mumbai
    "BLR": (13.191111, 77.706111),  # Bengaluru International
    "CCU": (22.654722, 88.446667),  # Netaji Subhash Chandra Bose
    "MAA": (12.990278, 80.169167),  # Chennai International
    "HYD": (17.247222, 78.429444),  # Hyderabad International
    "SIN": (1.350178, 103.991556),  # Singapore Changi
    "NRT": (35.764722, 140.386389),  # Narita International
    "HKG": (22.308944, 113.915028),  # Hong Kong International
}


def search_flights(
    departure_id, arrival_id, outbound_date, return_date=None, currency="USD"
):
    """
    Search for flights and return a user-friendly summary of the best options.

    Args:
        departure_id (str): Airport code for departure (e.g., "PEK")
        arrival_id (str): Airport code for arrival (e.g., "AUS")
        outbound_date (str): Departure date in YYYY-MM-DD format
        return_date (str, optional): Return date in YYYY-MM-DD format for round trips
        currency (str, optional): Currency code (default: "USD")

    Returns:
        str: Formatted string with simplified flight search results
    """
    # Flight search parameters
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "currency": currency,
        "hl": "en",
        "api_key": os.getenv("SERP_API_KEY"),
        "gl": "us",
    }

    if return_date:
        params["return_date"] = return_date

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # logger.info(f"whole results: {results}")

        if "best_flights" not in results or not results["best_flights"]:
            return f"No flights found from {departure_id} to {arrival_id} on {outbound_date}."

        # Get price insights if available
        price_insights = {}
        if "price_insights" in results:
            price_insights = results["price_insights"]

        # Calculate flight distance if we have coordinates for both airports
        flight_distance = None
        if departure_id in AIRPORT_COORDS and arrival_id in AIRPORT_COORDS:
            dep_lat, dep_lon = AIRPORT_COORDS[departure_id]
            arr_lat, arr_lon = AIRPORT_COORDS[arrival_id]
            flight_distance = calculate_distance(dep_lat, dep_lon, arr_lat, arr_lon)

        # Start building output
        output = []
        output.append(f"TOP FLIGHT OPTIONS FROM {departure_id} TO {arrival_id}")
        output.append(
            f"Date: {outbound_date}" + (f" - {return_date}" if return_date else "")
        )

        # Add price insights if available
        if price_insights and "lowest_price" in price_insights:
            lowest = price_insights.get("lowest_price")
            price_level = price_insights.get("price_level", "")
            typical_range = price_insights.get("typical_price_range", [])

            output.append(
                f"Lowest Price: ${lowest} ({price_level.capitalize()} price level)"
            )
            if typical_range and len(typical_range) == 2:
                output.append(
                    f"Typical Price Range: ${typical_range[0]} - ${typical_range[1]}"
                )

        # If we have flight distance information, display it
        if flight_distance:
            output.append(
                f"Flight Distance: {flight_distance:.0f} km ({int(flight_distance * 0.621371)} miles)"
            )

        output.append("")

        # Process and simplify the flight results
        simplified_results = []
        for flight in results["best_flights"]:
            # Extract details for each flight
            flight_info = {
                "price": flight.get("price"),
                "total_duration": flight.get("total_duration"),
                "airline": flight["flights"][0].get("airline"),
                "airline_logo": flight.get("airline_logo"),
                "departure": {
                    "airport": flight["flights"][0]["departure_airport"].get("name"),
                    "time": flight["flights"][0]["departure_airport"].get("time"),
                    "id": flight["flights"][0]["departure_airport"].get("id"),
                },
                "arrival": {
                    "airport": flight["flights"][-1]["arrival_airport"].get("name"),
                    "time": flight["flights"][-1]["arrival_airport"].get("time"),
                    "id": flight["flights"][-1]["arrival_airport"].get("id"),
                },
                "layovers": [
                    {
                        "name": layover.get("name"),
                        "duration": layover.get("duration"),
                        "overnight": layover.get("overnight", False),
                    }
                    for layover in flight.get("layovers", [])
                ],
                "carbon_emissions": flight.get("carbon_emissions", {}),
                "flights_detail": flight.get("flights", []),
            }

            # Calculate segment distances if multi-segment flight
            if flight.get("flights") and len(flight.get("flights", [])) > 1:
                segments_with_distance = []
                total_distance = 0

                for i in range(len(flight["flights"])):
                    segment = flight["flights"][i]
                    dep_id = segment["departure_airport"].get("id")
                    arr_id = segment["arrival_airport"].get("id")

                    segment_distance = None
                    if dep_id in AIRPORT_COORDS and arr_id in AIRPORT_COORDS:
                        dep_lat, dep_lon = AIRPORT_COORDS[dep_id]
                        arr_lat, arr_lon = AIRPORT_COORDS[arr_id]
                        segment_distance = calculate_distance(
                            dep_lat, dep_lon, arr_lat, arr_lon
                        )
                        total_distance += segment_distance

                    segments_with_distance.append(
                        {"segment": segment, "distance": segment_distance}
                    )

                flight_info["segment_distances"] = segments_with_distance
                flight_info["total_distance"] = (
                    total_distance if total_distance > 0 else None
                )

            simplified_results.append(flight_info)

        # Format the results as a string
        for idx, flight in enumerate(simplified_results, 1):
            output.append(f"Flight Option {idx}:")
            output.append(f"  Price: ${flight['price']}")

            # Convert minutes to hours and minutes
            total_mins = flight["total_duration"]
            hours = total_mins // 60
            mins = total_mins % 60
            output.append(f"  Duration: {hours}h {mins}m ({total_mins} minutes)")
            output.append(f"  Airline: {flight['airline']}")
            output.append(
                f"  From: {flight['departure']['airport']} at {flight['departure']['time']}"
            )
            output.append(
                f"  To: {flight['arrival']['airport']} at {flight['arrival']['time']}"
            )

            # Add per-flight distance if it has segments with calculated distances
            if "total_distance" in flight and flight["total_distance"]:
                total_dist = flight["total_distance"]
                miles = int(total_dist * 0.621371)
                output.append(
                    f"  Total Flight Distance: {total_dist:.0f} km ({miles} miles)"
                )

                # Calculate efficiency metrics (distance/time)
                if flight["total_duration"] > 0:
                    speed = total_dist / (flight["total_duration"] / 60)  # km/h
                    output.append(f"  Average Speed: {speed:.0f} km/h")

            # Format layovers with duration in hours and minutes
            if flight["layovers"]:
                layover_details = []
                for layover in flight["layovers"]:
                    lay_hours = layover["duration"] // 60
                    lay_mins = layover["duration"] % 60
                    layover_text = f"{layover['name']} ({lay_hours}h {lay_mins}m)"
                    if layover.get("overnight", False):
                        layover_text += " 🌙 overnight"
                    layover_details.append(layover_text)
                output.append(f"  Layovers: {', '.join(layover_details)}")

            # Add carbon emissions info if available
            if (
                flight.get("carbon_emissions")
                and "this_flight" in flight["carbon_emissions"]
            ):
                carbon = flight["carbon_emissions"]
                carbon_kg = carbon["this_flight"] / 1000  # Convert to kg

                carbon_comparison = ""
                if "difference_percent" in carbon:
                    diff = carbon["difference_percent"]
                    if diff < 0:
                        carbon_comparison = f" ({abs(diff)}% less than average)"
                    elif diff > 0:
                        carbon_comparison = f" ({diff}% more than average)"

                output.append(
                    f"  Carbon Emissions: {carbon_kg:.0f} kg{carbon_comparison}"
                )

                # Calculate emissions efficiency if we have distance
                if "total_distance" in flight and flight["total_distance"]:
                    carbon_efficiency = carbon_kg / (
                        flight["total_distance"] / 1000
                    )  # kg per 1000 km
                    output.append(
                        f"  Emissions Efficiency: {carbon_efficiency:.1f} kg CO₂ per 1000 km"
                    )

            # Add flight details
            if flight.get("flights_detail") and len(flight["flights_detail"]) > 1:
                output.append("  Flight Segments:")
                for i, segment in enumerate(flight["flights_detail"], 1):
                    dep = segment["departure_airport"]
                    arr = segment["arrival_airport"]
                    segment_airline = segment.get("airline")
                    flight_num = segment.get("flight_number", "")
                    segment_duration = segment.get("duration", 0)

                    seg_hours = segment_duration // 60
                    seg_mins = segment_duration % 60

                    segment_info = f"    {i}. {dep.get('id')} → {arr.get('id')}: {segment_airline} {flight_num}"

                    # Add segment distance if available
                    if "segment_distances" in flight and i - 1 < len(
                        flight["segment_distances"]
                    ):
                        seg_dist = flight["segment_distances"][i - 1]["distance"]
                        if seg_dist:
                            seg_miles = int(seg_dist * 0.621371)
                            segment_info += f" ({seg_dist:.0f} km / {seg_miles} mi)"

                    output.append(segment_info)
                    output.append(
                        f"       {dep.get('time')} → {arr.get('time')} ({seg_hours}h {seg_mins}m)"
                    )

            output.append("")  # Empty line between flight options

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Error searching for flights: {str(e)}")
        return f"Error searching for flights: {str(e)}"


def search_hotels(location, check_in_date, check_out_date, adults=1, currency="USD"):
    """
    Search for accommodations and return a user-friendly summary of the best options.

    Args:
        location (str): Location to search for accommodations (e.g., "Austin TX")
        check_in_date (str): Check-in date in YYYY-MM-DD format
        check_out_date (str): Check-out date in YYYY-MM-DD format
        adults (int, optional): Number of adults (default: 1)
        currency (str, optional): Currency code (default: "USD")

    Returns:
        str: Formatted string with simplified accommodation search results
    """
    # Hotel search parameters
    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": str(adults),
        "currency": currency,
        "gl": "us",
        "hl": "en",
        "api_key": os.getenv("SERP_API_KEY"),
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "properties" not in results or not results["properties"]:
            return f"No accommodations found in {location} for {check_in_date} to {check_out_date}."

        output = []
        output.append(f"TOP ACCOMMODATIONS IN {location.upper()}")
        output.append(f"Dates: {check_in_date} to {check_out_date} | Adults: {adults}")
        output.append("")

        # Only show top 10 properties for reasonable selection
        properties_to_show = min(10, len(results["properties"]))

        for i in range(properties_to_show):
            property_data = results["properties"][i]

            # Extract hotel name and type
            name = property_data.get("name", "N/A")
            property_type = property_data.get("type", "N/A").capitalize()

            # Extract hotel class/star rating if available
            stars = None
            if "hotel_class" in property_data:
                hotel_class = property_data.get("hotel_class", "")
                # Try to extract the star rating from the hotel_class string
                if hotel_class and "star" in hotel_class.lower():
                    try:
                        stars = int(hotel_class.split("-")[0])
                    except (ValueError, IndexError):
                        pass
            elif "extracted_hotel_class" in property_data:
                stars = property_data.get("extracted_hotel_class", 0)

            # Format name with property type and stars
            type_info = []
            if property_type and property_type.lower() != "n/a":
                type_info.append(property_type)
            if stars and stars > 0:
                type_info.append(f"{stars}-Star")

            name_line = f"{i+1}. {name}"
            if type_info:
                name_line += f" [{', '.join(type_info)}]"

            # Check for deals or special offers
            if "deal" in property_data:
                deal = property_data.get("deal", "")
                if deal:
                    name_line += f" 🔥 {deal}"

            # Extract hotel description
            description = property_data.get("description", "")

            # Extract location information
            address_lines = []

            # Check for address in property_data
            if "address" in property_data:
                addr = property_data.get("address")
                if isinstance(addr, str) and addr:
                    address_lines.append(addr)
                elif isinstance(addr, dict):
                    addr_parts = []
                    for key in ["street", "city", "state", "postal_code", "country"]:
                        if key in addr and addr[key]:
                            addr_parts.append(addr[key])
                    if addr_parts:
                        address_lines.append(", ".join(addr_parts))

            # Use coordinates if no address
            if not address_lines and "gps_coordinates" in property_data:
                coords = property_data.get("gps_coordinates", {})
                latitude = coords.get("latitude", "")
                longitude = coords.get("longitude", "")
                if latitude and longitude:
                    address_lines.append(f"Coordinates: {latitude}, {longitude}")

            # Check for link which might contain hotel's website
            hotel_link = property_data.get("link", "")
            if hotel_link and hotel_link.startswith("http"):
                address_lines.append(f"Website: {hotel_link}")

            # Get price information
            price_info = "Price not available"
            if (
                "rate_per_night" in property_data
                and "lowest" in property_data["rate_per_night"]
            ):
                price_info = property_data["rate_per_night"]["lowest"]

                # Check for before taxes/fees price
                if "before_taxes_fees" in property_data["rate_per_night"]:
                    before_tax_price = property_data["rate_per_night"][
                        "before_taxes_fees"
                    ]
                    price_info += f" (Base: {before_tax_price})"

            # Get rating information
            rating = property_data.get("overall_rating", None)
            reviews = property_data.get("reviews", "0")
            rating_text = ""
            if rating:
                if isinstance(rating, (int, float)):
                    rating_text = f"Rating: {rating:.1f}/5 ({reviews} reviews)"
                else:
                    rating_text = f"Rating: {rating} ({reviews} reviews)"

                # Add location rating if available
                if "location_rating" in property_data:
                    loc_rating = property_data.get("location_rating")
                    if loc_rating:
                        rating_text += f" | Location: {loc_rating}/5"

            # Check-in/check-out times
            times = []
            if "check_in_time" in property_data:
                times.append(f"Check-in: {property_data['check_in_time']}")
            if "check_out_time" in property_data:
                times.append(f"Check-out: {property_data['check_out_time']}")

            # Location/nearby places - with distance and transportation info
            nearby_places = []
            if "nearby_places" in property_data:
                for place in property_data["nearby_places"]:
                    place_name = place.get("name", "")
                    if place_name:
                        transportation = ""
                        if "transportations" in place and place["transportations"]:
                            transport = place["transportations"][0]
                            transport_type = transport.get("type", "")
                            duration = transport.get("duration", "")
                            if transport_type and duration:
                                transportation = f" ({transport_type}, {duration})"
                        nearby_places.append(f"{place_name}{transportation}")

            # Top amenities with categories
            free_amenities = []
            paid_amenities = []
            key_amenities = []
            if "amenities" in property_data:
                for amenity in property_data["amenities"]:
                    if amenity.startswith("Free "):
                        free_amenities.append(amenity)
                    elif "($)" in amenity:
                        paid_amenities.append(amenity)
                    elif amenity in [
                        "Pool",
                        "Pools",
                        "Indoor pool",
                        "Outdoor pool",
                        "Beach access",
                        "Fitness centre",
                        "Spa",
                        "Restaurant",
                        "Bar",
                    ]:
                        key_amenities.append(amenity)

            # Format the property information
            output.append(name_line)

            if description:
                output.append(f"   {description}")

            for addr_line in address_lines:
                output.append(f"   {addr_line}")

            if times:
                output.append(f"   {' | '.join(times)}")

            output.append(f"   Price: {price_info}")

            if rating_text:
                output.append(f"   {rating_text}")

            # Show key amenities first, then free amenities
            if key_amenities:
                output.append(f"   Key Amenities: {', '.join(key_amenities)}")

            if free_amenities:
                output.append(f"   Free Amenities: {', '.join(free_amenities)}")

            if paid_amenities:
                output.append(f"   Paid Amenities: {', '.join(paid_amenities)}")

            # Categorize nearby places
            if nearby_places:
                # Group nearby places by category
                airports = []
                attractions = []
                dining = []

                for place in nearby_places:
                    if "airport" in place.lower():
                        airports.append(place)
                    elif any(
                        word in place.lower()
                        for word in ["restaurant", "café", "bar", "food", "coffee"]
                    ):
                        dining.append(place)
                    else:
                        attractions.append(place)

                if airports:
                    output.append(f"   Airport: {airports[0]}")
                if dining:
                    output.append(f"   Dining: {', '.join(dining[:2])}")
                if attractions:
                    output.append(f"   Nearby: {', '.join(attractions[:2])}")

            # Add a divider between hotels for better readability
            output.append("   " + "-" * 50)
            output.append("")  # Empty line for spacing

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Error searching for accommodations: {str(e)}")
        return f"Error searching for accommodations: {str(e)}"


if __name__ == "__main__":
    # Example flight search
    flight_results = search_flights("PEK", "AUS", "2025-04-28", "2025-05-04")
    print(flight_results)

    # Example hotel search
    # hotel_results = search_hotels("Austin TX", "2025-04-28", "2025-05-04", 2)
    # print(hotel_results)
