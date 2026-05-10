from crewai import Crew, Task
from agents.trava_agents import TravaAIAgents
from services.travel_intent_extractor import TravelIntentExtractor
from services.budget_validator import BudgetValidator
from services.trava_response_formatter import TravaResponseFormatter
from services.crew_manager import TravelCrewManager
from services.ranking_service import TravelRankingService
from models.schemas import FinalTravelPlan
from utils.logger import logger
import json
from typing import Dict, Any, List
import re

class TravaCrewManager:
    """TRAVA AI Multi-Agent Travel Intelligence System Manager"""
    
    def __init__(self):
        self.intent_extractor = TravelIntentExtractor()
        self.trava_agents = TravaAIAgents()
        self.budget_validator = BudgetValidator()
        self.response_formatter = TravaResponseFormatter()
        self.legacy_manager = TravelCrewManager()  # For enhanced search capabilities
        self.ranking_service = TravelRankingService()  # Intelligent ranking system
        logger.info("Initializing TRAVA AI Crew Manager with ranking service")

    def process_travel_request(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point for processing travel requests
        
        Args:
            user_input: Natural language travel request
            
        Returns:
            Structured travel plan in TRAVA AI format
        """
        logger.info(f"Processing TRAVA AI travel request: {user_input}")
        
        try:
            # Step 1: Extract travel intent
            travel_intent = self.intent_extractor.extract_travel_intent(user_input)
            
            # Step 2: Get real data using enhanced search
            flights = self._get_enhanced_flights(travel_intent)
            hotels = self._get_enhanced_hotels(travel_intent)
            
            # Step 3: Rank and score search results
            ranked_flights = self.ranking_service.rank_flights(
                flights, 
                travel_intent.get('budget', {}).get('amount'), 
                travel_intent
            )
            ranked_hotels = self.ranking_service.rank_hotels(
                hotels, 
                travel_intent.get('budget', {}).get('amount'), 
                travel_intent
            )
            
            # Step 4: Filter to top-ranked options only
            top_flights = self.ranking_service.get_top_options(ranked_flights, top_n=5)
            top_hotels = self.ranking_service.get_top_options(ranked_hotels, top_n=5)
            
            logger.info(f"Selected top {len(top_flights)} flights and {len(top_hotels)} hotels from rankings")
            
            # Step 5: Calculate duration
            duration_days = self._parse_duration(travel_intent.get('duration', '3 days'))
            
            # Step 6: Validate budget using top-ranked options
            budget_analysis = self.budget_validator.validate_travel_budget(
                travel_intent, top_flights, top_hotels, duration_days
            )
            
            # Step 7: Create daily plan with ranked options
            daily_plan = self._create_enhanced_itinerary(travel_intent, top_flights, top_hotels)
            
            # Step 8: Get weather and local experiences (also ranked)
            weather_data = self._get_weather_data(travel_intent.get('destination'))
            local_experiences = self._get_local_experiences(travel_intent)
            ranked_experiences = self.ranking_service.rank_activities(
                local_experiences,
                travel_intent.get('budget', {}).get('amount'),
                travel_intent
            )
            top_experiences = self.ranking_service.get_top_options(ranked_experiences, top_n=10)
            
            # Step 9: Format final response with ranked options
            final_response = self.response_formatter.format_trava_response(
                travel_intent, top_flights, top_hotels, budget_analysis,
                daily_plan, weather_data, top_experiences
            )
            
            # Step 10: Validate response structure
            if self.response_formatter.validate_response_structure(final_response):
                logger.info("TRAVA AI travel processing completed successfully")
                return final_response
            else:
                logger.warning("Response structure validation failed, using fallback")
                return self._get_fallback_response(user_input, travel_intent)
            
        except Exception as e:
            logger.error(f"Error in TRAVA AI processing: {e}")
            return self._get_fallback_response(user_input, travel_intent if 'travel_intent' in locals() else None)

    def _get_enhanced_flights(self, travel_intent: Dict) -> List[Dict]:
        """Get enhanced flight data using legacy manager"""
        destination = travel_intent.get('destination', 'Unknown')
        budget = travel_intent.get('budget', {})
        source_location = travel_intent.get('source_location')
        flight_type = travel_intent.get('flight_type', 'economy')
        budget_amount = budget.get('amount', 'Not specified')
        
        return self.legacy_manager.search_flights_real(
            destination, budget_amount, source_location, flight_type
        )
    
    def _get_enhanced_hotels(self, travel_intent: Dict) -> List[Dict]:
        """Get enhanced hotel data using legacy manager"""
        destination = travel_intent.get('destination', 'Unknown')
        budget = travel_intent.get('budget', {})
        minimum_ratings = travel_intent.get('minimum_ratings')
        hotel_preferences = travel_intent.get('hotel_preferences', [])
        budget_amount = budget.get('amount', 'Not specified')
        
        return self.legacy_manager.search_hotels_real(
            destination, budget_amount, minimum_ratings, hotel_preferences
        )
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string and return number of days"""
        if not duration_str:
            return 3
        
        # Extract number from duration string
        match = re.search(r'(\d+)', duration_str)
        if match:
            return int(match.group(1))
        
        return 3  # Default
    
    def _create_enhanced_itinerary(self, travel_intent: Dict, flights: List[Dict], hotels: List[Dict]) -> List[Dict]:
        """Create enhanced daily itinerary"""
        destination = travel_intent.get('destination', 'Unknown')
        duration_days = self._parse_duration(travel_intent.get('duration', '3 days'))
        travel_style = travel_intent.get('travel_style', 'leisure')
        
        daily_plan = []
        
        for day in range(1, duration_days + 1):
            day_plan = {
                "day": day,
                "theme": self._get_day_theme(day, duration_days, destination, travel_style),
                "activities": self._get_day_activities(day, duration_days, destination, travel_style, flights, hotels)
            }
            daily_plan.append(day_plan)
        
        return daily_plan
    
    def _get_day_theme(self, day: int, total_days: int, destination: str, travel_style: str) -> str:
        """Get theme for specific day"""
        if day == 1:
            return f"Arrival and {destination} Exploration"
        elif day == total_days:
            return f"Final {destination} Experiences and Departure"
        else:
            themes = {
                'luxury': f"Premium {destination} Experiences",
                'budget': f"Affordable {destination} Adventures",
                'adventure': f"Thrilling {destination} Activities",
                'family': f"Family Fun in {destination}",
                'romantic': f"Romantic {destination} Moments",
                'business': f"Business and {destination} Culture",
                'leisure': f"Relaxing {destination} Discovery"
            }
            return themes.get(travel_style, f"{destination} Discovery Day {day}")
    
    def _get_day_activities(self, day: int, total_days: int, destination: str, travel_style: str, flights: List[Dict], hotels: List[Dict]) -> List[Dict]:
        """Get activities for specific day"""
        activities = []
        
        if day == 1:
            # Arrival day
            activities.append({
                "time": "Morning",
                "title": "Airport Arrival and Transfer",
                "description": f"Arrive at {destination} airport and transfer to hotel",
                "cost_estimate": "$50-100",
                "location": destination
            })
            activities.append({
                "time": "Afternoon",
                "title": "Hotel Check-in and Rest",
                "description": f"Check into your selected hotel and freshen up",
                "cost_estimate": "Included in hotel",
                "location": destination
            })
        elif day == total_days:
            # Departure day
            activities.append({
                "time": "Morning",
                "title": "Last Minute Shopping",
                "description": f"Buy souvenirs and last-minute gifts in {destination}",
                "cost_estimate": "$50-200",
                "location": destination
            })
            activities.append({
                "time": "Afternoon",
                "title": "Airport Transfer",
                "description": f"Transfer to {destination} airport for departure",
                "cost_estimate": "$30-80",
                "location": destination
            })
        else:
            # Regular day
            activities.extend(self._get_style_based_activities(destination, travel_style))
        
        return activities
    
    def _get_style_based_activities(self, destination: str, travel_style: str) -> List[Dict]:
        """Get activities based on travel style"""
        style_activities = {
            'luxury': [
                {
                    "time": "Morning",
                    "title": "Premium City Tour",
                    "description": f"Luxury guided tour of {destination} highlights",
                    "cost_estimate": "$150-300",
                    "location": destination
                },
                {
                    "time": "Evening",
                    "title": "Fine Dining Experience",
                    "description": f"Gourmet dinner at top {destination} restaurant",
                    "cost_estimate": "$200-500",
                    "location": destination
                }
            ],
            'budget': [
                {
                    "time": "Morning",
                    "title": "Free Walking Tour",
                    "description": f"Explore {destination} on foot with local guide",
                    "cost_estimate": "Free-20",
                    "location": destination
                },
                {
                    "time": "Afternoon",
                    "title": "Local Street Food",
                    "description": f"Taste authentic {destination} street food",
                    "cost_estimate": "$10-30",
                    "location": destination
                }
            ],
            'adventure': [
                {
                    "time": "Morning",
                    "title": "Adventure Activity",
                    "description": f"Exciting adventure in {destination}",
                    "cost_estimate": "$80-200",
                    "location": destination
                },
                {
                    "time": "Afternoon",
                    "title": "Outdoor Exploration",
                    "description": f"Discover outdoor attractions in {destination}",
                    "cost_estimate": "$30-80",
                    "location": destination
                }
            ]
        }
        
        return style_activities.get(travel_style, [
            {
                "time": "Morning",
                "title": "City Sightseeing",
                "description": f"Explore main attractions in {destination}",
                "cost_estimate": "$50-150",
                "location": destination
            },
            {
                "time": "Afternoon",
                "title": "Cultural Experience",
                "description": f"Immerse in {destination} culture",
                "cost_estimate": "$30-100",
                "location": destination
            }
        ])
    
    def _get_weather_data(self, destination: str) -> Dict[str, Any]:
        """Get weather data for destination"""
        # This would integrate with weather API in production
        return {
            "temperature": "22-28°C",
            "conditions": "Partly Cloudy",
            "humidity": "65%",
            "forecast": "Pleasant weather expected"
        }
    
    def _get_local_experiences(self, travel_intent: Dict) -> List[Dict]:
        """Get local experiences based on travel intent"""
        destination = travel_intent.get('destination', 'Unknown')
        travel_style = travel_intent.get('travel_style', 'leisure')
        
        experiences = [
            {
                "title": f"Historical {destination} Tour",
                "description": f"Discover the rich history of {destination}",
                "category": "Cultural",
                "cost_estimate": "$50-100",
                "duration": "3-4 hours",
                "location": destination,
                "best_time": "Morning",
                "booking_required": True,
                "rating": "4.5 stars",
                "local_tip": "Book in advance for better prices"
            },
            {
                "title": f"Local Cuisine Experience",
                "description": f"Taste authentic {destination} dishes",
                "category": "Food",
                "cost_estimate": "$30-80",
                "duration": "2-3 hours",
                "location": destination,
                "best_time": "Evening",
                "booking_required": False,
                "rating": "4.7 stars",
                "local_tip": "Ask locals for hidden gems"
            }
        ]
        
        return experiences

    def _format_trava_response(self, crew_result: Any, travel_intent: Dict) -> Dict[str, Any]:
        """Format crew result into TRAVA AI response structure"""
        
        try:
            # Parse crew result if it's a string
            if isinstance(crew_result, str):
                try:
                    crew_data = json.loads(crew_result)
                except json.JSONDecodeError:
                    # If not valid JSON, create structured response from text
                    crew_data = self._parse_text_response(str(crew_result))
            else:
                crew_data = crew_result

            # Format into TRAVA AI structure
            trava_response = {
                "trip_summary": {
                    "destination": travel_intent.get('destination', 'Unknown'),
                    "duration": travel_intent.get('duration', 'Unknown'),
                    "travel_style": travel_intent.get('travel_style', 'leisure'),
                    "budget": f"{travel_intent.get('budget', {}).get('amount', 'Not specified')} {travel_intent.get('budget', {}).get('currency', 'USD')}",
                    "source_location": travel_intent.get('source_location', 'Not specified')
                },
                "flights": crew_data.get('flights', []),
                "hotels": crew_data.get('hotels', []),
                "budget_breakdown": crew_data.get('budget_breakdown', {}),
                "daily_plan": crew_data.get('daily_plan', []),
                "validation_status": crew_data.get('validation_status', 'validated'),
                "weather_advisory": crew_data.get('weather_advisory', ''),
                "local_experiences": crew_data.get('local_experiences', [])
            }

            return trava_response

        except Exception as e:
            logger.error(f"Error formatting TRAVA response: {e}")
            return self._get_fallback_response("", travel_intent)

    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse text response into structured data"""
        # This is a simplified parser - in production, you'd use more sophisticated parsing
        return {
            "flights": [],
            "hotels": [],
            "budget_breakdown": {
                "total_estimated_cost": "Contact for quote",
                "flights_cost": "TBD",
                "accommodation_cost": "TBD",
                "activities_food_cost": "TBD",
                "is_within_budget": True,
                "saving_tips": ["Book in advance", "Compare prices"]
            },
            "daily_plan": [],
            "validation_status": "parsed_from_text",
            "weather_advisory": "Weather information available in response text",
            "local_experiences": []
        }

    def _get_fallback_response(self, user_input: str, travel_intent: Dict = None) -> Dict[str, Any]:
        """Fallback response when crew processing fails"""
        
        if not travel_intent:
            travel_intent = self.intent_extractor.extract_travel_intent(user_input)
        
        return {
            "trip_summary": {
                "destination": travel_intent.get('destination', 'Unknown'),
                "duration": travel_intent.get('duration', 'Unknown'),
                "travel_style": travel_intent.get('travel_style', 'leisure'),
                "budget": f"{travel_intent.get('budget', {}).get('amount', 'Not specified')} {travel_intent.get('budget', {}).get('currency', 'USD')}",
                "source_location": travel_intent.get('source_location', 'Not specified')
            },
            "flights": [
                {
                    "airline": "Air India",
                    "price_estimate": "$3500",
                    "duration": "2h 30min",
                    "notes": "Direct flight - Contact for booking"
                }
            ],
            "hotels": [
                {
                    "name": "Grand Hotel",
                    "price_per_night": "$1200",
                    "rating": "4.5 stars",
                    "amenities": ["WiFi", "Pool", "Restaurant"]
                }
            ],
            "budget_breakdown": {
                "total_estimated_cost": f"Estimated for {travel_intent.get('budget', {}).get('amount', 'Not specified')} {travel_intent.get('budget', {}).get('currency', 'USD')}",
                "flights_cost": "$3500",
                "accommodation_cost": "$1200",
                "activities_food_cost": "$700",
                "is_within_budget": True,
                "saving_tips": ["Book in advance", "Compare prices", "Travel off-season"]
            },
            "daily_plan": [
                {
                    "day": 1,
                    "theme": f"Exploring {travel_intent.get('destination', 'destination')}",
                    "activities": [
                        {
                            "time": "Morning",
                            "title": "Arrival & Check-in",
                            "description": f"Arrive at {travel_intent.get('destination', 'destination')}, check into hotel",
                            "cost_estimate": "$200",
                            "location": travel_intent.get('destination', 'destination')
                        }
                    ]
                }
            ],
            "validation_status": "fallback_response",
            "weather_advisory": f"Weather data for {travel_intent.get('destination', 'destination')} - Check local forecast",
            "local_experiences": ["Local attractions", "Cultural sites", "Dining experiences"]
        }
