import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import logger

class TravelIntentExtractor:
    """Advanced travel intent extraction system for TRAVA AI"""
    
    def __init__(self):
        self.indian_cities = [
            'mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'kolkata', 
            'hyderabad', 'pune', 'jaipur', 'ahmedabad', 'goa', 'kochi', 'cochin',
            'lucknow', 'nagpur', 'indore', 'bhopal', 'chandigarh', 'amritsar'
        ]
        
        self.international_cities = [
            'dubai', 'london', 'paris', 'tokyo', 'new york', 'singapore', 
            'bangkok', 'hong kong', 'sydney', 'los angeles', 'barcelona', 'rome'
        ]
        
        self.budget_keywords = [
            'budget', 'cheap', 'affordable', 'economy', 'low cost', 'inexpensive',
            'luxury', 'premium', 'deluxe', '5-star', 'high-end', 'expensive',
            'mid-range', 'moderate', 'reasonable', 'standard'
        ]
        
        self.hotel_preferences = [
            '4-star', '5-star', 'luxury', 'boutique', 'resort', 'spa', 'pool',
            'gym', 'wifi', 'breakfast', 'pet-friendly', 'beach', 'city center',
            'airport', 'business', 'family', 'romantic', 'adults only'
        ]

    def extract_travel_intent(self, user_input: str) -> Dict:
        """
        Extract comprehensive travel intent from user message
        
        Args:
            user_input: Natural language travel request
            
        Returns:
            Structured travel intent dictionary
        """
        logger.info(f"Extracting travel intent from: {user_input}")
        
        intent = {
            'source_location': self._extract_source_location(user_input),
            'destination': self._extract_destination(user_input),
            'travel_dates': self._extract_travel_dates(user_input),
            'duration': self._extract_duration(user_input),
            'budget': self._extract_budget(user_input),
            'hotel_preferences': self._extract_hotel_preferences(user_input),
            'flight_type': self._extract_flight_type(user_input),
            'hotel_duration': self._extract_hotel_duration(user_input),
            'minimum_ratings': self._extract_minimum_ratings(user_input),
            'travel_style': self._extract_travel_style(user_input),
            'special_requirements': self._extract_special_requirements(user_input)
        }
        
        # Post-processing and validation
        intent = self._validate_and_enhance_intent(intent, user_input)
        
        logger.info(f"Extracted intent: {json.dumps(intent, indent=2)}")
        return intent

    def _extract_destination(self, text: str) -> Optional[str]:
        """Extract destination from user input"""
        text_lower = text.lower()
        
        # Enhanced destination patterns
        patterns = [
            # "to [destination]" pattern
            r'\b(?:to|in|for|visit)\s+([a-z\s]+?)(?:\s+(?:for|from|on|in|at|$|trip|travel|vacation|holiday))',
            # "travel to [destination]" pattern
            r'\btravel\s+(?:to|for|in)\s+([a-z\s]+?)(?:\s+(?:for|from|on|in|at|$))',
            # "trip to [destination]" pattern
            r'\btrip\s+(?:to|for|in)\s+([a-z\s]+?)(?:\s+(?:for|from|on|in|at|$))',
            # "vacation in [destination]" pattern
            r'\bvacation\s+(?:to|for|in)\s+([a-z\s]+?)(?:\s+(?:for|from|on|in|at|$))',
            # "going to [destination]" pattern
            r'\bgoing\s+(?:to|for|in)\s+([a-z\s]+?)(?:\s+(?:for|from|on|in|at|$))'
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_dest = match.group(1).strip()
                if len(potential_dest) > 2 and potential_dest not in ['trip', 'travel', 'vacation', 'holiday', 'weekend']:
                    # Check if this matches any known city
                    if potential_dest in self.international_cities:
                        return potential_dest.title()
                    elif potential_dest in self.indian_cities:
                        return potential_dest.title()
        
        # If no pattern found, check all cities in text
        # Check international cities first (more likely to be destination)
        for city in self.international_cities:
            if city in text_lower:
                return city.title()
        
        # Then check Indian cities
        for city in self.indian_cities:
            if city in text_lower:
                return city.title()
        
        return None

    def _extract_source_location(self, text: str) -> Optional[str]:
        """Extract source location from user input"""
        text_lower = text.lower()
        
        # Enhanced source patterns
        patterns = [
            # "from [location]" pattern
            r'\bfrom\s+([a-z\s]+?)(?:\s+(?:to|for|on|in|at|$))',
            # "travel from [location]" pattern
            r'\btravel\s+from\s+([a-z\s]+?)(?:\s+(?:to|for|on|in|at|$))',
            # "trip from [location]" pattern
            r'\btrip\s+from\s+([a-z\s]+?)(?:\s+(?:to|for|on|in|at|$))',
            # "leaving from [location]" pattern
            r'\bleaving\s+from\s+([a-z\s]+?)(?:\s+(?:to|for|on|in|at|$))'
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_source = match.group(1).strip()
                if len(potential_source) > 2:
                    return potential_source.title()
        
        return None

    def _extract_travel_dates(self, text: str) -> Dict[str, Optional[str]]:
        """Extract travel dates from user input"""
        dates = {'departure_date': None, 'return_date': None}
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY/MM/DD
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}',  # Month DD, YYYY
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?',  # Month DD
        ]
        
        found_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            found_dates.extend(matches)
        
        if len(found_dates) >= 2:
            dates['departure_date'] = found_dates[0]
            dates['return_date'] = found_dates[1]
        elif len(found_dates) == 1:
            dates['departure_date'] = found_dates[0]
        
        # Relative date patterns
        if not dates['departure_date']:
            if 'next week' in text.lower():
                next_week = datetime.now() + timedelta(days=7)
                dates['departure_date'] = next_week.strftime('%Y-%m-%d')
            elif 'this weekend' in text.lower():
                saturday = datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
                dates['departure_date'] = saturday.strftime('%Y-%m-%d')
            elif 'tomorrow' in text.lower():
                tomorrow = datetime.now() + timedelta(days=1)
                dates['departure_date'] = tomorrow.strftime('%Y-%m-%d')
        
        return dates

    def _extract_duration(self, text: str) -> str:
        """Extract trip duration from user input"""
        text_lower = text.lower()
        
        # Numeric duration patterns
        duration_patterns = [
            r'(\d+)\s+days?',      # 3 days, 7 day
            r'(\d+)\s+nights?',    # 3 nights, 7 night
            r'(\d+)\s+weeks?',     # 2 weeks, 1 week
            r'weekend',            # weekend (2 days)
            r'long weekend',       # long weekend (3 days)
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern == r'weekend':
                    return '2 days'
                elif pattern == r'long weekend':
                    return '3 days'
                elif 'week' in pattern:
                    days = int(match.group(1)) * 7
                    return f'{days} days'
                else:
                    unit = 'nights' if 'night' in pattern else 'days'
                    return f"{match.group(1)} {unit}"
        
        return '3 days'  # Default

    def _extract_budget(self, text: str) -> Dict[str, Optional[str]]:
        """Extract budget information from user input"""
        budget_info = {'amount': None, 'currency': 'USD', 'type': None}
        
        # Currency patterns
        currency_patterns = [
            (r'[$]\s*(\d{1,6}(?:,\d{3})*)', 'USD'),
            (r'₹\s*(\d{1,6}(?:,\d{3})*)', 'INR'),
            (r'€\s*(\d{1,6}(?:,\d{3})*)', 'EUR'),
            (r'£\s*(\d{1,6}(?:,\d{3})*)', 'GBP'),
            (r'(\d{1,6}(?:,\d{3})*)\s*USD', 'USD'),
            (r'(\d{1,6}(?:,\d{3})*)\s*INR', 'INR'),
            (r'(\d{1,6}(?:,\d{3})*)\s*rupees?', 'INR'),
            (r'(\d{1,6}(?:,\d{3})*)\s*Rs\.?', 'INR'),
        ]
        
        for pattern, currency in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                budget_info['amount'] = amount
                budget_info['currency'] = currency
                break
        
        # Budget type keywords
        for keyword in self.budget_keywords:
            if keyword in text.lower():
                if keyword in ['budget', 'cheap', 'affordable', 'economy', 'low cost', 'inexpensive']:
                    budget_info['type'] = 'budget'
                elif keyword in ['luxury', 'premium', 'deluxe', '5-star', 'high-end', 'expensive']:
                    budget_info['type'] = 'luxury'
                else:
                    budget_info['type'] = 'mid-range'
                break
        
        return budget_info

    def _extract_hotel_preferences(self, text: str) -> List[str]:
        """Extract hotel preferences from user input"""
        preferences = []
        text_lower = text.lower()
        
        for preference in self.hotel_preferences:
            if preference in text_lower:
                preferences.append(preference)
        
        return preferences

    def _extract_flight_type(self, text: str) -> str:
        """Extract flight type preference"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['direct', 'non-stop']):
            return 'direct'
        elif any(word in text_lower for word in ['business class', 'business']):
            return 'business'
        elif any(word in text_lower for word in ['first class', 'first']):
            return 'first'
        elif any(word in text_lower for word in ['economy', 'budget']):
            return 'economy'
        else:
            return 'economy'  # Default

    def _extract_hotel_duration(self, text: str) -> str:
        """Extract hotel stay duration"""
        return self._extract_duration(text)

    def _extract_minimum_ratings(self, text: str) -> Optional[float]:
        """Extract minimum hotel rating requirement"""
        text_lower = text.lower()
        
        rating_patterns = [
            r'(\d+\.?\d*)\s*stars?',
            r'minimum\s+(\d+\.?\d*)',
            r'at least\s+(\d+\.?\d*)\s*stars?',
            r'(\d+)\s*star\s+or\s+above',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    rating = float(match.group(1))
                    return min(rating, 5.0)  # Cap at 5 stars
                except ValueError:
                    continue
        
        return None

    def _extract_travel_style(self, text: str) -> str:
        """Extract travel style preference"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['luxury', 'premium', 'deluxe']):
            return 'luxury'
        elif any(word in text_lower for word in ['budget', 'cheap', 'affordable']):
            return 'budget'
        elif any(word in text_lower for word in ['family', 'kids', 'children']):
            return 'family'
        elif any(word in text_lower for word in ['romantic', 'couple', 'honeymoon']):
            return 'romantic'
        elif any(word in text_lower for word in ['adventure', 'thrill', 'extreme']):
            return 'adventure'
        elif any(word in text_lower for word in ['business', 'work', 'conference']):
            return 'business'
        else:
            return 'leisure'

    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special travel requirements"""
        requirements = []
        text_lower = text.lower()
        
        special_keywords = {
            'wheelchair accessible': 'wheelchair_accessible',
            'pet friendly': 'pet_friendly',
            'all inclusive': 'all_inclusive',
            'free cancellation': 'free_cancellation',
            'breakfast included': 'breakfast_included',
            'airport transfer': 'airport_transfer',
            'wifi included': 'wifi_included',
            'parking included': 'parking_included',
        }
        
        for keyword, requirement in special_keywords.items():
            if keyword in text_lower:
                requirements.append(requirement)
        
        return requirements

    def _validate_and_enhance_intent(self, intent: Dict, original_text: str) -> Dict:
        """Validate and enhance extracted intent"""
        
        # Set defaults for missing critical fields
        if not intent['destination']:
            # Try to extract destination one more time with broader patterns
            words = original_text.split()
            for word in words:
                if len(word) > 3 and word.lower() not in ['trip', 'travel', 'vacation', 'holiday']:
                    intent['destination'] = word.title()
                    break
        
        # Enhance budget with defaults based on travel style
        if not intent['budget']['amount'] and intent['travel_style']:
            if intent['travel_style'] == 'luxury':
                intent['budget']['amount'] = '5000'
                intent['budget']['currency'] = 'USD'
            elif intent['travel_style'] == 'budget':
                intent['budget']['amount'] = '1000'
                intent['budget']['currency'] = 'USD'
            else:
                intent['budget']['amount'] = '2500'
                intent['budget']['currency'] = 'USD'
        
        # Set minimum rating based on travel style
        if not intent['minimum_ratings']:
            if intent['travel_style'] == 'luxury':
                intent['minimum_ratings'] = 4.5
            elif intent['travel_style'] == 'budget':
                intent['minimum_ratings'] = 3.0
            else:
                intent['minimum_ratings'] = 4.0
        
        return intent
