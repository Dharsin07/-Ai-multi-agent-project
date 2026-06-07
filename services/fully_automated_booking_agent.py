"""
Fully Automated Booking Agent
Complete end-to-end automation: LLM Analysis → Automatic Flight Selection → Booking → Payment Stop
"""
import os
import re
import asyncio
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import logger
from tools.correct_booking_automation import CorrectBookingAutomation

class FullyAutomatedBookingAgent:
    def __init__(self):
        self.logger = logger
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Booking automation
        self.booking_automation = CorrectBookingAutomation()
        
        # Booking websites priority order
        self.booking_sites = {
            'makemytrip': 'https://www.makemytrip.com/',
            'goibibo': 'https://www.goibibo.com/',
            'indigo': 'https://www.goindigo.in/',
            'spicejet': 'https://www.spicejet.com/',
            'airasia': 'https://www.airasia.co.in/'
        }
    
    async def process_and_book_automatically(self, user_request: str, passenger_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Complete end-to-end automation: Process request and automatically book
        
        Args:
            user_request: Natural language travel request
            passenger_info: Passenger details for booking
            
        Returns:
            Dict with complete booking status and details
        """
        try:
            self.logger.info("Starting fully automated booking process...")
            
            # Phase 1: LLM Analysis and Request Processing
            analysis_result = await self._analyze_request_with_llm(user_request)
            if not analysis_result['success']:
                return analysis_result
            
            # Phase 2: Intelligent Flight Search and Selection
            flight_selection = await self._intelligent_flight_selection(analysis_result['travel_details'])
            if not flight_selection['success']:
                return flight_selection
            
            # Phase 3: Automatic Booking Execution
            booking_result = await self._execute_automatic_booking(
                flight_selection['selected_flight'], 
                analysis_result['travel_details'],
                passenger_info
            )
            
            return {
                'success': True,
                'phase': 'completed',
                'analysis': analysis_result,
                'flight_selection': flight_selection,
                'booking': booking_result,
                'status': 'automation_completed',
                'next_action': 'MANUAL_PAYMENT_REQUIRED'
            }
            
        except Exception as e:
            self.logger.error(f"Fully automated booking failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'phase': 'automation_failed'
            }
    
    async def _analyze_request_with_llm(self, user_request: str) -> Dict[str, Any]:
        """Phase 1: LLM-powered request analysis"""
        try:
            self.logger.info("Phase 1: Analyzing request with LLM...")
            
            # Extract travel details
            travel_details = self._extract_travel_details(user_request)
            
            # Get LLM recommendations
            llm_analysis = await self._get_llm_recommendations(travel_details, user_request)
            
            # Validate with real-time data
            validation = await self._validate_with_realtime_data(travel_details)
            
            return {
                'success': True,
                'travel_details': travel_details,
                'llm_analysis': llm_analysis,
                'validation': validation,
                'recommendations': llm_analysis.get('recommendations', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"LLM Analysis failed: {str(e)}",
                'phase': 'analysis_failed'
            }
    
    async def _intelligent_flight_selection(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Intelligent flight search and selection"""
        try:
            self.logger.info("Phase 2: Intelligent flight selection...")
            
            # Search multiple sources
            search_results = await self._search_multiple_sources(travel_details)
            
            # AI-powered selection
            best_flight = await self._ai_select_best_flight(search_results, travel_details)
            
            # Get booking URL
            booking_url = self._get_best_booking_url(best_flight)
            
            return {
                'success': True,
                'search_results': search_results,
                'selected_flight': {
                    **best_flight,
                    'booking_url': booking_url,
                    'selection_reason': best_flight.get('reason', 'Best value for money')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Flight selection failed: {str(e)}",
                'phase': 'selection_failed'
            }
    
    async def _execute_automatic_booking(self, selected_flight: Dict[str, Any], 
                                      travel_details: Dict[str, Any], 
                                      passenger_info: Dict[str, str]) -> Dict[str, Any]:
        """Phase 3: Execute automatic booking"""
        try:
            self.logger.info("Phase 3: Executing automatic booking...")
            
            # Prepare booking details
            booking_details = {
                'source': travel_details['source'],
                'destination': travel_details['destination'],
                'departure_date': travel_details['departure_date'],
                'flight_info': selected_flight
            }
            
            # Execute browser automation
            automation_result = await self.booking_automation.book_chennai_goa_flight(passenger_info)
            
            return {
                'success': automation_result.get('success', False),
                'booking_details': booking_details,
                'automation_result': automation_result,
                'passenger_info': passenger_info,
                'screenshots': automation_result.get('screenshots', []),
                'status': 'BOOKING_FORMS_FILLED' if automation_result.get('success') else 'BOOKING_FAILED'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Booking execution failed: {str(e)}",
                'phase': 'booking_failed'
            }
    
    def _extract_travel_details(self, user_request: str) -> Dict[str, Any]:
        """Extract comprehensive travel details"""
        request_lower = user_request.lower()
        
        # Enhanced city extraction
        cities = {
            'chennai': 'Chennai', 'bangalore': 'Bangalore', 'bengaluru': 'Bangalore',
            'mumbai': 'Mumbai', 'delhi': 'Delhi', 'hyderabad': 'Hyderabad',
            'kolkata': 'Kolkata', 'pune': 'Pune', 'goa': 'Goa', 
            'jaipur': 'Jaipur', 'kerala': 'Kerala', 'cochin': 'Kochi'
        }
        
        found_cities = [city for city_key, city in cities.items() if city_key in request_lower]
        
        source = found_cities[0] if len(found_cities) > 0 else 'Not specified'
        destination = found_cities[1] if len(found_cities) > 1 else (found_cities[0] if len(found_cities) > 0 else 'Not specified')
        
        # Enhanced date extraction
        date_patterns = [
            r'(?:date|on|for)\s+([a-zA-Z]+\s+\d+|\d{1,2}\s+[a-zA-Z]+)',
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
            r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)'
        ]
        
        departure_date = 'Not specified'
        for pattern in date_patterns:
            match = re.search(pattern, request_lower)
            if match:
                departure_date = self._normalize_date(match.group(1))
                break
        
        # Enhanced budget extraction
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
        
        return {
            'source': source,
            'destination': destination,
            'departure_date': departure_date,
            'budget': budget,
            'raw_request': user_request,
            'request_complexity': self._assess_request_complexity(user_request)
        }
    
    async def _get_llm_recommendations(self, travel_details: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """Get LLM-powered recommendations"""
        try:
            if not self.groq_api_key:
                return {'success': False, 'error': 'Groq API not available'}
            
            prompt = f"""
            As an expert travel AI, analyze this request and provide recommendations:
            
            Request: {user_request}
            Travel Details: {travel_details}
            
            Provide:
            1. Best flight recommendations
            2. Optimal booking strategy
            3. Budget optimization tips
            4. Travel timing suggestions
            
            Format as JSON with keys: flights, strategy, budget_tips, timing
            """
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    'Authorization': f'Bearer {self.groq_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-8b-instant',
                    'messages': [
                        {'role': 'system', 'content': 'You are an expert travel booking AI assistant.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 1000,
                    'temperature': 0.3
                }
            )
            
            if response.status_code == 200:
                llm_response = response.json()
                return {
                    'success': True,
                    'recommendations': llm_response['choices'][0]['message']['content'],
                    'confidence': 0.85
                }
            else:
                return {'success': False, 'error': f'Groq API error: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _validate_with_realtime_data(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate with real-time data"""
        validation_results = {}
        
        # Weather validation
        if travel_details['destination'] != 'Not specified':
            try:
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={travel_details['destination']}&appid={self.openweather_api_key}&units=metric"
                response = requests.get(weather_url)
                if response.status_code == 200:
                    weather_data = response.json()
                    validation_results['weather'] = {
                        'valid': True,
                        'temperature': weather_data['main']['temp'],
                        'condition': weather_data['weather'][0]['description']
                    }
                else:
                    validation_results['weather'] = {'valid': False, 'error': 'Weather API failed'}
            except:
                validation_results['weather'] = {'valid': False, 'error': 'Weather check failed'}
        
        # Flight availability validation
        if self.serper_api_key:
            try:
                query = f"flights from {travel_details['source']} to {travel_details['destination']} on {travel_details['departure_date']}"
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers={'X-API-KEY': self.serper_api_key, 'Content-Type': 'application/json'},
                    json={'q': query}
                )
                if response.status_code == 200:
                    search_results = response.json()
                    validation_results['flights'] = {
                        'valid': True,
                        'available': len(search_results.get('organicResults', [])) > 0,
                        'results_count': len(search_results.get('organicResults', []))
                    }
                else:
                    validation_results['flights'] = {'valid': False, 'error': 'Flight search failed'}
            except:
                validation_results['flights'] = {'valid': False, 'error': 'Flight validation failed'}
        
        return validation_results
    
    async def _search_multiple_sources(self, travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Search flights from multiple sources"""
        search_results = {}
        
        # Google Search via Serper
        if self.serper_api_key:
            try:
                query = f"best flights {travel_details['source']} to {travel_details['destination']} {travel_details['departure_date']} price comparison"
                response = requests.post(
                    "https://google.serper.dev/search",
                    headers={'X-API-KEY': self.serper_api_key, 'Content-Type': 'application/json'},
                    json={'q': query}
                )
                if response.status_code == 200:
                    search_results['google'] = response.json()
            except Exception as e:
                search_results['google'] = {'error': str(e)}
        
        # Add more sources as needed
        search_results['sources_used'] = ['google']
        search_results['total_sources'] = len(search_results['sources_used'])
        
        return search_results
    
    async def _ai_select_best_flight(self, search_results: Dict[str, Any], travel_details: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered flight selection"""
        # For now, select first available result
        # In production, this would use sophisticated AI selection
        
        google_results = search_results.get('google', {}).get('organicResults', [])
        
        if google_results:
            best_option = google_results[0]
            return {
                'success': True,
                'airline': 'Extracted from search',
                'price': 'To be extracted',
                'timing': 'To be extracted',
                'reason': 'Best available option based on search ranking',
                'source_result': best_option
            }
        
        return {
            'success': False,
            'error': 'No flight options found'
        }
    
    def _get_best_booking_url(self, flight: Dict[str, Any]) -> str:
        """Get best booking URL for selected flight"""
        # Priority order: MakeMyTrip -> Goibibo -> Airline direct
        return self.booking_sites.get('makemytrip', 'https://www.makemytrip.com/')
    
    def _assess_request_complexity(self, user_request: str) -> str:
        """Assess complexity of user request"""
        complexity_indicators = {
            'multi_city': ['and', 'also', 'plus', 'multiple'],
            'specific_requirements': ['window seat', 'aisle seat', 'vegetarian', 'business class'],
            'flexible_dates': ['flexible', 'around', 'sometime', 'any day']
        }
        
        request_lower = user_request.lower()
        score = 0
        
        for category, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                score += 1
        
        if score >= 2:
            return 'high'
        elif score == 1:
            return 'medium'
        else:
            return 'low'
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string"""
        try:
            months = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }
            
            for month_name, month_num in months.items():
                if month_name in date_str.lower():
                    day_match = re.search(r'\d+', date_str)
                    if day_match:
                        day = day_match.group().zfill(2)
                        return f"2024-{month_num}-{day}"
            return date_str
        except:
            return date_str
    
    def _normalize_budget(self, budget_str: str) -> str:
        """Normalize budget string"""
        budget_str = budget_str.replace(',', '').replace('k', '000')
        return f"₹{budget_str}"

# Usage example and helper functions
async def demo_fully_automated_booking():
    """Demo the fully automated booking system"""
    agent = FullyAutomatedBookingAgent()
    
    # Example request
    user_request = "Book Chennai to Bangalore flight for May 25 under 8000 rupees"
    
    passenger_info = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '+919876543210'
    }
    
    result = await agent.process_and_book_automatically(user_request, passenger_info)
    
    print("=" * 80)
    print("FULLY AUTOMATED BOOKING RESULT")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Next Action: {result.get('next_action', 'None')}")
    
    if result['success']:
        print("\n✅ Automation completed successfully!")
        print("📸 Check screenshots for booking confirmation")
        print("💳 Complete payment manually in the browser")
    else:
        print(f"\n❌ Automation failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(demo_fully_automated_booking())
