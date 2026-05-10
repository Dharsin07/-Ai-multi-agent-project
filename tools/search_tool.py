from tools.api_driven_search import api_search_tool
from langchain.tools import tool
from utils.logger import logger

logger.info("Initializing API-driven search tool...")

@tool("Flight Search Tool")
def flight_search_tool(destination: str, budget: str = None, source_location: str = None, flight_type: str = "economy") -> str:
    """
    Search for flights using structured API responses only.
    Returns clean, structured flight data without regex parsing.
    """
    logger.info(f"Flight search tool called for destination: {destination}")
    
    flights = api_search_tool.search_flights(
        destination=destination,
        budget=budget,
        source_location=source_location,
        flight_type=flight_type
    )
    
    return {
        "flights": [flight.dict() for flight in flights],
        "count": len(flights),
        "source": "api_driven"
    }

@tool("Hotel Search Tool")
def hotel_search_tool(destination: str, budget: str = None, minimum_ratings: float = None, hotel_preferences: str = None) -> str:
    """
    Search for hotels using structured API responses only.
    Returns clean, structured hotel data without regex parsing.
    """
    logger.info(f"Hotel search tool called for destination: {destination}")
    
    preferences = hotel_preferences.split(",") if hotel_preferences else None
    
    hotels = api_search_tool.search_hotels(
        destination=destination,
        budget=budget,
        minimum_ratings=minimum_ratings,
        hotel_preferences=preferences
    )
    
    return {
        "hotels": [hotel.dict() for hotel in hotels],
        "count": len(hotels),
        "source": "api_driven"
    }

@tool("General Search Tool")
def general_search_tool(query: str) -> str:
    """
    General search using structured API responses only.
    Returns clean, structured search results without regex parsing.
    """
    logger.info(f"General search tool called for query: {query}")
    
    result = api_search_tool.general_search(query)
    
    return {
        "results": result.results,
        "total_results": result.total_results,
        "success": result.success,
        "source": "api_driven"
    }

# Legacy search_tool for backward compatibility
search_tool = general_search_tool
