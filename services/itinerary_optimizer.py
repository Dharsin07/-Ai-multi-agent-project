"""
Itinerary Optimization Layer for Multi-Agent Travel System

This service converts ranked flights, hotels, and activities into a complete day-wise travel plan.
It uses ONLY top-ranked results from the ranking system and builds realistic, optimized itineraries.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import re
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

class TimeSlot(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"

@dataclass
class ActivitySchedule:
    activity: Dict[str, Any]
    day: int
    time_slot: TimeSlot
    reasoning: str

@dataclass
class DayPlan:
    day: int
    theme: str
    time_slots: Dict[TimeSlot, List[Dict[str, Any]]]
    hotel: Dict[str, Any]
    reasoning: str
    estimated_cost: float

class ItineraryOptimizer:
    """Optimizes ranked travel components into complete day-wise itineraries"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Itinerary Optimizer initialized")
        
        # Activity categories for logical grouping
        self.activity_categories = {
            'outdoor': ['park', 'garden', 'beach', 'hiking', 'nature', 'adventure'],
            'cultural': ['museum', 'historical', 'heritage', 'temple', 'church', 'art gallery'],
            'entertainment': ['cinema', 'theater', 'concert', 'show', 'nightlife'],
            'shopping': ['mall', 'market', 'shopping', 'boutique'],
            'dining': ['restaurant', 'cafe', 'food', 'dining', 'cuisine'],
            'relaxation': ['spa', 'wellness', 'massage', 'relax', 'rest']
        }
        
        # Location keywords for proximity grouping
        self.location_keywords = {
            'downtown': ['downtown', 'city center', 'central', 'main street'],
            'waterfront': ['beach', 'harbor', 'marina', 'waterfront', 'river'],
            'historical': ['old town', 'heritage', 'historical', 'ancient'],
            'modern': ['modern', 'new', 'contemporary', 'skyline']
        }
    
    def optimize_itinerary(self, 
                          ranked_flights: List[Dict], 
                          ranked_hotels: List[Dict], 
                          ranked_activities: List[Dict],
                          budget: str,
                          duration: str,
                          destination: str) -> Dict[str, Any]:
        """
        Main optimization function that creates complete itinerary from ranked options
        """
        self.logger.info(f"Starting itinerary optimization for {duration} trip to {destination}")
        
        try:
            # Parse duration and budget
            num_days = self._parse_duration(duration)
            budget_amount = self._parse_budget(budget)
            
            # Select best options
            selected_flight = self._select_best_flight(ranked_flights)
            selected_hotel = self._select_best_hotel(ranked_hotels, budget_amount, num_days)
            
            # Create day-wise plan
            day_plans = self._create_day_plans(
                ranked_activities, 
                num_days, 
                destination, 
                selected_flight
            )
            
            # Validate and optimize budget
            optimized_plans, total_cost = self._validate_and_optimize_budget(
                day_plans, 
                selected_flight, 
                selected_hotel, 
                budget_amount
            )
            
            # Build final structured output
            final_itinerary = self._build_final_itinerary(
                optimized_plans,
                selected_flight,
                selected_hotel,
                total_cost,
                budget_amount,
                destination,
                duration
            )
            
            self.logger.info(f"Itinerary optimization completed. Total cost: ${total_cost:.2f}")
            return final_itinerary
            
        except Exception as e:
            self.logger.error(f"Error in itinerary optimization: {e}")
            return self._get_error_itinerary(destination, duration, budget, str(e))
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to number of days"""
        try:
            # Extract number from duration string
            match = re.search(r'(\d+)', duration.lower())
            if match:
                days = int(match.group(1))
                return max(1, min(days, 14))  # Limit to reasonable range
            return 3  # Default to 3 days
        except:
            return 3
    
    def _parse_budget(self, budget: str) -> float:
        """Parse budget string to numeric amount"""
        try:
            # Extract numeric budget
            match = re.search(r'[\d,]+', budget.replace('$', '').replace(',', ''))
            if match:
                return float(match.group())
            return 2000.0  # Default budget
        except:
            return 2000.0
    
    def _select_best_flight(self, ranked_flights: List[Dict]) -> Dict[str, Any]:
        """Select the best flight from ranked options"""
        if not ranked_flights:
            return self._create_fallback_flight()
        
        # Select top-ranked flight
        best_flight = ranked_flights[0]
        self.logger.info(f"Selected flight: {best_flight.get('airline', 'Unknown')}")
        return best_flight
    
    def _select_best_hotel(self, ranked_hotels: List[Dict], budget: float, num_days: int) -> Dict[str, Any]:
        """Select best hotel considering budget and duration"""
        if not ranked_hotels:
            return self._create_fallback_hotel()
        
        # Calculate total hotel cost and check budget fit
        affordable_hotels = []
        for hotel in ranked_hotels:
            price_per_night = self._parse_price(hotel.get('price_per_night', '0'))
            total_hotel_cost = price_per_night * num_days
            
            # Check if hotel fits budget (leave room for activities)
            if total_hotel_cost <= budget * 0.4:  # Max 40% of budget for hotel
                hotel['total_cost'] = total_hotel_cost
                affordable_hotels.append(hotel)
        
        # Select best affordable hotel, or fallback to top-ranked
        if affordable_hotels:
            selected_hotel = affordable_hotels[0]
        else:
            selected_hotel = ranked_hotels[0]
            price_per_night = self._parse_price(selected_hotel.get('price_per_night', '0'))
            selected_hotel['total_cost'] = price_per_night * num_days
        
        self.logger.info(f"Selected hotel: {selected_hotel.get('name', 'Unknown')}")
        return selected_hotel
    
    def _create_day_plans(self, ranked_activities: List[Dict], num_days: int, 
                         destination: str, flight: Dict[str, Any]) -> List[DayPlan]:
        """Create structured day plans with logical activity grouping"""
        day_plans = []
        
        # Group activities by category and location
        grouped_activities = self._group_activities_by_proximity(ranked_activities)
        
        for day in range(1, num_days + 1):
            # Determine day theme based on available activities
            day_theme = self._determine_day_theme(day, num_days, grouped_activities, flight)
            
            # Allocate activities to time slots
            time_slots = self._allocate_activities_to_slots(
                grouped_activities, 
                day, 
                num_days,
                flight
            )
            
            # Generate reasoning for the day
            reasoning = self._generate_day_reasoning(day, day_theme, time_slots, num_days)
            
            # Calculate estimated cost for the day
            day_cost = self._calculate_day_cost(time_slots)
            
            day_plan = DayPlan(
                day=day,
                theme=day_theme,
                time_slots=time_slots,
                hotel={},  # Will be set consistently across all days
                reasoning=reasoning,
                estimated_cost=day_cost
            )
            
            day_plans.append(day_plan)
        
        return day_plans
    
    def _group_activities_by_proximity(self, activities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group activities by location and category for logical scheduling"""
        grouped = {
            'outdoor': [],
            'cultural': [],
            'entertainment': [],
            'shopping': [],
            'dining': [],
            'relaxation': [],
            'other': []
        }
        
        for activity in activities:
            category = self._categorize_activity(activity)
            grouped[category].append(activity)
        
        return grouped
    
    def _categorize_activity(self, activity: Dict) -> str:
        """Categorize activity based on title and description"""
        text = f"{activity.get('title', '')} {activity.get('description', '')}".lower()
        
        for category, keywords in self.activity_categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'other'
    
    def _determine_day_theme(self, day: int, num_days: int, 
                           grouped_activities: Dict[str, List[Dict]], 
                           flight: Dict) -> str:
        """Determine theme for each day based on trip structure"""
        
        # Day 1: Arrival and orientation
        if day == 1:
            return "Arrival & City Orientation"
        
        # Last day: Departure preparation
        if day == num_days:
            return "Final Exploration & Departure Prep"
        
        # Middle days: Based on available activities
        available_categories = [cat for cat, activities in grouped_activities.items() if activities]
        
        if 'outdoor' in available_categories and day % 2 == 1:
            return "Outdoor Adventure & Nature"
        elif 'cultural' in available_categories:
            return "Cultural Heritage & History"
        elif 'entertainment' in available_categories:
            return "Entertainment & Local Life"
        elif 'shopping' in available_categories:
            return "Shopping & Local Markets"
        else:
            return "City Exploration & Discovery"
    
    def _allocate_activities_to_slots(self, grouped_activities: Dict[str, List[Dict]], 
                                    day: int, num_days: int, flight: Dict) -> Dict[TimeSlot, List[Dict]]:
        """Allocate activities to morning, afternoon, and evening slots"""
        time_slots = {
            TimeSlot.MORNING: [],
            TimeSlot.AFTERNOON: [],
            TimeSlot.EVENING: []
        }
        
        # Day 1 special handling - arrival day
        if day == 1:
            time_slots[TimeSlot.MORNING].append(self._create_arrival_activity(flight))
            # Add one light activity for afternoon
            available = self._get_available_activities(grouped_activities, 1)
            if available:
                time_slots[TimeSlot.AFTERNOON].append(available[0])
            # Evening: rest and dinner
            time_slots[TimeSlot.EVENING].append(self._create_dinner_activity())
            return time_slots
        
        # Last day special handling - departure day
        if day == num_days:
            # Morning: one final activity
            available = self._get_available_activities(grouped_activities, 1)
            if available:
                time_slots[TimeSlot.MORNING].append(available[0])
            # Afternoon: departure prep
            time_slots[TimeSlot.AFTERNOON].append(self._create_departure_activity(flight))
            return time_slots
        
        # Regular days - fill with 2-3 activities
        available_activities = self._get_available_activities(grouped_activities, 3)
        
        if len(available_activities) >= 2:
            time_slots[TimeSlot.MORNING].append(available_activities[0])
            time_slots[TimeSlot.AFTERNOON].append(available_activities[1])
            
            if len(available_activities) >= 3:
                time_slots[TimeSlot.EVENING].append(available_activities[2])
            else:
                time_slots[TimeSlot.EVENING].append(self._create_dinner_activity())
        else:
            # Fallback if not enough activities
            time_slots[TimeSlot.MORNING].append(self._create_generic_activity("Morning Exploration"))
            time_slots[TimeSlot.AFTERNOON].append(self._create_generic_activity("Afternoon Discovery"))
            time_slots[TimeSlot.EVENING].append(self._create_dinner_activity())
        
        return time_slots
    
    def _get_available_activities(self, grouped_activities: Dict[str, List[Dict]], 
                                max_count: int) -> List[Dict]:
        """Get available activities from grouped pools"""
        available = []
        
        # Collect activities from all categories
        for category, activities in grouped_activities.items():
            available.extend(activities)
        
        # Shuffle for variety and return requested count
        random.shuffle(available)
        return available[:max_count]
    
    def _create_arrival_activity(self, flight: Dict) -> Dict:
        """Create arrival activity for first day"""
        return {
            'title': 'Airport Arrival & Transfer',
            'description': f"Arrive via {flight.get('airline', 'flight')} and transfer to hotel",
            'cost_estimate': '$50',
            'location': 'Airport to Hotel',
            'time': 'Morning',
            'type': 'logistics'
        }
    
    def _create_departure_activity(self, flight: Dict) -> Dict:
        """Create departure activity for last day"""
        return {
            'title': 'Hotel Check-out & Airport Transfer',
            'description': f"Check-out and transfer to airport for {flight.get('airline', 'flight')} departure",
            'cost_estimate': '$50',
            'location': 'Hotel to Airport',
            'time': 'Afternoon',
            'type': 'logistics'
        }
    
    def _create_dinner_activity(self) -> Dict:
        """Create dinner activity"""
        return {
            'title': 'Local Dinner Experience',
            'description': 'Enjoy local cuisine at a recommended restaurant',
            'cost_estimate': '$40',
            'location': 'Local Restaurant',
            'time': 'Evening',
            'type': 'dining'
        }
    
    def _create_generic_activity(self, title: str) -> Dict:
        """Create generic exploration activity"""
        return {
            'title': title,
            'description': 'Explore local attractions and points of interest',
            'cost_estimate': '$30',
            'location': 'City Center',
            'time': 'Flexible',
            'type': 'exploration'
        }
    
    def _generate_day_reasoning(self, day: int, theme: str, 
                              time_slots: Dict[TimeSlot, List[Dict]], 
                              num_days: int) -> str:
        """Generate reasoning for day's schedule"""
        if day == 1:
            return "First day focuses on smooth arrival, hotel check-in, and gentle introduction to the destination."
        elif day == num_days:
            return "Final day includes one last activity and departure preparation to ensure stress-free exit."
        else:
            activities_count = sum(len(activities) for activities in time_slots.values())
            return f"Day {day} features {theme} with {activities_count} activities balanced across time slots for optimal experience."
    
    def _calculate_day_cost(self, time_slots: Dict[TimeSlot, List[Dict]]) -> float:
        """Calculate estimated cost for all activities in a day"""
        total = 0.0
        for activities in time_slots.values():
            for activity in activities:
                cost = self._parse_price(activity.get('cost_estimate', '0'))
                total += cost
        return total
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to numeric value"""
        try:
            match = re.search(r'[\d,]+', price_str.replace('$', '').replace(',', ''))
            if match:
                return float(match.group())
        except:
            pass
        return 0.0
    
    def _validate_and_optimize_budget(self, day_plans: List[DayPlan], 
                                    flight: Dict, hotel: Dict, 
                                    budget: float) -> Tuple[List[DayPlan], float]:
        """Validate total cost against budget and optimize if needed"""
        
        # Calculate total cost
        flight_cost = self._parse_price(flight.get('price_estimate', '0'))
        hotel_cost = hotel.get('total_cost', self._parse_price(hotel.get('price_per_night', '0')) * len(day_plans))
        activities_cost = sum(plan.estimated_cost for plan in day_plans)
        
        total_cost = flight_cost + hotel_cost + activities_cost
        
        self.logger.info(f"Initial total cost: ${total_cost:.2f} (Budget: ${budget:.2f})")
        
        # If within budget, return as-is
        if total_cost <= budget:
            return day_plans, total_cost
        
        # If over budget, optimize by reducing activities
        optimization_needed = total_cost - budget
        self.logger.info(f"Budget exceeded by ${optimization_needed:.2f}, optimizing...")
        
        optimized_plans = self._reduce_activities_cost(day_plans, optimization_needed)
        
        # Recalculate total
        new_activities_cost = sum(plan.estimated_cost for plan in optimized_plans)
        new_total = flight_cost + hotel_cost + new_activities_cost
        
        return optimized_plans, new_total
    
    def _reduce_activities_cost(self, day_plans: List[DayPlan], amount_to_reduce: float) -> List[DayPlan]:
        """Reduce activity costs by removing/downgrading activities"""
        optimized_plans = []
        amount_reduced = 0.0
        
        for plan in day_plans:
            optimized_plan = DayPlan(
                day=plan.day,
                theme=plan.theme,
                time_slots=plan.time_slots.copy(),
                hotel=plan.hotel,
                reasoning=plan.reasoning,
                estimated_cost=plan.estimated_cost
            )
            
            # Try to remove evening activities first (least essential)
            if amount_reduced < amount_to_reduce and optimized_plan.time_slots[TimeSlot.EVENING]:
                removed_activity = optimized_plan.time_slots[TimeSlot.EVENING].pop()
                cost_saved = self._parse_price(removed_activity.get('cost_estimate', '0'))
                amount_reduced += cost_saved
                optimized_plan.estimated_cost -= cost_saved
                
                # Replace with cheaper dinner
                optimized_plan.time_slots[TimeSlot.EVENING].append({
                    'title': 'Simple Local Dinner',
                    'description': 'Budget-friendly local dining option',
                    'cost_estimate': '$20',
                    'location': 'Local Eatery',
                    'time': 'Evening',
                    'type': 'dining'
                })
                optimized_plan.estimated_cost += 20.0
                amount_reduced -= 20.0
            
            # If still need to reduce more, remove afternoon activities
            if amount_reduced < amount_to_reduce and optimized_plan.time_slots[TimeSlot.AFTERNOON]:
                removed_activity = optimized_plan.time_slots[TimeSlot.AFTERNOON].pop()
                cost_saved = self._parse_price(removed_activity.get('cost_estimate', '0'))
                amount_reduced += cost_saved
                optimized_plan.estimated_cost -= cost_saved
            
            optimized_plans.append(optimized_plan)
        
        return optimized_plans
    
    def _build_final_itinerary(self, day_plans: List[DayPlan], flight: Dict, 
                             hotel: Dict, total_cost: float, budget: float,
                             destination: str, duration: str) -> Dict[str, Any]:
        """Build final structured JSON itinerary"""
        
        # Set hotel consistently across all days
        for plan in day_plans:
            plan.hotel = hotel
        
        # Convert day plans to JSON format
        itinerary_days = []
        for plan in day_plans:
            day_data = {
                'day': plan.day,
                'theme': plan.theme,
                'reasoning': plan.reasoning,
                'time_slots': {
                    slot.value: [
                        {
                            'title': activity['title'],
                            'description': activity['description'],
                            'cost_estimate': activity['cost_estimate'],
                            'location': activity['location'],
                            'type': activity.get('type', 'activity')
                        }
                        for activity in activities
                    ]
                    for slot, activities in plan.time_slots.items()
                },
                'estimated_cost': f"${plan.estimated_cost:.2f}"
            }
            itinerary_days.append(day_data)
        
        # Build budget summary
        flight_cost = self._parse_price(flight.get('price_estimate', '0'))
        hotel_cost = hotel.get('total_cost', 0)
        activities_cost = total_cost - flight_cost - hotel_cost
        
        budget_summary = {
            'total_estimated_cost': f"${total_cost:.2f}",
            'flights_cost': f"${flight_cost:.2f}",
            'accommodation_cost': f"${hotel_cost:.2f}",
            'activities_food_cost': f"${activities_cost:.2f}",
            'is_within_budget': total_cost <= budget,
            'budget_remaining': f"${max(0, budget - total_cost):.2f}",
            'optimization_applied': total_cost > budget
        }
        
        return {
            'destination': destination,
            'duration': duration,
            'selected_flight': {
                **flight,
                'selection_reason': 'Top-ranked option from ranking system'
            },
            'selected_hotel': {
                **hotel,
                'selection_reason': 'Best value option within budget constraints'
            },
            'itinerary': itinerary_days,
            'budget_summary': budget_summary,
            'optimization_summary': {
                'total_days': len(day_plans),
                'total_activities': sum(
                    sum(len(activities) for activities in plan.time_slots.values())
                    for plan in day_plans
                ),
                'average_daily_cost': f"${total_cost / len(day_plans):.2f}",
                'budget_utilization': f"{(total_cost / budget * 100):.1f}%"
            }
        }
    
    def _create_fallback_flight(self) -> Dict[str, Any]:
        """Create fallback flight when no flights available"""
        return {
            'airline': 'Major Airline',
            'price_estimate': '$500',
            'duration': '3 hours',
            'notes': 'Standard economy flight',
            'selection_reason': 'Fallback option - no flights available'
        }
    
    def _create_fallback_hotel(self) -> Dict[str, Any]:
        """Create fallback hotel when no hotels available"""
        return {
            'name': 'Standard Hotel',
            'price_per_night': '$100',
            'rating': '3 stars',
            'amenities': ['WiFi', 'Breakfast'],
            'selection_reason': 'Fallback option - no hotels available'
        }
    
    def _get_error_itinerary(self, destination: str, duration: str, 
                           budget: str, error: str) -> Dict[str, Any]:
        """Get error response when optimization fails"""
        return {
            'destination': destination,
            'duration': duration,
            'selected_flight': self._create_fallback_flight(),
            'selected_hotel': self._create_fallback_hotel(),
            'itinerary': [],
            'budget_summary': {
                'total_estimated_cost': 'Error',
                'flights_cost': 'N/A',
                'accommodation_cost': 'N/A',
                'activities_food_cost': 'N/A',
                'is_within_budget': False,
                'error': error
            },
            'optimization_summary': {
                'error': error,
                'status': 'failed'
            }
        }
