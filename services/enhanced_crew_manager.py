from utils.logger import logger
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from services.api_driven_crew_manager import APIDrivenTravelCrewManager

class EnhancedTravelCrewManager:
    def __init__(self):
        logger.info("Initializing Enhanced Travel Crew Manager with real-time data capabilities")
        self.api_manager = APIDrivenTravelCrewManager()
        
    def run_crew(self, inputs: dict) -> Dict[str, Any]:
        """Enhanced crew execution with real-time data simulation"""
        logger.info(f"Starting Enhanced Travel Crew with inputs: {inputs}")
        
        try:
            # Extract inputs
            destination = inputs.get('destination', 'Unknown')
            budget = inputs.get('budget', 'Not specified')
            duration = inputs.get('duration', '3 days')
            preferences = inputs.get('preferences', 'general tourism')
            
            # Generate real-time simulated data
            flight_data = self._generate_flight_data(destination, budget)
            hotel_data = self._generate_hotel_data(destination, budget, duration)
            weather_data = self._get_weather_data(destination)
            itinerary_data = self._generate_itinerary(destination, duration, preferences, weather_data)
            budget_analysis = self._analyze_budget(flight_data, hotel_data, budget)
            
            result = {
                "destination": destination,
                "duration": duration,
                "preferences": preferences,
                "flights": flight_data,
                "hotels": hotel_data,
                "itinerary": itinerary_data,
                "budget": budget_analysis,
                "weather_advisory": weather_data.get('advisory', 'Weather data available'),
                "generated_at": datetime.now().isoformat(),
                "data_quality": "real_time_simulated",
                "source": "enhanced_multi_agent_system"
            }
            
            logger.info("Enhanced travel planning completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced travel planning: {e}")
            return self.get_fallback_response(inputs)
    
    def _generate_flight_data(self, destination: str, budget: str) -> List[Dict[str, Any]]:
        """Generate realistic flight data based on destination and budget"""
        airlines = ["Delta Airlines", "United Airlines", "American Airlines", "Lufthansa", "Emirates", "Qatar Airways", "Singapore Airlines", "Japan Airlines"]
        
        # Parse budget
        budget_amount = self._parse_budget(budget)
        flight_budget = budget_amount * 0.3 if budget_amount > 0 else 1500  # 30% of budget for flights
        
        flights = []
        for i in range(3):  # Generate 3 flight options
            airline = random.choice(airlines)
            price = flight_budget + random.randint(-200, 300)
            duration_hours = random.randint(6, 15)
            
            flights.append({
                "airline": airline,
                "price_estimate": f"${price:,}",
                "route": f"From nearest airport to {destination}",
                "duration": f"{duration_hours}h {random.randint(0, 59)}m",
                "stops": random.choice(["Non-stop", "1 Stop", "2 Stops"]),
                "departure_time": f"{random.randint(6, 23):02d}:{random.randint(0, 59):02d}",
                "arrival_time": f"{random.randint(6, 23):02d}:{random.randint(0, 59):02d}",
                "aircraft": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A380"]),
                "booking_class": "Economy",
                "availability": "Available"
            })
        
        return sorted(flights, key=lambda x: self._parse_price(x['price_estimate']))
    
    def _generate_hotel_data(self, destination: str, budget: str, duration: str) -> List[Dict[str, Any]]:
        """Generate realistic hotel data"""
        hotel_chains = ["Marriott", "Hilton", "Hyatt", "InterContinental", "Four Seasons", "Ritz-Carlton", "Sheraton", "Westin"]
        
        # Parse budget and duration
        budget_amount = self._parse_budget(budget)
        duration_days = self._parse_duration(duration)
        hotel_budget_per_night = (budget_amount * 0.4) / duration_days if budget_amount > 0 else 200
        
        hotels = []
        for i in range(4):  # Generate 4 hotel options
            chain = random.choice(hotel_chains)
            base_price = hotel_budget_per_night + random.randint(-50, 150)
            rating = round(random.uniform(3.5, 5.0), 1)
            
            hotels.append({
                "name": f"{chain} {destination}",
                "price_per_night": f"${base_price:,}",
                "rating": f"{rating} ⭐",
                "description": f"Luxury {chain.lower()} hotel in the heart of {destination} with premium amenities",
                "amenities": ["Free WiFi", "Gym", "Pool", "Restaurant", "Spa", "Concierge"],
                "location": f"Central {destination}",
                "room_type": "Deluxe Room",
                "availability": "Available",
                "total_cost": f"${base_price * duration_days:,}",
                "guest_rating": f"{random.randint(8, 10)}/10"
            })
        
        return sorted(hotels, key=lambda x: float(x['rating'].split()[0]), reverse=True)
    
    def _get_weather_data(self, destination: str) -> Dict[str, Any]:
        """Generate realistic weather data"""
        # Simulate weather based on destination (in real app, would call weather API)
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
        temperatures = {
            "summer": (22, 32),
            "winter": (-5, 15),
            "spring": (15, 25),
            "autumn": (10, 20)
        }
        
        season = self._get_current_season()
        temp_range = temperatures.get(season, (15, 25))
        temp = random.randint(temp_range[0], temp_range[1])
        
        return {
            "current_temp": f"{temp}°C",
            "condition": random.choice(weather_conditions),
            "humidity": f"{random.randint(40, 80)}%",
            "wind_speed": f"{random.randint(5, 25)} km/h",
            "advisory": f"{random.choice(weather_conditions)} weather expected. Pack accordingly!",
            "forecast": [
                {"day": "Tomorrow", "temp": f"{temp + random.randint(-3, 3)}°C", "condition": random.choice(weather_conditions)},
                {"day": "Day 2", "temp": f"{temp + random.randint(-3, 3)}°C", "condition": random.choice(weather_conditions)},
                {"day": "Day 3", "temp": f"{temp + random.randint(-3, 3)}°C", "condition": random.choice(weather_conditions)}
            ]
        }
    
    def _generate_itinerary(self, destination: str, duration: str, preferences: str, weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed itinerary based on preferences and weather"""
        duration_days = self._parse_duration(duration)
        
        # Activity pools based on preferences
        activities = {
            "cultural": ["Visit museums", "Historical landmarks tour", "Art galleries", "Cultural performances", "Local festivals"],
            "adventure": ["Hiking excursion", "Water sports", "Mountain climbing", "Safari tour", "Scuba diving"],
            "food": ["Food tour", "Cooking class", "Wine tasting", "Local market visit", "Fine dining experience"],
            "relaxation": ["Spa treatment", "Beach day", "Meditation session", "Yoga class", "Sunset viewing"],
            "shopping": ["Local markets", "Shopping districts", "Souvenir hunting", "Mall exploration", "Boutique visits"],
            "nightlife": ["Bar hopping", "Nightclub tour", "Live music venue", "Rooftop bar", "Cultural night show"]
        }
        
        # Select activities based on preferences
        selected_activities = []
        pref_lower = preferences.lower()
        
        for category, acts in activities.items():
            if any(keyword in pref_lower for keyword in [category, category[:-1]]):
                selected_activities.extend(acts)
        
        # If no specific preferences, add general activities
        if not selected_activities:
            selected_activities = activities["cultural"] + activities["food"] + activities["sightseeing"] if "sightseeing" in activities else activities["cultural"]
        
        itinerary = []
        for day in range(1, duration_days + 1):
            day_theme = random.choice(["Exploration", "Adventure", "Relaxation", "Cultural Immersion", "Local Experience"])
            day_activities = []
            
            # Morning activity
            morning_act = random.choice(selected_activities)
            day_activities.append({
                "time": "09:00 AM",
                "title": morning_act,
                "description": f"Start your day with {morning_act.lower()} in {destination}",
                "cost_estimate": f"${random.randint(20, 100)}",
                "location": destination,
                "duration": "2-3 hours"
            })
            
            # Afternoon activity
            afternoon_act = random.choice(selected_activities)
            day_activities.append({
                "time": "02:00 PM",
                "title": afternoon_act,
                "description": f"Continue with {afternoon_act.lower()} and local experiences",
                "cost_estimate": f"${random.randint(30, 150)}",
                "location": destination,
                "duration": "3-4 hours"
            })
            
            # Evening activity
            evening_act = random.choice(["Dinner at local restaurant", "Evening city tour", "Sunset viewing", "Entertainment show"])
            day_activities.append({
                "time": "07:00 PM",
                "title": evening_act,
                "description": f"Enjoy {evening_act.lower()} to end your day",
                "cost_estimate": f"${random.randint(40, 200)}",
                "location": destination,
                "duration": "2-3 hours"
            })
            
            itinerary.append({
                "day": day,
                "theme": f"Day {day}: {day_theme}",
                "activities": day_activities,
                "weather_tip": f"Weather: {weather_data.get('condition', 'Variable')}, {weather_data.get('current_temp', '20°C')}"
            })
        
        return itinerary
    
    def _analyze_budget(self, flights: List[Dict], hotels: List[Dict], budget: str) -> Dict[str, Any]:
        """Analyze budget and provide recommendations"""
        budget_amount = self._parse_budget(budget)
        
        # Calculate costs
        flight_cost = self._parse_price(flights[0]['price_estimate']) if flights else 0
        hotel_cost = self._parse_price(hotels[0]['total_cost']) if hotels else 0
        
        # Estimate other costs
        activities_cost = budget_amount * 0.2 if budget_amount > 0 else 500
        food_cost = budget_amount * 0.1 if budget_amount > 0 else 300
        
        total_estimated = flight_cost + hotel_cost + activities_cost + food_cost
        
        return {
            "total_estimated_cost": f"${total_estimated:,}",
            "flights_cost": f"${flight_cost:,}",
            "accommodation_cost": f"${hotel_cost:,}",
            "activities_food_cost": f"${activities_cost + food_cost:,}",
            "is_within_budget": total_estimated <= budget_amount if budget_amount > 0 else True,
            "budget_remaining": f"${budget_amount - total_estimated:,}" if budget_amount > 0 else "N/A",
            "saving_tips": [
                "Book flights in advance for better prices",
                "Consider alternative accommodation options",
                "Look for city tourism cards for discounts",
                "Eat at local restaurants for authentic experience",
                "Use public transportation"
            ],
            "budget_breakdown": {
                "Flights": f"{(flight_cost/total_estimated*100):.1f}%",
                "Hotels": f"{(hotel_cost/total_estimated*100):.1f}%",
                "Activities": f"{(activities_cost/total_estimated*100):.1f}%",
                "Food": f"{(food_cost/total_estimated*100):.1f}%"
            }
        }
    
    def _parse_budget(self, budget: str) -> int:
        """Parse budget string to get numeric value"""
        try:
            # Remove currency symbols and commas, convert to int
            cleaned = budget.replace('$', '').replace(',', '').replace('USD', '').strip()
            return int(float(cleaned))
        except:
            return 0
    
    def _parse_price(self, price: str) -> int:
        """Parse price string to get numeric value"""
        try:
            cleaned = price.replace('$', '').replace(',', '').strip()
            return int(float(cleaned))
        except:
            return 0
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to get number of days"""
        try:
            if 'day' in duration.lower():
                return int(duration.split()[0])
            elif 'week' in duration.lower():
                return int(duration.split()[0]) * 7
            elif 'month' in duration.lower():
                return int(duration.split()[0]) * 30
            else:
                return 3  # Default to 3 days
        except:
            return 3
    
    def _get_current_season(self) -> str:
        """Get current season"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def get_fallback_response(self, inputs: dict) -> Dict[str, Any]:
        """Fallback response when enhanced system fails"""
        destination = inputs.get('destination', 'Unknown')
        budget = inputs.get('budget', 'Not specified')
        duration = inputs.get('duration', '3 days')
        
        return {
            "destination": destination,
            "duration": duration,
            "flights": [],
            "hotels": [],
            "itinerary": self._create_basic_itinerary(destination, duration),
            "budget": {
                "total_estimated_cost": f"Error occurred for {budget}",
                "flights_cost": "N/A",
                "accommodation_cost": "N/A",
                "activities_food_cost": "N/A",
                "is_within_budget": False,
                "saving_tips": [],
                "error": "Enhanced system failed"
            },
            "weather_advisory": "Weather data unavailable due to error",
            "error": "Enhanced system failed",
            "source": "fallback"
        }
    
    def _create_basic_itinerary(self, destination: str, duration: str) -> List[Dict[str, Any]]:
        """Create basic itinerary structure"""
        duration_days = self._parse_duration(duration)
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
