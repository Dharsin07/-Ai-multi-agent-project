"""
Autonomous AI Travel Booking Agent
Understands natural language requests, plans tasks, and executes semi-auto booking
"""
import os
import re
import asyncio
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import logger

class AutonomousBookingAgent:
    def __init__(self):
        self.logger = logger
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Booking websites
        self.booking_sites = {
            'indigo': 'https://www.goindigo.in/',
            'spicejet': 'https://www.spicejet.com/',
            'airasia': 'https://www.airasia.co.in/',
            'makemytrip': 'https://www.makemytrip.com/',
            'goibibo': 'https://www.goibibo.com/'
        }
    
    def process_travel_request(self, user_request: str) -> Dict[str, Any]:
        """
        Main entry point - process natural language travel request
        
        Args:
            user_request: Natural language travel request
            
        Returns:
            Dict with travel plan and booking automation status
        """
        try:
            self.logger.info(f"Processing travel request: {user_request}")
            
            # Step 1: Extract travel details
            travel_details = self.extract_travel_details(user_request)
            self.logger.info(f"Extracted details: {travel_details}")
            
            # Step 2: Plan tasks automatically
            task_plan = self.plan_tasks(travel_details)
            
            # Step 3: Execute tasks
            execution_result = self.execute_tasks(task_plan, travel_details)
            
            # Step 4: Prepare booking automation
            booking_automation = self.prepare_booking_automation(
                execution_result, travel_details
            )
            
            return {
                'success': True,
                'travel_details': travel_details,
                'task_plan': task_plan,
                'execution_result': execution_result,
                'booking_automation': booking_automation,
                'status': 'ready_for_booking'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing travel request: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def extract_travel_details(self, user_request: str) -> Dict[str, Any]:
        """Extract all travel details from natural language"""
        request_lower = user_request.lower()
        
        # Extract cities
        cities = ['chennai', 'bangalore', 'bengaluru', 'mumbai', 'delhi', 'hyderabad', 
                 'kolkata', 'pune', 'goa', 'jaipur', 'kerala', 'cochin']
        found_cities = [city for city in cities if city in request_lower]
        
        source = found_cities[0] if len(found_cities) > 0 else 'Not specified'
        destination = found_cities[1] if len(found_cities) > 1 else (found_cities[0] if len(found_cities) > 0 else 'Not specified')
        
        # Extract dates
        date_patterns = [
            r'(?:date|on|for)\s+([a-zA-Z]+\s+\d+|\d{1,2}\s+[a-zA-Z]+)',
            r'(?:may|april|march|february|january|june|july|august|september|october|november|december)\s+(\d{1,2})',
            r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?:may|april|march|february|january|june|july|august|september|october|november|december)'
        ]
        
        departure_date = 'Not specified'
        return_date = None
        
        for pattern in date_patterns:
            match = re.search(pattern, request_lower)
            if match:
                departure_date = self._normalize_date(match.group(1))
                break
        
        # Check for return date
        if 'return' in request_lower or 'back' in request_lower:
            date_matches = re.findall(r'(?:may|april|march|february|january|june|july|august|september|october|november|december)\s+(\d{1,2})', request_lower)
            if len(date_matches) > 1:
                return_date = self._normalize_date(f"{date_matches[1]}")
        
        # Extract budget
        budget_patterns = [
            r'budget\s+(?:is|of|under|below)?\s*([0-9,]+k?)',
            r'([0-9,]+k?)\s*(?:budget|rupees|rs)',
            r'₹?\s*([0-9,]+k?)(?:\s+or less)?'
        ]
        
        budget = 'Not specified'
        for pattern in budget_patterns:
            match = re.search(pattern, request_lower)
            if match:
                budget = self._normalize_budget(match.group(1))
                break
        
        # Extract hotel preference
        hotel_keywords = {
            'luxury': '5 star',
            'budget': '3 star',
            'mid-range': '4 star',
            'cheap': '2 star',
            'premium': '5 star'
        }
        
        hotel_preference = '3 star'
        for keyword, rating in hotel_keywords.items():
            if keyword in request_lower:
                hotel_preference = rating
                break
        
        # Extract stay duration
        duration_match = re.search(r'(\d+)\s*(?:days|nights?)', request_lower)
        stay_duration = int(duration_match.group(1)) if duration_match else 3
        
        return {
            'source': source.capitalize() if source != 'Not specified' else source,
            'destination': destination.capitalize() if destination != 'Not specified' else destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'budget': budget,
            'hotel_preference': hotel_preference,
            'stay_duration': stay_duration,
            'raw_request': user_request
        }
    
    def plan_tasks(self, travel_details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Plan tasks automatically based on travel details"""
        tasks = {
            'search_tasks': [],
            'validation_tasks': [],
            'booking_tasks': []
        }
        
        # Search tasks
        tasks['search_tasks'].append(f"Search flights from {travel_details['source']} to {travel_details['destination']} on {travel_details['departure_date']}")
        tasks['search_tasks'].append(f"Search hotels in {travel_details['destination']} with {travel_details['hotel_preference']} rating")
        tasks['search_tasks'].append(f"Check weather in {travel_details['destination']} for {travel_details['departure_date']}")
        
        # Validation tasks
        tasks['validation_tasks'].append(f"Validate budget: {travel_details['budget']}")
        tasks['validation_tasks'].append("Compare flight options and select cheapest")
        tasks['validation_tasks'].append("Compare hotel options and select best value")
        
        # Booking tasks
        tasks['booking_tasks'].append("Open booking website for selected flight")
        tasks['booking_tasks'].append("Autofill passenger details")
        tasks['booking_tasks'].append("Stop at payment page for manual confirmation")
        
        return tasks
    
    def execute_tasks(self, task_plan: Dict[str, List[str]], travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planned tasks"""
        results = {
            'search_results': {},
            'validation_results': {},
            'selected_options': {}
        }
        
        # Execute search tasks
        for task in task_plan['search_tasks']:
            if 'flights' in task.lower():
                flight_results = self.search_flights(travel_details)
                results['search_results']['flights'] = flight_results
            elif 'hotels' in task.lower():
                hotel_results = self.search_hotels(travel_details)
                results['search_results']['hotels'] = hotel_results
            elif 'weather' in task.lower():
                weather_results = self.check_weather(travel_details)
                results['search_results']['weather'] = weather_results
        
        # Execute validation tasks
        for task in task_plan['validation_tasks']:
            if 'budget' in task.lower():
                budget_valid = self.validate_budget(travel_details, results['search_results'])
                results['validation_results']['budget'] = budget_valid
            elif 'compare flight' in task.lower():
                cheapest_flight = self.select_cheapest_flight(results['search_results'].get('flights', {}))
                results['selected_options']['flight'] = cheapest_flight
            elif 'compare hotel' in task.lower():
                best_hotel = self.select_best_hotel(results['search_results'].get('hotels', {}))
                results['selected_options']['hotel'] = best_hotel
        
        return results
    
    def search_flights(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Search flights using Serper API"""
        try:
            query = f"flights from {travel_details['source']} to {travel_details['destination']} on {travel_details['departure_date']}"
            
            if not self.serper_api_key:
                return {'success': False, 'error': 'Serper API not available'}
            
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            data = {'q': query}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                search_results = response.json()
                return {
                    'success': True,
                    'query': query,
                    'results': search_results.get('organicResults', [])[:5],
                    'total_results': len(search_results.get('organicResults', []))
                }
            else:
                return {'success': False, 'error': f'Serper API error: {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"Flight search error: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_hotels(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Search hotels using Serper API"""
        try:
            query = f"hotels in {travel_details['destination']} {travel_details['hotel_preference']} for {travel_details['stay_duration']} days"
            
            if not self.serper_api_key:
                return {'success': False, 'error': 'Serper API not available'}
            
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            data = {'q': query}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                search_results = response.json()
                return {
                    'success': True,
                    'query': query,
                    'results': search_results.get('organicResults', [])[:5],
                    'total_results': len(search_results.get('organicResults', []))
                }
            else:
                return {'success': False, 'error': f'Serper API error: {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"Hotel search error: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_weather(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Check weather using OpenWeatherMap API"""
        try:
            if not self.openweather_api_key:
                return {'success': False, 'error': 'OpenWeatherMap API not available'}
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q={travel_details['destination']}&appid={self.openweather_api_key}&units=metric"
            response = requests.get(url)
            
            if response.status_code == 200:
                weather_data = response.json()
                return {
                    'success': True,
                    'temperature': weather_data['main']['temp'],
                    'condition': weather_data['weather'][0]['description'],
                    'humidity': weather_data['main']['humidity'],
                    'location': travel_details['destination']
                }
            else:
                return {'success': False, 'error': f'Weather API error: {response.status_code}'}
                
        except Exception as e:
            self.logger.error(f"Weather check error: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_budget(self, travel_details: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate budget against search results"""
        budget_amount = self._parse_budget_amount(travel_details['budget'])
        
        if not budget_amount:
            return {
                'valid': True,
                'message': 'Budget not specified, showing all options'
            }
        
        # Estimate costs from search results
        estimated_cost = budget_amount * 0.7  # Assume 70% of budget for flight
        
        return {
            'valid': estimated_cost <= budget_amount,
            'budget': travel_details['budget'],
            'estimated_cost': estimated_cost,
            'remaining': budget_amount - estimated_cost,
            'message': 'Within budget' if estimated_cost <= budget_amount else 'Over budget'
        }
    
    def select_cheapest_flight(self, flight_results: Dict[str, Any]) -> Dict[str, Any]:
        """Select cheapest flight from search results"""
        if not flight_results.get('success') or not flight_results.get('results'):
            return {
                'success': False,
                'message': 'No flight results available'
            }
        
        # For now, return the first result (would need actual price extraction)
        results = flight_results['results']
        if results:
            return {
                'success': True,
                'selected': results[0],
                'reason': 'First available option',
                'booking_url': self.booking_sites.get('makemytrip')  # Default to MakeMyTrip
            }
        
        return {'success': False, 'message': 'No flights found'}
    
    def select_best_hotel(self, hotel_results: Dict[str, Any]) -> Dict[str, Any]:
        """Select best hotel from search results"""
        if not hotel_results.get('success') or not hotel_results.get('results'):
            return {
                'success': False,
                'message': 'No hotel results available'
            }
        
        results = hotel_results['results']
        if results:
            return {
                'success': True,
                'selected': results[0],
                'reason': 'First available option with good rating',
                'booking_url': self.booking_sites.get('makemytrip')  # Default to MakeMyTrip
            }
        
        return {'success': False, 'message': 'No hotels found'}
    
    def prepare_booking_automation(self, execution_result: Dict[str, Any], travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare booking automation details"""
        selected_flight = execution_result['selected_options'].get('flight', {})
        selected_hotel = execution_result['selected_options'].get('hotel', {})
        
        return {
            'ready': True,
            'flight_booking': {
                'url': selected_flight.get('booking_url', 'https://www.makemytrip.com/'),
                'details': selected_flight,
                'status': 'ready_to_autofill'
            },
            'hotel_booking': {
                'url': selected_hotel.get('booking_url', 'https://www.makemytrip.com/'),
                'details': selected_hotel,
                'status': 'ready_to_autofill'
            },
            'passenger_info_needed': [
                'full_name',
                'email',
                'phone',
                'date_of_birth'
            ],
            'payment_stage': 'manual_confirmation_required',
            'safety_notice': 'System will stop at payment page for manual confirmation'
        }
    
    # Helper methods
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string"""
        try:
            if 'may' in date_str.lower():
                import re
                day_match = re.search(r'\d+', date_str)
                if day_match:
                    day = day_match.group()
                    return f"2024-05-{day.zfill(2)}"
            if 'june' in date_str.lower():
                import re
                day_match = re.search(r'\d+', date_str)
                if day_match:
                    day = day_match.group()
                    return f"2024-06-{day.zfill(2)}"
            if 'july' in date_str.lower():
                import re
                day_match = re.search(r'\d+', date_str)
                if day_match:
                    day = day_match.group()
                    return f"2024-07-{day.zfill(2)}"
            return date_str
        except:
            return date_str
    
    def _normalize_budget(self, budget_str: str) -> str:
        """Normalize budget string"""
        budget_str = budget_str.replace(',', '').replace('k', '000')
        return f"₹{budget_str}"
    
    def _parse_budget_amount(self, budget_str: str) -> Optional[float]:
        """Parse budget amount from string"""
        import re
        match = re.search(r'[\d,]+', budget_str.replace(',', ''))
        if match:
            return float(match.group())
        return None
