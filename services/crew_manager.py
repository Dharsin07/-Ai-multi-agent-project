from utils.logger import logger
import json
from services.api_driven_crew_manager import APIDrivenTravelCrewManager

class TravelCrewManager:
    def __init__(self):
        # Use API-driven crew manager
        logger.info("Initializing Travel Crew Manager with API-driven tools")
        self.api_manager = APIDrivenTravelCrewManager()

    def run_crew(self, inputs: dict):
        logger.info(f"Starting Travel Crew with inputs: {inputs}")
        
        try:
            # Use API-driven manager
            logger.info("Using API-driven tools for travel planning")
            return self.api_manager.run_crew(inputs)
                
        except Exception as e:
            logger.error(f"Error during travel planning: {e}")
            return self.get_fallback_response(inputs)
    
    def get_fallback_response(self, inputs: dict):
        """Fallback response when all else fails"""
        destination = inputs.get('destination', 'Unknown')
        budget = inputs.get('budget', 'Not specified')
        duration = inputs.get('duration', '3 days')
        
        return {
            "destination": destination,
            "duration": duration,
            "flights": [],
            "hotels": [],
            "itinerary": self.create_basic_itinerary(destination, duration),
            "budget": {
                "total_estimated_cost": f"Error occurred for {budget}",
                "flights_cost": "N/A",
                "accommodation_cost": "N/A",
                "activities_food_cost": "N/A",
                "is_within_budget": False,
                "saving_tips": [],
                "error": "API-driven tools failed"
            },
            "weather_advisory": f"Weather data unavailable due to error",
            "error": "API-driven tools failed",
            "source": "fallback"
        }
    
    def create_basic_itinerary(self, destination: str, duration: str):
        """Create basic itinerary structure"""
        return [
            {
                "day": 1,
                "theme": f"Exploring {destination}",
                "activities": [
                    {
                        "time": "Morning",
                        "title": "Arrival & Check-in",
                        "description": f"Arrive at {destination}, check into hotel",
                        "cost_estimate": "$200",
                        "location": destination
                    },
                    {
                        "time": "Afternoon",
                        "title": "Local Exploration",
                        "description": f"Explore local attractions in {destination}",
                        "cost_estimate": "$500",
                        "location": destination
                    }
                ]
            }
        ]
