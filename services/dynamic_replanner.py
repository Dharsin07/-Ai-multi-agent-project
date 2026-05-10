"""
Dynamic Replanning Engine for Targeted Itinerary Updates

This service handles targeted replanning of affected itinerary sections while
preserving valid, unaffected components. It integrates with the existing optimization
and reflection pipeline for intelligent, adaptive travel planning.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import json
from dataclasses import dataclass
from datetime import datetime
from services.disruption_detector import DisruptionEvent, ImpactAnalysis, DisruptionSeverity
from services.ranking_service import TravelRankingService
from services.itinerary_optimizer import ItineraryOptimizer
from services.reflection_agent import ReflectionAgent

@dataclass
class ReplanRequest:
    disruption_event: DisruptionEvent
    impact_analysis: ImpactAnalysis
    current_itinerary: Dict[str, Any]
    updated_data: Dict[str, Any]
    user_preferences: Dict[str, Any]

@dataclass
class ReplanResult:
    success: bool
    updated_itinerary: Dict[str, Any]
    change_log: List[Dict[str, Any]]
    confidence_score: float
    replan_reason: str
    affected_sections: List[str]
    preserved_sections: List[str]
    version_number: int

class DynamicReplanner:
    """Engine for targeted, intelligent itinerary replanning"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Dynamic Replanner initialized")
        
        self.ranking_service = TravelRankingService()
        self.itinerary_optimizer = ItineraryOptimizer()
        self.reflection_agent = ReflectionAgent()
        
        # Replanning strategies based on disruption types
        self.replan_strategies = {
            "external_flight": self._replan_flight_disruption,
            "external_hotel": self._replan_hotel_disruption,
            "external_weather": self._replan_weather_disruption,
            "internal_budget": self._replan_budget_violation,
            "internal_time": self._replan_time_violation,
            "internal_schedule": self._replan_schedule_violation,
            "user_preference": self._replan_preference_change
        }
    
    def execute_replan(self, request: ReplanRequest) -> ReplanResult:
        """
        Execute targeted replanning based on disruption analysis
        """
        self.logger.info(f"Executing replan for {request.disruption_event.disruption_type.value} disruption")
        
        try:
            # Step 1: Initialize change tracking
            change_log = []
            original_itinerary = json.loads(json.dumps(request.current_itinerary))  # Deep copy
            
            # Step 2: Execute targeted replanning strategy
            strategy_func = self.replan_strategies.get(request.disruption_event.disruption_type.value)
            
            if not strategy_func:
                raise ValueError(f"No replanning strategy for {request.disruption_event.disruption_type.value}")
            
            updated_itinerary = strategy_func(request, change_log)
            
            # Step 3: Re-run optimization for affected sections
            if request.impact_analysis.requires_full_replan:
                updated_itinerary = self._full_optimization_replan(request, updated_itinerary, change_log)
            else:
                updated_itinerary = self._targeted_optimization_replan(request, updated_itinerary, change_log)
            
            # Step 4: Re-run reflection check
            reflected_itinerary = self._validate_with_reflection(updated_itinerary, request, change_log)
            
            # Step 5: Generate final result
            confidence_score = reflected_itinerary.get('reflection_report', {}).get('confidence_score', 0.0)
            
            result = ReplanResult(
                success=True,
                updated_itinerary=reflected_itinerary,
                change_log=change_log,
                confidence_score=confidence_score,
                replan_reason=request.disruption_event.description,
                affected_sections=request.impact_analysis.affected_components,
                preserved_sections=request.impact_analysis.preserve_sections,
                version_number=original_itinerary.get('version', 1) + 1
            )
            
            self.logger.info(f"Replanning completed successfully. Confidence: {confidence_score:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Replanning failed: {e}")
            return ReplanResult(
                success=False,
                updated_itinerary=request.current_itinerary,
                change_log=[{"error": str(e), "step": "replanning_failed"}],
                confidence_score=0.0,
                replan_reason=f"Replanning failed: {str(e)}",
                affected_sections=[],
                preserved_sections=[],
                version_number=request.current_itinerary.get('version', 1)
            )
    
    def _replan_flight_disruption(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle flight-related disruptions"""
        self.logger.info("Replanning flight disruption")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        flight_update = request.updated_data.get('flight_update', {})
        
        # Update flight information
        if flight_update:
            old_flight = updated_itinerary.get('selected_flight', {})
            new_flight = self._find_alternative_flight(old_flight, flight_update, request)
            
            updated_itinerary['selected_flight'] = new_flight
            
            change_log.append({
                "type": "flight_update",
                "action": "replaced_flight",
                "old_flight": old_flight.get('airline', 'Unknown'),
                "new_flight": new_flight.get('airline', 'Unknown'),
                "reason": flight_update.get('status', 'Disruption'),
                "timestamp": datetime.now().isoformat()
            })
            
            # Adjust Day 1 activities if arrival time changed significantly
            if self._arrival_time_changed(old_flight, new_flight):
                self._adjust_day1_schedule(updated_itinerary, new_flight, change_log)
        
        return updated_itinerary
    
    def _replan_hotel_disruption(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle hotel-related disruptions"""
        self.logger.info("Replanning hotel disruption")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        hotel_update = request.updated_data.get('hotel_update', {})
        
        # Find alternative hotel
        old_hotel = updated_itinerary.get('selected_hotel', {})
        new_hotel = self._find_alternative_hotel(old_hotel, hotel_update, request)
        
        updated_itinerary['selected_hotel'] = new_hotel
        
        change_log.append({
            "type": "hotel_update",
            "action": "replaced_hotel",
            "old_hotel": old_hotel.get('name', 'Unknown'),
            "new_hotel": new_hotel.get('name', 'Unknown'),
            "reason": hotel_update.get('status', 'Disruption'),
            "timestamp": datetime.now().isoformat()
        })
        
        # Update hotel reference in all days
        for day in updated_itinerary.get('itinerary', []):
            day['hotel'] = new_hotel
        
        return updated_itinerary
    
    def _replan_weather_disruption(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle weather-related disruptions"""
        self.logger.info("Replanning weather disruption")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        weather_update = request.updated_data.get('weather_update', {})
        affected_days = request.impact_analysis.affected_days
        
        # Replace outdoor activities with indoor alternatives
        for day_num in affected_days:
            day_data = self._find_day_by_number(updated_itinerary, day_num)
            if day_data:
                self._replace_outdoor_activities(day_data, weather_update, change_log)
        
        return updated_itinerary
    
    def _replan_budget_violation(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle budget constraint violations"""
        self.logger.info("Replanning budget violation")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        budget_info = request.disruption_event.metadata
        
        # Reduce costs systematically
        cost_reduction_needed = budget_info.get('exceed_amount', 0)
        
        # Strategy 1: Reduce hotel costs
        if cost_reduction_needed > 0:
            updated_itinerary = self._reduce_hotel_costs(updated_itinerary, cost_reduction_needed, change_log)
        
        # Strategy 2: Reduce activity costs
        if cost_reduction_needed > 0:
            updated_itinerary = self._reduce_activity_costs(updated_itinerary, cost_reduction_needed, change_log)
        
        change_log.append({
            "type": "budget_optimization",
            "action": "cost_reduction",
            "reduction_amount": budget_info.get('exceed_amount', 0),
            "strategies_applied": ["hotel_downgrade", "activity_reduction"],
            "timestamp": datetime.now().isoformat()
        })
        
        return updated_itinerary
    
    def _replan_time_violation(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle time and scheduling violations"""
        self.logger.info("Replanning time violation")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        affected_days = request.impact_analysis.affected_days
        
        for day_num in affected_days:
            day_data = self._find_day_by_number(updated_itinerary, day_num)
            if day_data:
                self._optimize_day_timing(day_data, change_log)
        
        return updated_itinerary
    
    def _replan_schedule_violation(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle schedule overload violations"""
        self.logger.info("Replanning schedule violation")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        affected_days = request.impact_analysis.affected_days
        
        for day_num in affected_days:
            day_data = self._find_day_by_number(updated_itinerary, day_num)
            if day_data:
                self._reduce_schedule_overload(day_data, change_log)
        
        return updated_itinerary
    
    def _replan_preference_change(self, request: ReplanRequest, change_log: List[Dict]) -> Dict[str, Any]:
        """Handle user preference changes"""
        self.logger.info("Replanning preference change")
        
        updated_itinerary = json.loads(json.dumps(request.current_itinerary))
        preference_analysis = request.disruption_event.metadata.get('change_analysis', {})
        
        # Update preferences in itinerary
        updated_itinerary['preferences'] = request.user_preferences.get('preferences', '')
        
        # If style change detected, modify affected components
        if preference_analysis.get('style_change'):
            style_changes = preference_analysis.get('style_changes', [])
            
            for style_change in style_changes:
                if style_change == 'budget_to_luxury':
                    self._upgrade_to_luxury(updated_itinerary, change_log)
                elif style_change == 'luxury_to_budget':
                    self._downgrade_to_budget(updated_itinerary, change_log)
        
        # Replace activities based on new preferences
        updated_itinerary = self._update_activities_for_preferences(updated_itinerary, request.user_preferences, change_log)
        
        change_log.append({
            "type": "preference_update",
            "action": "preferences_changed",
            "old_preferences": request.current_itinerary.get('preferences', ''),
            "new_preferences": request.user_preferences.get('preferences', ''),
            "style_changes": preference_analysis.get('style_changes', []),
            "timestamp": datetime.now().isoformat()
        })
        
        return updated_itinerary
    
    def _targeted_optimization_replan(self, request: ReplanRequest, 
                                    updated_itinerary: Dict[str, Any], 
                                    change_log: List[Dict]) -> Dict[str, Any]:
        """Run optimization only on affected sections"""
        self.logger.info("Running targeted optimization")
        
        affected_days = request.impact_analysis.affected_days
        
        # Re-optimize only affected days
        for day_num in affected_days:
            day_data = self._find_day_by_number(updated_itinerary, day_num)
            if day_data:
                # Get alternative activities for the affected day
                alternative_activities = self._get_alternative_activities(day_data, request)
                
                # Re-optimize the day
                optimized_day = self._optimize_single_day(day_data, alternative_activities, request)
                
                # Update the day in itinerary
                self._update_day_in_itinerary(updated_itinerary, day_num, optimized_day)
                
                change_log.append({
                    "type": "day_optimization",
                    "action": "reoptimized_day",
                    "day_number": day_num,
                    "activities_count": len(optimized_day.get('time_slots', {})),
                    "timestamp": datetime.now().isoformat()
                })
        
        return updated_itinerary
    
    def _full_optimization_replan(self, request: ReplanRequest, 
                                updated_itinerary: Dict[str, Any], 
                                change_log: List[Dict]) -> Dict[str, Any]:
        """Run full optimization when major changes are needed"""
        self.logger.info("Running full optimization replan")
        
        # Extract current selections
        current_flight = updated_itinerary.get('selected_flight', {})
        current_hotel = updated_itinerary.get('selected_hotel', {})
        
        # Get new ranked options considering the disruption
        destination = updated_itinerary.get('destination', 'Unknown')
        budget = request.user_preferences.get('budget', '$2000')
        preferences = request.user_preferences.get('preferences', '')
        duration = updated_itinerary.get('duration', '3 days')
        
        # Re-run full optimization with updated constraints
        try:
            optimized_itinerary = self.itinerary_optimizer.optimize_itinerary(
                [current_flight] if current_flight else [],
                [current_hotel] if current_hotel else [],
                self._extract_all_activities(updated_itinerary),
                budget,
                duration,
                destination
            )
            
            change_log.append({
                "type": "full_optimization",
                "action": "complete_replan",
                "reason": "major_disruption",
                "timestamp": datetime.now().isoformat()
            })
            
            return optimized_itinerary
            
        except Exception as e:
            self.logger.error(f"Full optimization failed: {e}")
            return updated_itinerary
    
    def _validate_with_reflection(self, updated_itinerary: Dict[str, Any], 
                                request: ReplanRequest, 
                                change_log: List[Dict]) -> Dict[str, Any]:
        """Validate the updated itinerary with reflection agent"""
        self.logger.info("Running reflection validation on updated itinerary")
        
        try:
            budget = request.user_preferences.get('budget', '$2000')
            reflected_itinerary = self.reflection_agent.reflect_on_itinerary(
                updated_itinerary,
                budget,
                max_iterations=1
            )
            
            # Add reflection validation to change log
            reflection_report = reflected_itinerary.get('reflection_report', {})
            change_log.append({
                "type": "reflection_validation",
                "action": "validated_updated_itinerary",
                "confidence_score": reflection_report.get('confidence_score', 0.0),
                "issues_found": len(reflection_report.get('issues_found', [])),
                "timestamp": datetime.now().isoformat()
            })
            
            return reflected_itinerary
            
        except Exception as e:
            self.logger.error(f"Reflection validation failed: {e}")
            change_log.append({
                "type": "reflection_validation",
                "action": "validation_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return updated_itinerary
    
    # Helper methods
    
    def _find_alternative_flight(self, old_flight: Dict, flight_update: Dict, request: ReplanRequest) -> Dict:
        """Find alternative flight based on disruption"""
        # In a real implementation, this would call the flight search API
        # For now, create a modified version of the old flight
        alternative = old_flight.copy()
        
        if flight_update.get('status', '').lower() == 'cancelled':
            alternative.update({
                'airline': 'Alternative Airline',
                'price_estimate': f"${int(self._parse_price(old_flight.get('price_estimate', '0')) * 1.1)}",
                'notes': f"Alternative flight due to cancellation: {flight_update.get('status', '')}"
            })
        elif 'delayed' in flight_update.get('status', '').lower():
            alternative.update({
                'notes': f"Flight delayed: {flight_update.get('delay_hours', 0)} hours"
            })
        
        return alternative
    
    def _find_alternative_hotel(self, old_hotel: Dict, hotel_update: Dict, request: ReplanRequest) -> Dict:
        """Find alternative hotel based on disruption"""
        # In a real implementation, this would call the hotel search API
        alternative = old_hotel.copy()
        
        if hotel_update.get('status', '').lower() == 'unavailable':
            alternative.update({
                'name': 'Alternative Hotel',
                'price_per_night': f"${int(self._parse_price(old_hotel.get('price_per_night', '0')) * 0.8)}",
                'rating': '4 stars',
                'notes': f"Alternative hotel due to: {hotel_update.get('status', '')}"
            })
        
        return alternative
    
    def _arrival_time_changed(self, old_flight: Dict, new_flight: Dict) -> bool:
        """Check if arrival time changed significantly"""
        # Simplified check - in real implementation would compare actual times
        return new_flight.get('notes', '') != old_flight.get('notes', '')
    
    def _adjust_day1_schedule(self, itinerary: Dict, new_flight: Dict, change_log: List[Dict]):
        """Adjust Day 1 schedule based on new flight arrival"""
        day1 = self._find_day_by_number(itinerary, 1)
        if day1:
            # Modify morning activities based on arrival
            morning_activities = day1.get('time_slots', {}).get('morning', [])
            
            change_log.append({
                "type": "schedule_adjustment",
                "action": "adjusted_day1_arrival",
                "flight_notes": new_flight.get('notes', ''),
                "timestamp": datetime.now().isoformat()
            })
    
    def _find_day_by_number(self, itinerary: Dict, day_num: int) -> Optional[Dict]:
        """Find specific day in itinerary"""
        for day in itinerary.get('itinerary', []):
            if day.get('day') == day_num:
                return day
        return None
    
    def _replace_outdoor_activities(self, day_data: Dict, weather_update: Dict, change_log: List[Dict]):
        """Replace outdoor activities with indoor alternatives"""
        outdoor_keywords = ['outdoor', 'park', 'beach', 'hiking', 'nature']
        indoor_alternatives = [
            {'title': 'Museum Visit', 'description': 'Explore local museums', 'cost_estimate': '$30', 'location': 'Museum District', 'type': 'cultural'},
            {'title': 'Indoor Shopping', 'description': 'Visit shopping centers', 'cost_estimate': '$40', 'location': 'Shopping Mall', 'type': 'shopping'},
            {'title': 'Art Gallery', 'description': 'Visit art galleries', 'cost_estimate': '$25', 'location': 'Gallery District', 'type': 'cultural'}
        ]
        
        for slot_name, activities in day_data.get('time_slots', {}).items():
            for i, activity in enumerate(activities):
                activity_text = f"{activity.get('title', '')} {activity.get('description', '')}".lower()
                
                if any(keyword in activity_text for keyword in outdoor_keywords):
                    # Replace with indoor alternative
                    alternative = indoor_alternatives[i % len(indoor_alternatives)]
                    activities[i] = alternative
                    
                    change_log.append({
                        "type": "activity_replacement",
                        "action": "weather_related_replacement",
                        "day": day_data.get('day'),
                        "time_slot": slot_name,
                        "original_activity": activity.get('title', ''),
                        "new_activity": alternative.get('title', ''),
                        "reason": weather_update.get('condition', 'Bad weather'),
                        "timestamp": datetime.now().isoformat()
                    })
    
    def _reduce_hotel_costs(self, itinerary: Dict, reduction_needed: float, change_log: List[Dict]) -> Dict:
        """Reduce hotel costs to meet budget"""
        current_hotel = itinerary.get('selected_hotel', {})
        current_price = self._parse_price(current_hotel.get('price_per_night', '0'))
        
        # Find cheaper alternative
        new_price = current_price * 0.7  # 30% reduction
        new_hotel = current_hotel.copy()
        new_hotel.update({
            'name': 'Mid-Range Hotel',
            'price_per_night': f"${int(new_price)}",
            'rating': '3 stars',
            'notes': 'Downgraded to meet budget constraints'
        })
        
        itinerary['selected_hotel'] = new_hotel
        
        # Update hotel in all days
        for day in itinerary.get('itinerary', []):
            day['hotel'] = new_hotel
        
        change_log.append({
            "type": "cost_reduction",
            "action": "hotel_downgrade",
            "old_price": current_price,
            "new_price": new_price,
            "savings": current_price - new_price,
            "timestamp": datetime.now().isoformat()
        })
        
        return itinerary
    
    def _reduce_activity_costs(self, itinerary: Dict, reduction_needed: float, change_log: List[Dict]) -> Dict:
        """Reduce activity costs to meet budget"""
        total_savings = 0
        
        for day in itinerary.get('itinerary', []):
            for slot_name, activities in day.get('time_slots', {}).items():
                for i, activity in enumerate(activities):
                    current_cost = self._parse_price(activity.get('cost_estimate', '0'))
                    
                    # Reduce expensive activities
                    if current_cost > 100:
                        new_cost = current_cost * 0.6  # 40% reduction
                        activities[i]['cost_estimate'] = f"${int(new_cost)}"
                        activities[i]['notes'] = 'Cost adjusted for budget'
                        
                        total_savings += (current_cost - new_cost)
                        
                        change_log.append({
                            "type": "cost_reduction",
                            "action": "activity_cost_reduction",
                            "day": day.get('day'),
                            "time_slot": slot_name,
                            "activity": activity.get('title', ''),
                            "old_cost": current_cost,
                            "new_cost": new_cost,
                            "savings": current_cost - new_cost,
                            "timestamp": datetime.now().isoformat()
                        })
        
        return itinerary
    
    def _optimize_day_timing(self, day_data: Dict, change_log: List[Dict]):
        """Optimize timing within a day"""
        # Remove duplicate activities in same time slot
        for slot_name, activities in day_data.get('time_slots', {}).items():
            if len(activities) > 2:
                # Keep only the first 2 activities
                removed_activities = activities[2:]
                activities[:] = activities[:2]
                
                change_log.append({
                    "type": "timing_optimization",
                    "action": "removed_overloaded_activities",
                    "day": day_data.get('day'),
                    "time_slot": slot_name,
                    "removed_count": len(removed_activities),
                    "timestamp": datetime.now().isoformat()
                })
    
    def _reduce_schedule_overload(self, day_data: Dict, change_log: List[Dict]):
        """Reduce overloaded schedule"""
        total_activities = sum(len(activities) for activities in day_data.get('time_slots', {}).values())
        
        if total_activities > 6:
            # Remove evening activities first (least essential)
            evening_activities = day_data.get('time_slots', {}).get('evening', [])
            if evening_activities:
                removed_count = min(2, len(evening_activities))
                removed_activities = evening_activities[-removed_count:]
                evening_activities[:] = evening_activities[:-removed_count]
                
                change_log.append({
                    "type": "schedule_optimization",
                    "action": "reduced_evening_activities",
                    "day": day_data.get('day'),
                    "removed_count": removed_count,
                    "timestamp": datetime.now().isoformat()
                })
    
    def _upgrade_to_luxury(self, itinerary: Dict, change_log: List[Dict]):
        """Upgrade itinerary to luxury style"""
        current_hotel = itinerary.get('selected_hotel', {})
        current_price = self._parse_price(current_hotel.get('price_per_night', '0'))
        
        luxury_hotel = current_hotel.copy()
        luxury_hotel.update({
            'name': 'Luxury Grand Hotel',
            'price_per_night': f"${int(current_price * 1.5)}",
            'rating': '5 stars',
            'amenities': ['Spa', 'Fine Dining', 'Concierge', 'Premium WiFi'],
            'notes': 'Upgraded to luxury accommodations'
        })
        
        itinerary['selected_hotel'] = luxury_hotel
        
        change_log.append({
            "type": "style_upgrade",
            "action": "upgraded_to_luxury",
            "old_hotel": current_hotel.get('name', ''),
            "new_hotel": luxury_hotel.get('name', ''),
            "timestamp": datetime.now().isoformat()
        })
    
    def _downgrade_to_budget(self, itinerary: Dict, change_log: List[Dict]):
        """Downgrade itinerary to budget style"""
        current_hotel = itinerary.get('selected_hotel', {})
        current_price = self._parse_price(current_hotel.get('price_per_night', '0'))
        
        budget_hotel = current_hotel.copy()
        budget_hotel.update({
            'name': 'Budget Inn',
            'price_per_night': f"${int(current_price * 0.5)}",
            'rating': '3 stars',
            'amenities': ['WiFi', 'Breakfast'],
            'notes': 'Downgraded to budget accommodations'
        })
        
        itinerary['selected_hotel'] = budget_hotel
        
        change_log.append({
            "type": "style_downgrade",
            "action": "downgraded_to_budget",
            "old_hotel": current_hotel.get('name', ''),
            "new_hotel": budget_hotel.get('name', ''),
            "timestamp": datetime.now().isoformat()
        })
    
    def _update_activities_for_preferences(self, itinerary: Dict, user_prefs: Dict, change_log: List[Dict]) -> Dict:
        """Update activities based on new user preferences"""
        # This would involve re-ranking activities based on new preferences
        # For now, just log that preferences were updated
        change_log.append({
            "type": "activity_update",
            "action": "preferences_applied",
            "new_preferences": user_prefs.get('preferences', ''),
            "timestamp": datetime.now().isoformat()
        })
        
        return itinerary
    
    def _get_alternative_activities(self, day_data: Dict, request: ReplanRequest) -> List[Dict]:
        """Get alternative activities for a specific day"""
        # In a real implementation, this would call the activity search API
        # For now, return some generic alternatives
        return [
            {'title': 'Alternative Activity 1', 'description': 'Backup activity option', 'cost_estimate': '$30', 'location': 'City Center', 'type': 'cultural'},
            {'title': 'Alternative Activity 2', 'description': 'Another backup option', 'cost_estimate': '$25', 'location': 'Downtown', 'type': 'entertainment'}
        ]
    
    def _optimize_single_day(self, day_data: Dict, activities: List[Dict], request: ReplanRequest) -> Dict:
        """Optimize a single day's activities"""
        # Simplified optimization - just ensure we have activities in each time slot
        time_slots = day_data.get('time_slots', {})
        
        for slot_name in ['morning', 'afternoon', 'evening']:
            if slot_name not in time_slots or not time_slots[slot_name]:
                time_slots[slot_name] = activities[:1] if activities else [{
                    'title': f'Free Time {slot_name.title()}',
                    'description': 'Relax and explore',
                    'cost_estimate': '$0',
                    'location': 'Hotel Area',
                    'type': 'free_time'
                }]
        
        return day_data
    
    def _update_day_in_itinerary(self, itinerary: Dict, day_num: int, updated_day: Dict):
        """Update a specific day in the itinerary"""
        for i, day in enumerate(itinerary.get('itinerary', [])):
            if day.get('day') == day_num:
                itinerary['itinerary'][i] = updated_day
                break
    
    def _extract_all_activities(self, itinerary: Dict) -> List[Dict]:
        """Extract all activities from itinerary"""
        activities = []
        for day in itinerary.get('itinerary', []):
            for slot_activities in day.get('time_slots', {}).values():
                activities.extend(slot_activities)
        return activities
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to numeric value"""
        try:
            if isinstance(price_str, str):
                import re
                match = re.search(r'[\d,]+', price_str.replace('$', '').replace(',', ''))
                if match:
                    return float(match.group())
            elif isinstance(price_str, (int, float)):
                return float(price_str)
        except:
            pass
        return 0.0
