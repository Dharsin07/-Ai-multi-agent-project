"""
Working Crew Manager with Available APIs
Uses Groq, Serper, and OpenWeatherMap APIs for functional travel planning
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from utils.logger import logger

class WorkingCrewManager:
    def __init__(self):
        """Initialize crew manager with available APIs"""
        self.logger = logger
        
        # Available API keys
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        
        self.logger.info("Working Crew Manager initialized with available APIs")
    
    def run_travel_planning(self, user_request: str) -> Dict[str, Any]:
        """Run travel planning with available APIs"""
        try:
            self.logger.info(f"Processing travel request: {user_request}")
            
            # Extract travel details
            travel_details = self._extract_travel_details(user_request)
            
            # Get weather data
            weather_data = self._get_weather_data(travel_details['destination'], travel_details['date'])
            
            # Get web search data for travel information
            search_data = self._get_travel_search_data(travel_details)
            
            # Generate travel plan using Groq LLM
            travel_plan = self._generate_travel_plan_with_llm(travel_details, weather_data, search_data, user_request)
            
            return {
                'success': True,
                'travel_plan': travel_plan,
                'travel_details': travel_details,
                'weather_data': weather_data,
                'search_data': search_data,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_sources': ['Groq LLM', 'Serper Search', 'OpenWeatherMap'],
                    'apis_used': ['GROQ_API_KEY', 'SERPER_API_KEY', 'OPENWEATHERMAP_API_KEY']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in travel planning: {e}")
            return {
                'success': False,
                'error': str(e),
                'travel_plan': None
            }
    
    def _extract_travel_details(self, user_request: str) -> Dict[str, Any]:
        """Extract travel details from user request"""
        import re
        
        request_lower = user_request.lower()
        
        # Extract cities
        cities = ['chennai', 'bangalore', 'bengaluru', 'mumbai', 'delhi', 'hyderabad', 'kolkata', 'pune']
        found_cities = [city for city in cities if city in request_lower]
        
        origin = found_cities[0] if len(found_cities) > 0 else 'Not specified'
        destination = found_cities[1] if len(found_cities) > 1 else (found_cities[0] if len(found_cities) > 0 else 'Not specified')
        
        # Extract date
        date_match = re.search(r'(?:date|on|for)\s+([a-zA-Z]+\s+\d+|\d{1,2}\s+[a-zA-Z]+)', request_lower)
        date = date_match.group(1) if date_match else 'May 25'
        
        # Extract budget
        budget_match = re.search(r'budget\s+(?:is|of)?\s*([0-9,]+k?)', request_lower)
        budget = budget_match.group(1) if budget_match else '15k'
        
        # Extract rating requirement
        rating_match = re.search(r'(\d+)\s*\+\s*star|above\s+(\d+)\s+star', request_lower)
        min_rating = 4.0 if rating_match else 3.5
        
        return {
            'origin': origin.capitalize() if origin != 'Not specified' else origin,
            'destination': destination.capitalize() if destination != 'Not specified' else destination,
            'date': date,
            'budget': budget,
            'min_rating': min_rating,
            'raw_request': user_request
        }
    
    def _get_weather_data(self, destination: str, date: str) -> Dict[str, Any]:
        """Get weather data using OpenWeatherMap API"""
        try:
            if not self.openweather_api_key or destination == 'Not specified':
                return {'success': False, 'error': 'Weather API not available or destination not specified'}
            
            # Get current weather
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={destination}&appid={self.openweather_api_key}&units=metric"
            response = requests.get(weather_url)
            
            if response.status_code == 200:
                weather_data = response.json()
                
                # Get forecast
                forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={destination}&appid={self.openweather_api_key}&units=metric"
                forecast_response = requests.get(forecast_url)
                
                forecast_data = {}
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                
                return {
                    'success': True,
                    'current': {
                        'temperature': weather_data['main']['temp'],
                        'feels_like': weather_data['main']['feels_like'],
                        'humidity': weather_data['main']['humidity'],
                        'condition': weather_data['weather'][0]['description'],
                        'wind_speed': weather_data['wind']['speed']
                    },
                    'forecast': forecast_data,
                    'location': destination
                }
            else:
                return {'success': False, 'error': f'Weather API error: {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"Weather API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_travel_search_data(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get travel information using Serper API"""
        try:
            if not self.serper_api_key:
                return {'success': False, 'error': 'Serper API not available'}
            
            # Search for flights
            flight_query = f"flights from {travel_details['origin']} to {travel_details['destination']} on {travel_details['date']}"
            flight_data = self._search_with_serper(flight_query)
            
            # Search for hotels
            hotel_query = f"hotels in {travel_details['destination']} with {travel_details['min_rating']} star rating budget {travel_details['budget']}"
            hotel_data = self._search_with_serper(hotel_query)
            
            # Search for travel tips
            tips_query = f"travel tips for {travel_details['destination']} weather best time to visit"
            tips_data = self._search_with_serper(tips_query)
            
            return {
                'success': True,
                'flights': flight_data,
                'hotels': hotel_data,
                'tips': tips_data
            }
            
        except Exception as e:
            self.logger.error(f"Search API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_with_serper(self, query: str) -> Dict[str, Any]:
        """Search using Serper API"""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            data = {'q': query}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Serper API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_travel_plan_with_llm(self, travel_details: Dict[str, Any], 
                                     weather_data: Dict[str, Any], 
                                     search_data: Dict[str, Any], 
                                     user_request: str) -> Dict[str, Any]:
        """Generate travel plan using Groq LLM"""
        try:
            if not self.groq_api_key:
                return self._generate_fallback_plan(travel_details, weather_data, search_data)
            
            # Prepare prompt for Groq
            prompt = self._create_llm_prompt(travel_details, weather_data, search_data, user_request)
            
            # Call Groq API
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert travel planning assistant. Provide detailed, practical travel advice.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 2000,
                'temperature': 0.7
            }
            
            response = requests.post(groq_url, headers=headers, json=data)
            
            if response.status_code == 200:
                llm_response = response.json()
                plan_text = llm_response['choices'][0]['message']['content']
                
                return self._parse_llm_response(plan_text, travel_details, weather_data, search_data)
            else:
                self.logger.error(f"Groq API error: {response.status_code}")
                return self._generate_fallback_plan(travel_details, weather_data, search_data)
                
        except Exception as e:
            self.logger.error(f"LLM generation error: {e}")
            return self._generate_fallback_plan(travel_details, weather_data, search_data)
    
    def _create_llm_prompt(self, travel_details: Dict[str, Any], 
                          weather_data: Dict[str, Any], 
                          search_data: Dict[str, Any], 
                          user_request: str) -> str:
        """Create comprehensive prompt for LLM"""
        
        weather_info = ""
        if weather_data.get('success'):
            current = weather_data['current']
            weather_info = f"""
Current Weather in {travel_details['destination']}:
- Temperature: {current['temperature']}°C (feels like {current['feels_like']}°C)
- Condition: {current['condition']}
- Humidity: {current['humidity']}%
- Wind Speed: {current['wind_speed']} m/s
"""
        
        search_info = ""
        if search_data.get('success'):
            search_info = f"""
Search Results Available:
- Flight information: {'Found' if search_data.get('flights') else 'Not found'}
- Hotel information: {'Found' if search_data.get('hotels') else 'Not found'}
- Travel tips: {'Found' if search_data.get('tips') else 'Not found'}
"""
        
        prompt = f"""
Create a comprehensive travel plan for the following request:

USER REQUEST: {user_request}

TRAVEL DETAILS:
- Origin: {travel_details['origin']}
- Destination: {travel_details['destination']}
- Date: {travel_details['date']}
- Budget: {travel_details['budget']}
- Minimum Hotel Rating: {travel_details['min_rating']} stars

{weather_info}

{search_info}

Please provide a detailed travel plan including:
1. Flight recommendations (with estimated prices)
2. Hotel recommendations (with ratings and prices)
3. Weather-based travel advice
4. Budget breakdown
5. Day-by-day itinerary
6. Travel tips and recommendations

Format the response in a structured, easy-to-read format with clear sections.
"""
        
        return prompt
    
    def _parse_llm_response(self, plan_text: str, travel_details: Dict[str, Any], 
                          weather_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        
        # Create structured plan from LLM response
        return {
            'overview': {
                'origin': travel_details['origin'],
                'destination': travel_details['destination'],
                'date': travel_details['date'],
                'budget': travel_details['budget']
            },
            'llm_generated_plan': plan_text,
            'weather_advisory': weather_data,
            'search_results': search_data,
            'recommendations': self._extract_recommendations_from_text(plan_text),
            'budget_estimates': self._extract_budget_info_from_text(plan_text)
        }
    
    def _generate_fallback_plan(self, travel_details: Dict[str, Any], 
                             weather_data: Dict[str, Any], 
                             search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback plan without LLM"""
        
        return {
            'overview': {
                'origin': travel_details['origin'],
                'destination': travel_details['destination'],
                'date': travel_details['date'],
                'budget': travel_details['budget']
            },
            'flights': {
                'estimated_cost': '₹3,000 - ₹6,000',
                'recommendation': 'Book morning flights for better prices',
                'airlines': ['IndiGo', 'SpiceJet', 'AirAsia']
            },
            'hotels': {
                'estimated_cost': '₹2,000 - ₹4,000 per night',
                'recommendation': f'Look for {travel_details["min_rating"]}+ star hotels near city center',
                'areas': ['MG Road', 'Brigade Road', 'Koramangala']
            },
            'weather': weather_data,
            'total_estimated_budget': '₹8,000 - ₹12,000',
            'within_budget': True
        }
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from LLM text"""
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'tip', 'suggest', 'advice']):
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _extract_budget_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract budget information from LLM text"""
        import re
        
        budget_info = {
            'total_estimate': 'Not specified',
            'flight_cost': 'Not specified',
            'hotel_cost': 'Not specified',
            'other_costs': 'Not specified'
        }
        
        # Look for price patterns
        price_patterns = re.findall(r'[₹$]\s*[\d,]+', text)
        if price_patterns:
            budget_info['total_estimate'] = price_patterns[0] if price_patterns else 'Not specified'
        
        return budget_info
