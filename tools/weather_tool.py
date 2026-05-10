from tools.api_driven_weather import api_weather_tool
from langchain.tools import tool
from utils.logger import logger

@tool("Weather Tool")
def weather_tool(location: str) -> str:
    """
    Fetch current weather for a specific location using API only.
    Returns structured weather data without fallback parsing.
    Requires OPENWEATHER_API_KEY environment variable.
    """
    logger.info(f"Weather Tool called for location: {location}")
    
    weather_response = api_weather_tool.get_weather(location)
    
    if not weather_response.success:
        logger.error(f"Weather tool failed: {weather_response.message}")
        return {
            "success": False,
            "message": weather_response.message,
            "location": location,
            "source": "api_driven"
        }
    
    # Return structured weather data
    return {
        "success": True,
        "location": weather_response.location,
        "temperature": weather_response.temperature,
        "feels_like": weather_response.feels_like,
        "humidity": weather_response.humidity,
        "pressure": weather_response.pressure,
        "description": weather_response.description,
        "wind_speed": weather_response.wind_speed,
        "visibility": weather_response.visibility,
        "uv_index": weather_response.uv_index,
        "source": "api_driven"
    }
