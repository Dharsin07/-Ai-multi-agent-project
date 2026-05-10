"""
Universal Ranking and Scoring Service for Travel Options

This service provides intelligent ranking and scoring for flights, hotels, and activities
based on multiple factors including price, ratings, convenience, and user preferences.
"""

from typing import Dict, Any, List, Optional
from utils.logger import logger
import re
from dataclasses import dataclass
from enum import Enum

class OptionType(Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"

@dataclass
class ScoreWeights:
    """Weights for different scoring factors"""
    price_weight: float = 0.4
    rating_weight: float = 0.3
    convenience_weight: float = 0.2
    preference_weight: float = 0.1

@dataclass
class RankedOption:
    """A ranked travel option with score and metadata"""
    option: Dict[str, Any]
    score: float
    breakdown: Dict[str, float]
    rank: int
    option_type: OptionType

class TravelRankingService:
    """Universal ranking service for travel options"""
    
    def __init__(self):
        self.logger = logger
        self.weights = ScoreWeights()
        self.logger.info("Travel Ranking Service initialized")
    
    def rank_flights(self, flights: List[Dict], budget: str = None, user_preferences: Dict = None) -> List[RankedOption]:
        """Rank flights by score"""
        self.logger.info(f"Ranking {len(flights)} flights")
        
        ranked_flights = []
        for flight in flights:
            score, breakdown = self._score_flight(flight, budget, user_preferences)
            ranked_flight = RankedOption(
                option=flight,
                score=score,
                breakdown=breakdown,
                rank=0,  # Will be assigned after sorting
                option_type=OptionType.FLIGHT
            )
            ranked_flights.append(ranked_flight)
        
        # Sort by score (descending) and assign ranks
        ranked_flights.sort(key=lambda x: x.score, reverse=True)
        for i, flight in enumerate(ranked_flights):
            flight.rank = i + 1
        
        self.logger.info(f"Ranked flights: top score {ranked_flights[0].score if ranked_flights else 0:.2f}")
        return ranked_flights
    
    def rank_hotels(self, hotels: List[Dict], budget: str = None, user_preferences: Dict = None) -> List[RankedOption]:
        """Rank hotels by score"""
        self.logger.info(f"Ranking {len(hotels)} hotels")
        
        ranked_hotels = []
        for hotel in hotels:
            score, breakdown = self._score_hotel(hotel, budget, user_preferences)
            ranked_hotel = RankedOption(
                option=hotel,
                score=score,
                breakdown=breakdown,
                rank=0,  # Will be assigned after sorting
                option_type=OptionType.HOTEL
            )
            ranked_hotels.append(ranked_hotel)
        
        # Sort by score (descending) and assign ranks
        ranked_hotels.sort(key=lambda x: x.score, reverse=True)
        for i, hotel in enumerate(ranked_hotels):
            hotel.rank = i + 1
        
        self.logger.info(f"Ranked hotels: top score {ranked_hotels[0].score if ranked_hotels else 0:.2f}")
        return ranked_hotels
    
    def rank_activities(self, activities: List[Dict], budget: str = None, user_preferences: Dict = None) -> List[RankedOption]:
        """Rank activities by score"""
        self.logger.info(f"Ranking {len(activities)} activities")
        
        ranked_activities = []
        for activity in activities:
            score, breakdown = self._score_activity(activity, budget, user_preferences)
            ranked_activity = RankedOption(
                option=activity,
                score=score,
                breakdown=breakdown,
                rank=0,  # Will be assigned after sorting
                option_type=OptionType.ACTIVITY
            )
            ranked_activities.append(ranked_activity)
        
        # Sort by score (descending) and assign ranks
        ranked_activities.sort(key=lambda x: x.score, reverse=True)
        for i, activity in enumerate(ranked_activities):
            activity.rank = i + 1
        
        self.logger.info(f"Ranked activities: top score {ranked_activities[0].score if ranked_activities else 0:.2f}")
        return ranked_activities
    
    def _score_flight(self, flight: Dict, budget: str = None, user_preferences: Dict = None) -> tuple[float, Dict[str, float]]:
        """Score a flight based on multiple factors"""
        breakdown = {}
        
        # Price score (lower is better)
        price_score = self._score_price(flight.get('price_estimate', ''), budget)
        breakdown['price'] = price_score * self.weights.price_weight
        
        # Rating score (higher is better)
        rating_score = self._score_flight_rating(flight)
        breakdown['rating'] = rating_score * self.weights.rating_weight
        
        # Convenience score (duration, direct flights)
        convenience_score = self._score_flight_convenience(flight)
        breakdown['convenience'] = convenience_score * self.weights.convenience_weight
        
        # Preference score (airline preferences, flight type)
        preference_score = self._score_flight_preferences(flight, user_preferences)
        breakdown['preference'] = preference_score * self.weights.preference_weight
        
        total_score = sum(breakdown.values())
        return total_score, breakdown
    
    def _score_hotel(self, hotel: Dict, budget: str = None, user_preferences: Dict = None) -> tuple[float, Dict[str, float]]:
        """Score a hotel based on multiple factors"""
        breakdown = {}
        
        # Price score (lower is better)
        price_score = self._score_price(hotel.get('price_per_night', ''), budget)
        breakdown['price'] = price_score * self.weights.price_weight
        
        # Rating score (higher is better)
        rating_score = self._score_hotel_rating(hotel)
        breakdown['rating'] = rating_score * self.weights.rating_weight
        
        # Convenience score (location, amenities)
        convenience_score = self._score_hotel_convenience(hotel)
        breakdown['convenience'] = convenience_score * self.weights.convenience_weight
        
        # Preference score (amenities, hotel type)
        preference_score = self._score_hotel_preferences(hotel, user_preferences)
        breakdown['preference'] = preference_score * self.weights.preference_weight
        
        total_score = sum(breakdown.values())
        return total_score, breakdown
    
    def _score_activity(self, activity: Dict, budget: str = None, user_preferences: Dict = None) -> tuple[float, Dict[str, float]]:
        """Score an activity based on multiple factors"""
        breakdown = {}
        
        # Price score (lower is better)
        price_score = self._score_price(activity.get('cost_estimate', ''), budget)
        breakdown['price'] = price_score * self.weights.price_weight
        
        # Rating score (higher is better)
        rating_score = self._score_activity_rating(activity)
        breakdown['rating'] = rating_score * self.weights.rating_weight
        
        # Convenience score (duration, timing)
        convenience_score = self._score_activity_convenience(activity)
        breakdown['convenience'] = convenience_score * self.weights.convenience_weight
        
        # Preference score (category, travel style)
        preference_score = self._score_activity_preferences(activity, user_preferences)
        breakdown['preference'] = preference_score * self.weights.preference_weight
        
        total_score = sum(breakdown.values())
        return total_score, breakdown
    
    def _score_price(self, price_str: str, budget: str = None) -> float:
        """Score price factor (0-1, higher is better)"""
        try:
            # Extract numeric price
            price_match = re.search(r'[\d,]+', price_str.replace('$', '').replace(',', ''))
            if not price_match:
                return 0.5  # Neutral score if price not found
            
            price = float(price_match.group())
            
            # If budget is available, score relative to budget
            if budget and budget != 'Not specified':
                budget_match = re.search(r'[\d,]+', budget.replace('$', '').replace(',', ''))
                if budget_match:
                    budget_amount = float(budget_match.group())
                    # Score based on percentage of budget (lower percentage = higher score)
                    price_ratio = price / budget_amount
                    if price_ratio <= 0.3:
                        return 1.0
                    elif price_ratio <= 0.5:
                        return 0.8
                    elif price_ratio <= 0.7:
                        return 0.6
                    elif price_ratio <= 0.9:
                        return 0.4
                    else:
                        return 0.2
            
            # Default scoring without budget
            if price <= 100:
                return 1.0
            elif price <= 300:
                return 0.8
            elif price <= 500:
                return 0.6
            elif price <= 1000:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            self.logger.warning(f"Error scoring price '{price_str}': {e}")
            return 0.5
    
    def _score_flight_rating(self, flight: Dict) -> float:
        """Score flight rating (0-1, higher is better)"""
        # For flights, we'll use a combination of airline reputation and flight type
        airline = flight.get('airline', '') or ''
        flight_type = flight.get('flight_type', '') or ''
        
        airline = airline.lower()
        flight_type = flight_type.lower()
        
        # Premium airlines get higher scores
        premium_airlines = ['emirates', 'qatar', 'singapore', 'lufthansa', 'air france', 'british airways']
        good_airlines = ['air india', 'indigo', 'spicejet', 'vistara', 'go first']
        
        if any(premium in airline for premium in premium_airlines):
            airline_score = 0.9
        elif any(good in airline for good in good_airlines):
            airline_score = 0.7
        else:
            airline_score = 0.5
        
        # Flight type scoring
        if flight_type == 'business':
            type_score = 1.0
        elif flight_type == 'premium economy':
            type_score = 0.8
        else:  # economy
            type_score = 0.6
        
        return (airline_score + type_score) / 2
    
    def _score_flight_convenience(self, flight: Dict) -> float:
        """Score flight convenience (0-1, higher is better)"""
        duration = flight.get('duration', '') or ''
        notes = flight.get('notes', '') or ''
        
        duration = duration.lower()
        notes = notes.lower()
        
        # Duration scoring
        duration_score = 0.5  # Default
        if 'h' in duration:
            try:
                hours_match = re.search(r'(\d+)h', duration)
                if hours_match:
                    hours = int(hours_match.group(1))
                    if hours <= 2:
                        duration_score = 1.0
                    elif hours <= 4:
                        duration_score = 0.8
                    elif hours <= 6:
                        duration_score = 0.6
                    else:
                        duration_score = 0.4
            except:
                pass
        
        # Direct flight bonus
        direct_bonus = 0.2 if 'direct' in notes else 0.0
        
        return min(1.0, duration_score + direct_bonus)
    
    def _score_flight_preferences(self, flight: Dict, user_preferences: Dict = None) -> float:
        """Score flight based on user preferences"""
        if not user_preferences:
            return 0.5  # Neutral score
        
        score = 0.5
        
        # Airline preference
        preferred_airlines = user_preferences.get('preferred_airlines', [])
        if preferred_airlines and flight.get('airline'):
            if any(airline.lower() in flight.get('airline', '').lower() for airline in preferred_airlines):
                score += 0.3
        
        # Flight type preference
        preferred_flight_type = user_preferences.get('flight_type')
        if preferred_flight_type and flight.get('flight_type'):
            if preferred_flight_type.lower() in flight.get('flight_type', '').lower():
                score += 0.2
        
        return min(1.0, score)
    
    def _score_hotel_rating(self, hotel: Dict) -> float:
        """Score hotel rating (0-1, higher is better)"""
        rating_str = hotel.get('rating', '') or ''
        rating_str = rating_str.lower()
        
        try:
            # Extract numeric rating
            rating_match = re.search(r'(\d+\.?\d*)', rating_str)
            if rating_match:
                rating = float(rating_match.group())
                # Normalize to 0-1 scale (assuming 1-5 scale)
                return rating / 5.0
        except:
            pass
        
        # Fallback based on keywords
        if '5 star' in rating_str or 'excellent' in rating_str:
            return 1.0
        elif '4 star' in rating_str or 'very good' in rating_str:
            return 0.8
        elif '3 star' in rating_str or 'good' in rating_str:
            return 0.6
        elif '2 star' in rating_str or 'fair' in rating_str:
            return 0.4
        else:
            return 0.5
    
    def _score_hotel_convenience(self, hotel: Dict) -> float:
        """Score hotel convenience (0-1, higher is better)"""
        amenities = hotel.get('amenities', [])
        if isinstance(amenities, str):
            amenities = [amenities]
        
        # Essential amenities
        essential_amenities = ['wifi', 'parking', 'restaurant', 'pool', 'gym', 'spa']
        amenity_score = 0.0
        
        for amenity in essential_amenities:
            if any(amenity.lower() in str(a).lower() for a in amenities):
                amenity_score += 0.15
        
        # Location convenience (if address is available)
        location_score = 0.3 if hotel.get('address') else 0.1
        
        return min(1.0, amenity_score + location_score)
    
    def _score_hotel_preferences(self, hotel: Dict, user_preferences: Dict = None) -> float:
        """Score hotel based on user preferences"""
        if not user_preferences:
            return 0.5  # Neutral score
        
        score = 0.5
        
        # Hotel type preference
        preferred_types = user_preferences.get('hotel_preferences', [])
        if preferred_types and hotel.get('hotel_type'):
            if any(hotel_type.lower() in hotel.get('hotel_type', '').lower() for hotel_type in preferred_types):
                score += 0.3
        
        # Amenity preferences
        preferred_amenities = user_preferences.get('amenity_preferences', [])
        if preferred_amenities and hotel.get('amenities'):
            hotel_amenities = [str(a).lower() for a in hotel.get('amenities', [])]
            for amenity in preferred_amenities:
                if any(amenity.lower() in hotel_amenity for hotel_amenity in hotel_amenities):
                    score += 0.1
        
        return min(1.0, score)
    
    def _score_activity_rating(self, activity: Dict) -> float:
        """Score activity rating (0-1, higher is better)"""
        rating_str = activity.get('rating', '') or ''
        rating_str = rating_str.lower()
        
        try:
            # Extract numeric rating
            rating_match = re.search(r'(\d+\.?\d*)', rating_str)
            if rating_match:
                rating = float(rating_match.group())
                # Normalize to 0-1 scale (assuming 1-5 scale)
                return rating / 5.0
        except:
            pass
        
        # Fallback based on keywords
        if '5 star' in rating_str or 'excellent' in rating_str:
            return 1.0
        elif '4 star' in rating_str or 'very good' in rating_str:
            return 0.8
        elif '3 star' in rating_str or 'good' in rating_str:
            return 0.6
        elif '2 star' in rating_str or 'fair' in rating_str:
            return 0.4
        else:
            return 0.5
    
    def _score_activity_convenience(self, activity: Dict) -> float:
        """Score activity convenience (0-1, higher is better)"""
        duration = activity.get('duration', '') or ''
        best_time = activity.get('best_time', '') or ''
        
        duration = duration.lower()
        best_time = best_time.lower()
        
        # Duration scoring (prefer moderate durations)
        duration_score = 0.5
        if 'hour' in duration:
            try:
                hours_match = re.search(r'(\d+)', duration)
                if hours_match:
                    hours = int(hours_match.group(1))
                    if 2 <= hours <= 4:  # Sweet spot
                        duration_score = 1.0
                    elif hours <= 6:
                        duration_score = 0.8
                    else:
                        duration_score = 0.4
            except:
                pass
        
        # Timing convenience
        time_score = 0.3 if best_time in ['morning', 'afternoon'] else 0.2
        
        return min(1.0, duration_score + time_score)
    
    def _score_activity_preferences(self, activity: Dict, user_preferences: Dict = None) -> float:
        """Score activity based on user preferences"""
        if not user_preferences:
            return 0.5  # Neutral score
        
        score = 0.5
        
        # Travel style matching
        travel_style = user_preferences.get('travel_style', '') or ''
        category = activity.get('category', '') or ''
        title = activity.get('title', '') or ''
        
        travel_style = travel_style.lower()
        category = category.lower()
        title = title.lower()
        
        style_keywords = {
            'luxury': ['premium', 'luxury', 'vip', 'exclusive', 'gourmet'],
            'budget': ['free', 'cheap', 'budget', 'local', 'street'],
            'adventure': ['adventure', 'thrill', 'extreme', 'outdoor', 'hiking'],
            'family': ['family', 'kids', 'children', 'fun', 'park'],
            'romantic': ['romantic', 'couples', 'sunset', 'dinner', 'intimate'],
            'cultural': ['cultural', 'museum', 'historical', 'heritage', 'traditional']
        }
        
        if travel_style in style_keywords:
            keywords = style_keywords[travel_style]
            if any(keyword in category or keyword in title for keyword in keywords):
                score += 0.3
        
        return min(1.0, score)
    
    def get_top_options(self, ranked_options: List[RankedOption], top_n: int = 5) -> List[Dict]:
        """Get top N ranked options as plain dictionaries"""
        top_ranked = ranked_options[:top_n]
        return [
            {
                **option.option,
                'ranking_score': round(option.score, 3),
                'ranking_breakdown': {k: round(v, 3) for k, v in option.breakdown.items()},
                'rank': option.rank
            }
            for option in top_ranked
        ]
    
    def filter_by_score_threshold(self, ranked_options: List[RankedOption], min_score: float = 0.5) -> List[RankedOption]:
        """Filter options by minimum score threshold"""
        filtered = [option for option in ranked_options if option.score >= min_score]
        self.logger.info(f"Filtered {len(ranked_options)} options to {len(filtered)} with score >= {min_score}")
        return filtered
