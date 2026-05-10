from typing import Dict, List, Any
from utils.logger import logger
import json
from datetime import datetime

class TravaResponseFormatter:
    """TRAVA AI Response Formatter - Creates structured JSON responses"""
    
    def __init__(self):
        logger.info("Initializing TRAVA AI Response Formatter")

    def format_trava_response(self, travel_intent: Dict, flights: List[Dict], 
                            hotels: List[Dict], budget_analysis: Dict[str, Any],
                            daily_plan: List[Dict], weather_data: Dict[str, Any],
                            local_experiences: List[Dict]) -> Dict[str, Any]:
        """
        Format complete travel plan into TRAVA AI specified JSON format
        
        Args:
            travel_intent: Extracted travel intent
            flights: Flight options
            hotels: Hotel options  
            budget_analysis: Budget validation and breakdown
            daily_plan: Day-by-day itinerary
            weather_data: Weather information
            local_experiences: Local activities and experiences
            
        Returns:
            Structured TRAVA AI response
        """
        logger.info("Formatting TRAVA AI response")
        
        try:
            # Extract key information
            destination = travel_intent.get('destination', 'Unknown')
            duration = travel_intent.get('duration', 'Unknown')
            budget_info = travel_intent.get('budget', {})
            
            # Create structured response
            trava_response = {
                "trip_summary": self._create_trip_summary(travel_intent),
                "flights": self._format_flights(flights),
                "hotels": self._format_hotels(hotels),
                "budget_breakdown": self._format_budget_breakdown(budget_analysis),
                "daily_plan": self._format_daily_plan(daily_plan, destination),
                "validation_status": self._get_validation_status(budget_analysis),
                "weather_advisory": self._format_weather_advisory(weather_data, destination),
                "local_experiences": self._format_local_experiences(local_experiences),
                "metadata": self._create_metadata(travel_intent)
            }
            
            logger.info("TRAVA AI response formatted successfully")
            return trava_response
            
        except Exception as e:
            logger.error(f"Error formatting TRAVA response: {e}")
            return self._get_fallback_response()

    def _create_trip_summary(self, travel_intent: Dict) -> Dict[str, Any]:
        """Create comprehensive trip summary"""
        return {
            "destination": travel_intent.get('destination', 'Unknown'),
            "source_location": travel_intent.get('source_location', 'Not specified'),
            "duration": travel_intent.get('duration', 'Unknown'),
            "travel_dates": travel_intent.get('travel_dates', {}),
            "travel_style": travel_intent.get('travel_style', 'leisure'),
            "budget": f"{travel_intent.get('budget', {}).get('amount', 'Not specified')} {travel_intent.get('budget', {}).get('currency', 'USD')}",
            "hotel_preferences": travel_intent.get('hotel_preferences', []),
            "flight_type": travel_intent.get('flight_type', 'economy'),
            "minimum_ratings": travel_intent.get('minimum_ratings'),
            "special_requirements": travel_intent.get('special_requirements', [])
        }

    def _format_flights(self, flights: List[Dict]) -> List[Dict]:
        """Format flight options in TRAVA AI format with ranking information"""
        formatted_flights = []
        
        for i, flight in enumerate(flights[:5], 1):  # Limit to top 5
            formatted_flight = {
                "id": f"flight_{i}",
                "airline": flight.get('airline', 'Unknown Airline'),
                "price_estimate": flight.get('price_estimate', 'Contact for price'),
                "duration": flight.get('duration', 'TBD'),
                "flight_type": flight.get('flight_type', 'economy'),
                "source": flight.get('source', 'Not specified'),
                "destination": flight.get('destination', 'Not specified'),
                "notes": flight.get('notes', 'Standard Flight'),
                "booking_status": "available",
                "verified": bool(flight.get('airline') and flight.get('airline') != 'Unknown Airline'),
                # Add ranking information
                "rank": flight.get('rank', i),
                "ranking_score": flight.get('ranking_score', 0.0),
                "ranking_breakdown": flight.get('ranking_breakdown', {}),
                "recommendation_strength": self._get_recommendation_strength(flight.get('ranking_score', 0.0))
            }
            formatted_flights.append(formatted_flight)
        
        return formatted_flights

    def _format_hotels(self, hotels: List[Dict]) -> List[Dict]:
        """Format hotel options in TRAVA AI format with ranking information"""
        formatted_hotels = []
        
        for i, hotel in enumerate(hotels[:5], 1):  # Limit to top 5
            formatted_hotel = {
                "id": f"hotel_{i}",
                "name": hotel.get('name', 'Unknown Hotel'),
                "price_per_night": hotel.get('price_per_night', 'Contact for price'),
                "rating": hotel.get('rating', 'Not rated'),
                "amenities": hotel.get('amenities', []),
                "verified": hotel.get('verified', False),
                "booking_url": hotel.get('booking_url_mock', ''),
                "location": hotel.get('location', 'City Center'),
                "room_types": ["Standard", "Deluxe", "Suite"],
                "check_in": "Flexible",
                "check_out": "11:00 AM",
                # Add ranking information
                "rank": hotel.get('rank', i),
                "ranking_score": hotel.get('ranking_score', 0.0),
                "ranking_breakdown": hotel.get('ranking_breakdown', {}),
                "recommendation_strength": self._get_recommendation_strength(hotel.get('ranking_score', 0.0))
            }
            formatted_hotels.append(formatted_hotel)
        
        return formatted_hotels

    def _format_budget_breakdown(self, budget_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format budget breakdown in TRAVA AI format"""
        budget_validation = budget_analysis.get('budget_validation', {})
        cost_breakdown = budget_analysis.get('cost_breakdown', {})
        
        return {
            "total_estimated_cost": budget_validation.get('total_estimated_cost_original', 'Not available'),
            "flights_cost": cost_breakdown.get('flights', {}).get('cost_original', 'Not available'),
            "accommodation_cost": cost_breakdown.get('accommodation', {}).get('cost_original', 'Not available'),
            "activities_food_cost": cost_breakdown.get('daily_expenses', {}).get('cost_original', 'Not available'),
            "contingency_cost": cost_breakdown.get('contingency', {}).get('cost_original', 'Not available'),
            "is_within_budget": budget_validation.get('is_within_budget', False),
            "budget_variance": f"{budget_validation.get('budget_variance_percentage', 0):.1f}%",
            "currency": budget_analysis.get('currency', 'USD'),
            "daily_breakdown": cost_breakdown.get('daily_expenses', {}).get('per_day_breakdown', {}),
            "optimization_tips": budget_analysis.get('optimization_suggestions', [])
        }

    def _format_daily_plan(self, daily_plan: List[Dict], destination: str) -> List[Dict]:
        """Format daily itinerary in TRAVA AI format"""
        formatted_plan = []
        
        for day_data in daily_plan:
            formatted_day = {
                "day": day_data.get('day', 1),
                "theme": day_data.get('theme', f'Exploring {destination}'),
                "activities": []
            }
            
            # Format activities
            for activity in day_data.get('activities', []):
                formatted_activity = {
                    "time": activity.get('time', 'Flexible'),
                    "title": activity.get('title', 'Activity'),
                    "description": activity.get('description', 'Activity description'),
                    "cost_estimate": activity.get('cost_estimate', 'Not specified'),
                    "location": activity.get('location', destination),
                    "duration": "2-3 hours",
                    "type": "sightseeing",
                    "booking_required": False
                }
                formatted_day["activities"].append(formatted_activity)
            
            formatted_plan.append(formatted_day)
        
        return formatted_plan

    def _get_validation_status(self, budget_analysis: Dict[str, Any]) -> str:
        """Get overall validation status"""
        budget_validation = budget_analysis.get('budget_validation', {})
        budget_compliance = budget_analysis.get('budget_compliance', {})
        
        # Check all validation criteria
        is_within_budget = budget_validation.get('is_within_budget', False)
        rating_requirements_met = budget_compliance.get('rating_requirements_met', False)
        hotel_preferences_matched = budget_compliance.get('hotel_preferences_matched', False)
        flight_preferences_matched = budget_compliance.get('flight_preferences_matched', False)
        
        if all([is_within_budget, rating_requirements_met, hotel_preferences_matched, flight_preferences_matched]):
            return "fully_validated"
        elif is_within_budget and rating_requirements_met:
            return "partially_validated"
        else:
            return "needs_review"

    def _format_weather_advisory(self, weather_data: Dict[str, Any], destination: str) -> str:
        """Format weather advisory"""
        if not weather_data:
            return f"Weather data for {destination} - Check local forecast before travel"
        
        temperature = weather_data.get('temperature', 'Not available')
        conditions = weather_data.get('conditions', 'Not specified')
        humidity = weather_data.get('humidity', 'Not specified')
        
        advisory = f"Weather forecast for {destination}: "
        advisory += f"{conditions}, Temperature: {temperature}"
        if humidity != 'Not specified':
            advisory += f", Humidity: {humidity}"
        advisory += ". Pack accordingly and check for weather updates before travel."
        
        return advisory

    def _format_local_experiences(self, local_experiences: List[Dict]) -> List[Dict]:
        """Format local experiences and activities with ranking information"""
        formatted_experiences = []
        
        for i, experience in enumerate(local_experiences[:10], 1):  # Limit to top 10
            formatted_experience = {
                "id": f"experience_{i}",
                "title": experience.get('title', 'Local Experience'),
                "description": experience.get('description', 'Experience description'),
                "category": experience.get('category', 'General'),
                "cost_estimate": experience.get('cost_estimate', 'Not specified'),
                "duration": experience.get('duration', '2-3 hours'),
                "location": experience.get('location', 'City Center'),
                "best_time": experience.get('best_time', 'Flexible'),
                "booking_required": experience.get('booking_required', False),
                "rating": experience.get('rating', 'Not rated'),
                "local_tip": experience.get('local_tip', 'Ask locals for recommendations'),
                # Add ranking information
                "rank": experience.get('rank', i),
                "ranking_score": experience.get('ranking_score', 0.0),
                "ranking_breakdown": experience.get('ranking_breakdown', {}),
                "recommendation_strength": self._get_recommendation_strength(experience.get('ranking_score', 0.0))
            }
            formatted_experiences.append(formatted_experience)
        
        return formatted_experiences

    def _create_metadata(self, travel_intent: Dict) -> Dict[str, Any]:
        """Create metadata for the response"""
        return {
            "generated_at": datetime.now().isoformat(),
            "system": "TRAVA AI",
            "version": "1.0",
            "request_id": f"trava_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "processing_time": "Real-time",
            "data_sources": ["Real-time search", "Verified databases", "API integrations"],
            "disclaimer": "Prices and availability are subject to change. Please verify before booking.",
            "contact_support": "For assistance, contact TRAVA AI support"
        }

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Fallback response if formatting fails"""
        return {
            "trip_summary": {
                "destination": "Unknown",
                "duration": "Unknown",
                "travel_style": "leisure",
                "budget": "Not specified"
            },
            "flights": [],
            "hotels": [],
            "budget_breakdown": {
                "total_estimated_cost": "Not available",
                "is_within_budget": False,
                "optimization_tips": ["Please provide more details for better recommendations"]
            },
            "daily_plan": [],
            "validation_status": "error",
            "weather_advisory": "Weather information not available",
            "local_experiences": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "system": "TRAVA AI",
                "version": "1.0",
                "error": "Response formatting failed"
            }
        }

    def validate_response_structure(self, response: Dict[str, Any]) -> bool:
        """Validate that response meets TRAVA AI structure requirements"""
        required_sections = [
            "trip_summary", "flights", "hotels", "budget_breakdown", 
            "daily_plan", "validation_status", "weather_advisory", 
            "local_experiences", "metadata"
        ]
        
        for section in required_sections:
            if section not in response:
                logger.error(f"Missing required section: {section}")
                return False
        
        # Validate trip summary
        trip_summary = response.get("trip_summary", {})
        required_summary_fields = ["destination", "duration", "travel_style", "budget"]
        for field in required_summary_fields:
            if field not in trip_summary:
                logger.error(f"Missing trip summary field: {field}")
                return False
        
        # Validate budget breakdown
        budget_breakdown = response.get("budget_breakdown", {})
        required_budget_fields = ["total_estimated_cost", "is_within_budget"]
        for field in required_budget_fields:
            if field not in budget_breakdown:
                logger.error(f"Missing budget breakdown field: {field}")
                return False
        
        logger.info("Response structure validation passed")
        return True

    def get_response_summary(self, response: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the response"""
        trip_summary = response.get("trip_summary", {})
        budget_breakdown = response.get("budget_breakdown", {})
        flights = response.get("flights", [])
        hotels = response.get("hotels", [])
        
        summary = f"TRAVA AI Travel Plan for {trip_summary.get('destination', 'Unknown')}\n"
        summary += f"Duration: {trip_summary.get('duration', 'Unknown')}\n"
        summary += f"Style: {trip_summary.get('travel_style', 'leisure')}\n"
        summary += f"Budget: {trip_summary.get('budget', 'Not specified')}\n\n"
        
        summary += f"Flight Options: {len(flights)} available\n"
        summary += f"Hotel Options: {len(hotels)} available\n"
        summary += f"Total Cost: {budget_breakdown.get('total_estimated_cost', 'Not available')}\n"
        summary += f"Within Budget: {'Yes' if budget_breakdown.get('is_within_budget', False) else 'No'}\n"
        summary += f"Validation Status: {response.get('validation_status', 'unknown')}\n"
        
        return summary

    def _get_recommendation_strength(self, score: float) -> str:
        """Convert ranking score to recommendation strength"""
        if score >= 0.8:
            return "Highly Recommended"
        elif score >= 0.6:
            return "Recommended"
        elif score >= 0.4:
            return "Consider"
        else:
            return "Alternative Option"
