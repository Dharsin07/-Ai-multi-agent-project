"""
Disruption Detection System for Dynamic Travel Replanning

This service monitors for various disruption triggers that require itinerary replanning,
including external disruptions, internal constraint violations, and user preference updates.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import re
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

class DisruptionType(Enum):
    EXTERNAL_FLIGHT = "external_flight"
    EXTERNAL_HOTEL = "external_hotel"
    EXTERNAL_WEATHER = "external_weather"
    INTERNAL_BUDGET = "internal_budget"
    INTERNAL_TIME = "internal_time"
    INTERNAL_SCHEDULE = "internal_schedule"
    USER_PREFERENCE = "user_preference"

class DisruptionSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DisruptionEvent:
    disruption_type: DisruptionType
    severity: DisruptionSeverity
    description: str
    affected_components: List[str]  # ["flight", "hotel", "day_1", "day_2", etc.]
    trigger_source: str  # "external_api", "internal_validation", "user_input"
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ImpactAnalysis:
    affected_days: List[int]
    affected_components: List[str]
    requires_full_replan: bool
    preserve_sections: List[str]
    estimated_replan_time: str  # "quick", "moderate", "extensive"

class DisruptionDetector:
    """Detects and analyzes various types of disruptions requiring replanning"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Disruption Detector initialized")
        
        # Disruption patterns and keywords
        self.flight_disruption_patterns = [
            "delayed", "cancelled", "missed connection", "schedule change",
            "flight unavailable", "booking failed", "price increased"
        ]
        
        self.hotel_disruption_patterns = [
            "unavailable", "fully booked", "booking failed", "price increased",
            "hotel closed", "maintenance", "overbooking"
        ]
        
        self.weather_disruption_patterns = [
            "severe weather", "storm", "hurricane", "heavy rain", "snow",
            "extreme heat", "weather advisory", "flight cancelled due to weather"
        ]
        
        # Budget violation thresholds
        self.budget_violation_thresholds = {
            "minor_exceed": 0.05,  # 5% over budget
            "moderate_exceed": 0.15,  # 15% over budget
            "major_exceed": 0.25   # 25% over budget
        }
        
        # Schedule violation patterns
        self.schedule_violation_patterns = [
            "overloaded", "unrealistic timing", "travel time insufficient",
            "too many activities", "conflicting times", "back-to-back activities"
        ]
    
    def detect_disruptions(self, current_itinerary: Dict[str, Any], 
                          new_data: Dict[str, Any] = None,
                          user_preferences: Dict[str, Any] = None) -> List[DisruptionEvent]:
        """
        Detect all types of disruptions in the current itinerary
        """
        disruptions = []
        
        # Detect external disruptions
        if new_data:
            disruptions.extend(self._detect_external_disruptions(current_itinerary, new_data))
        
        # Detect internal constraint violations
        disruptions.extend(self._detect_internal_violations(current_itinerary))
        
        # Detect user preference changes
        if user_preferences:
            disruptions.extend(self._detect_preference_changes(current_itinerary, user_preferences))
        
        self.logger.info(f"Detected {len(disruptions)} disruptions requiring attention")
        return disruptions
    
    def _detect_external_disruptions(self, current_itinerary: Dict[str, Any], 
                                   new_data: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect external disruptions like flight delays, hotel issues, weather"""
        disruptions = []
        
        # Flight disruptions
        flight_disruptions = self._detect_flight_disruptions(current_itinerary, new_data)
        disruptions.extend(flight_disruptions)
        
        # Hotel disruptions
        hotel_disruptions = self._detect_hotel_disruptions(current_itinerary, new_data)
        disruptions.extend(hotel_disruptions)
        
        # Weather disruptions
        weather_disruptions = self._detect_weather_disruptions(current_itinerary, new_data)
        disruptions.extend(weather_disruptions)
        
        return disruptions
    
    def _detect_flight_disruptions(self, current_itinerary: Dict[str, Any], 
                                 new_data: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect flight-related disruptions"""
        disruptions = []
        
        current_flight = current_itinerary.get('selected_flight', {})
        new_flight_info = new_data.get('flight_update', {})
        
        if new_flight_info:
            # Check for delay or cancellation
            status = new_flight_info.get('status', '').lower()
            if any(pattern in status for pattern in self.flight_disruption_patterns):
                severity = self._classify_flight_disruption_severity(status, new_flight_info)
                
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.EXTERNAL_FLIGHT,
                    severity=severity,
                    description=f"Flight disruption: {status}",
                    affected_components=["flight", "day_1", "departure_day"],
                    trigger_source="external_api",
                    timestamp=datetime.now(),
                    metadata={
                        "original_flight": current_flight,
                        "updated_info": new_flight_info,
                        "disruption_reason": status
                    }
                ))
            
            # Check for significant price increase
            current_price = self._parse_price(current_flight.get('price_estimate', '0'))
            new_price = self._parse_price(new_flight_info.get('price', '0'))
            
            if new_price > current_price * 1.2:  # 20% price increase
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.EXTERNAL_FLIGHT,
                    severity=DisruptionSeverity.MEDIUM,
                    description=f"Flight price increased by {((new_price/current_price-1)*100):.1f}%",
                    affected_components=["flight", "budget"],
                    trigger_source="external_api",
                    timestamp=datetime.now(),
                    metadata={
                        "original_price": current_price,
                        "new_price": new_price,
                        "price_increase_percentage": ((new_price/current_price-1)*100)
                    }
                ))
        
        return disruptions
    
    def _detect_hotel_disruptions(self, current_itinerary: Dict[str, Any], 
                                new_data: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect hotel-related disruptions"""
        disruptions = []
        
        current_hotel = current_itinerary.get('selected_hotel', {})
        new_hotel_info = new_data.get('hotel_update', {})
        
        if new_hotel_info:
            # Check for unavailability
            status = new_hotel_info.get('status', '').lower()
            if any(pattern in status for pattern in self.hotel_disruption_patterns):
                severity = DisruptionSeverity.HIGH if "unavailable" in status else DisruptionSeverity.MEDIUM
                
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.EXTERNAL_HOTEL,
                    severity=severity,
                    description=f"Hotel disruption: {status}",
                    affected_components=["hotel"] + [f"day_{i}" for i in range(1, len(current_itinerary.get('itinerary', [])) + 1)],
                    trigger_source="external_api",
                    timestamp=datetime.now(),
                    metadata={
                        "original_hotel": current_hotel,
                        "updated_info": new_hotel_info,
                        "disruption_reason": status
                    }
                ))
            
            # Check for significant price increase
            current_price = self._parse_price(current_hotel.get('price_per_night', '0'))
            new_price = self._parse_price(new_hotel_info.get('price_per_night', '0'))
            
            if new_price > current_price * 1.25:  # 25% price increase
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.EXTERNAL_HOTEL,
                    severity=DisruptionSeverity.MEDIUM,
                    description=f"Hotel price increased by {((new_price/current_price-1)*100):.1f}%",
                    affected_components=["hotel", "budget"],
                    trigger_source="external_api",
                    timestamp=datetime.now(),
                    metadata={
                        "original_price": current_price,
                        "new_price": new_price,
                        "price_increase_percentage": ((new_price/current_price-1)*100)
                    }
                ))
        
        return disruptions
    
    def _detect_weather_disruptions(self, current_itinerary: Dict[str, Any], 
                                  new_data: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect weather-related disruptions"""
        disruptions = []
        
        weather_update = new_data.get('weather_update', {})
        
        if weather_update:
            weather_condition = weather_update.get('condition', '').lower()
            severity_level = weather_update.get('severity', '').lower()
            
            if any(pattern in weather_condition for pattern in self.weather_disruption_patterns):
                severity = self._classify_weather_severity(severity_level, weather_condition)
                
                # Identify affected activities
                affected_days = self._find_weather_affected_days(current_itinerary, weather_condition)
                
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.EXTERNAL_WEATHER,
                    severity=severity,
                    description=f"Weather disruption: {weather_condition}",
                    affected_components=[f"day_{day}" for day in affected_days],
                    trigger_source="external_api",
                    timestamp=datetime.now(),
                    metadata={
                        "weather_condition": weather_condition,
                        "severity_level": severity_level,
                        "affected_days": affected_days,
                        "weather_details": weather_update
                    }
                ))
        
        return disruptions
    
    def _detect_internal_violations(self, current_itinerary: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect internal constraint violations"""
        disruptions = []
        
        # Budget violations
        budget_disruptions = self._detect_budget_violations(current_itinerary)
        disruptions.extend(budget_disruptions)
        
        # Time and schedule violations
        schedule_disruptions = self._detect_schedule_violations(current_itinerary)
        disruptions.extend(schedule_disruptions)
        
        # Travel time inconsistencies
        travel_time_disruptions = self._detect_travel_time_violations(current_itinerary)
        disruptions.extend(travel_time_disruptions)
        
        return disruptions
    
    def _detect_budget_violations(self, current_itinerary: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect budget constraint violations"""
        disruptions = []
        
        budget_summary = current_itinerary.get('budget_summary', {})
        total_cost_str = budget_summary.get('total_estimated_cost', '0')
        total_cost = self._parse_price(total_cost_str)
        
        # Get original budget from metadata or use a default
        original_budget = self._parse_price(current_itinerary.get('original_budget', '$2000'))
        
        if total_cost > original_budget:
            exceed_percentage = (total_cost - original_budget) / original_budget
            
            if exceed_percentage >= self.budget_violation_thresholds["major_exceed"]:
                severity = DisruptionSeverity.HIGH
            elif exceed_percentage >= self.budget_violation_thresholds["moderate_exceed"]:
                severity = DisruptionSeverity.MEDIUM
            else:
                severity = DisruptionSeverity.LOW
            
            disruptions.append(DisruptionEvent(
                disruption_type=DisruptionType.INTERNAL_BUDGET,
                severity=severity,
                description=f"Budget exceeded by {exceed_percentage*100:.1f}%",
                affected_components=["budget", "activities", "hotel"],
                trigger_source="internal_validation",
                timestamp=datetime.now(),
                metadata={
                    "total_cost": total_cost,
                    "original_budget": original_budget,
                    "exceed_amount": total_cost - original_budget,
                    "exceed_percentage": exceed_percentage * 100
                }
            ))
        
        return disruptions
    
    def _detect_schedule_violations(self, current_itinerary: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect schedule and timing violations"""
        disruptions = []
        
        itinerary = current_itinerary.get('itinerary', [])
        
        for day in itinerary:
            day_num = day.get('day', 0)
            time_slots = day.get('time_slots', {})
            
            # Check for overloaded time slots
            for slot_name, activities in time_slots.items():
                if len(activities) > 2:
                    disruptions.append(DisruptionEvent(
                        disruption_type=DisruptionType.INTERNAL_SCHEDULE,
                        severity=DisruptionSeverity.MEDIUM,
                        description=f"Day {day_num} {slot_name} has {len(activities)} activities (overloaded)",
                        affected_components=[f"day_{day_num}"],
                        trigger_source="internal_validation",
                        timestamp=datetime.now(),
                        metadata={
                            "day": day_num,
                            "time_slot": slot_name,
                            "activity_count": len(activities),
                            "activities": [a.get('title', '') for a in activities]
                        }
                    ))
            
            # Check for unrealistic timing (activities too close together)
            if self._has_unrealistic_timing(day):
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.INTERNAL_TIME,
                    severity=DisruptionSeverity.MEDIUM,
                    description=f"Day {day_num} has unrealistic activity timing",
                    affected_components=[f"day_{day_num}"],
                    trigger_source="internal_validation",
                    timestamp=datetime.now(),
                    metadata={
                        "day": day_num,
                        "timing_issue": "insufficient travel time between activities"
                    }
                ))
        
        return disruptions
    
    def _detect_travel_time_violations(self, current_itinerary: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect travel time inconsistencies between activities"""
        disruptions = []
        
        itinerary = current_itinerary.get('itinerary', [])
        
        for day in itinerary:
            day_num = day.get('day', 0)
            
            if self._has_distance_conflicts(day):
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.INTERNAL_TIME,
                    severity=DisruptionSeverity.MEDIUM,
                    description=f"Day {day_num} has activities with conflicting locations",
                    affected_components=[f"day_{day_num}"],
                    trigger_source="internal_validation",
                    timestamp=datetime.now(),
                    metadata={
                        "day": day_num,
                        "conflict_type": "geographic_distance",
                        "locations": self._get_day_locations(day)
                    }
                ))
        
        return disruptions
    
    def _detect_preference_changes(self, current_itinerary: Dict[str, Any], 
                                  user_preferences: Dict[str, Any]) -> List[DisruptionEvent]:
        """Detect user preference changes requiring replanning"""
        disruptions = []
        
        current_preferences = current_itinerary.get('preferences', '').lower()
        new_preferences = user_preferences.get('preferences', '').lower()
        
        if current_preferences != new_preferences:
            # Analyze the nature of preference changes
            change_analysis = self._analyze_preference_change(current_preferences, new_preferences)
            
            if change_analysis['significant_change']:
                severity = DisruptionSeverity.MEDIUM if change_analysis['style_change'] else DisruptionSeverity.LOW
                
                disruptions.append(DisruptionEvent(
                    disruption_type=DisruptionType.USER_PREFERENCE,
                    severity=severity,
                    description=f"User preferences updated: {change_analysis['description']}",
                    affected_components=change_analysis['affected_components'],
                    trigger_source="user_input",
                    timestamp=datetime.now(),
                    metadata={
                        "original_preferences": current_preferences,
                        "new_preferences": new_preferences,
                        "change_analysis": change_analysis
                    }
                ))
        
        return disruptions
    
    def analyze_impact(self, disruption: DisruptionEvent, 
                      current_itinerary: Dict[str, Any]) -> ImpactAnalysis:
        """Analyze the impact of a disruption on the current itinerary"""
        
        affected_days = []
        affected_components = disruption.affected_components.copy()
        requires_full_replan = False
        preserve_sections = []
        
        # Determine affected days from component names
        for component in affected_components:
            if component.startswith('day_'):
                day_num = int(component.split('_')[1])
                affected_days.append(day_num)
        
        # If no specific days mentioned, infer from disruption type
        if not affected_days:
            if disruption.disruption_type in [DisruptionType.EXTERNAL_FLIGHT]:
                affected_days = [1]  # Flight affects day 1
            elif disruption.disruption_type in [DisruptionType.EXTERNAL_HOTEL]:
                # Hotel affects all days
                total_days = len(current_itinerary.get('itinerary', []))
                affected_days = list(range(1, total_days + 1))
        
        # Determine if full replan is needed
        if disruption.severity == DisruptionSeverity.CRITICAL:
            requires_full_replan = True
        elif disruption.disruption_type in [DisruptionType.EXTERNAL_FLIGHT, DisruptionType.EXTERNAL_HOTEL]:
            requires_full_replan = True
        elif len(affected_days) > len(current_itinerary.get('itinerary', [])) * 0.5:
            requires_full_replan = True
        
        # Determine sections to preserve
        if not requires_full_replan:
            total_days = len(current_itinerary.get('itinerary', []))
            preserve_sections = [f"day_{i}" for i in range(1, total_days + 1) if i not in affected_days]
            
            # Always preserve unaffected components
            for component in ['flight', 'hotel']:
                if component not in affected_components:
                    preserve_sections.append(component)
        
        # Estimate replan time
        if requires_full_replan:
            estimated_time = "extensive"
        elif len(affected_days) <= 1:
            estimated_time = "quick"
        else:
            estimated_time = "moderate"
        
        return ImpactAnalysis(
            affected_days=affected_days,
            affected_components=affected_components,
            requires_full_replan=requires_full_replan,
            preserve_sections=preserve_sections,
            estimated_replan_time=estimated_time
        )
    
    # Helper methods
    
    def _classify_flight_disruption_severity(self, status: str, flight_info: Dict) -> DisruptionSeverity:
        """Classify the severity of flight disruptions"""
        status_lower = status.lower()
        
        if "cancelled" in status_lower:
            return DisruptionSeverity.CRITICAL
        elif "delayed" in status_lower:
            delay_hours = flight_info.get('delay_hours', 0)
            if delay_hours > 6:
                return DisruptionSeverity.HIGH
            elif delay_hours > 2:
                return DisruptionSeverity.MEDIUM
            else:
                return DisruptionSeverity.LOW
        else:
            return DisruptionSeverity.MEDIUM
    
    def _classify_weather_severity(self, severity_level: str, condition: str) -> DisruptionSeverity:
        """Classify weather disruption severity"""
        if "severe" in severity_level or "extreme" in condition:
            return DisruptionSeverity.HIGH
        elif "moderate" in severity_level or "advisory" in condition:
            return DisruptionSeverity.MEDIUM
        else:
            return DisruptionSeverity.LOW
    
    def _find_weather_affected_days(self, itinerary: Dict[str, Any], weather_condition: str) -> List[int]:
        """Find which days are affected by weather conditions"""
        affected_days = []
        
        # Simple heuristic: outdoor activities affected by bad weather
        outdoor_keywords = ['outdoor', 'park', 'beach', 'hiking', 'nature']
        
        for day in itinerary.get('itinerary', []):
            day_num = day.get('day', 0)
            has_outdoor_activities = False
            
            for slot_activities in day.get('time_slots', {}).values():
                for activity in slot_activities:
                    activity_text = f"{activity.get('title', '')} {activity.get('description', '')}".lower()
                    if any(keyword in activity_text for keyword in outdoor_keywords):
                        has_outdoor_activities = True
                        break
            
            if has_outdoor_activities:
                affected_days.append(day_num)
        
        return affected_days
    
    def _has_unrealistic_timing(self, day_data: Dict) -> bool:
        """Check if a day has unrealistic activity timing"""
        # Simple heuristic: too many activities in a day
        total_activities = sum(len(activities) for activities in day_data.get('time_slots', {}).values())
        return total_activities > 6  # More than 6 activities per day is unrealistic
    
    def _has_distance_conflicts(self, day_data: Dict) -> bool:
        """Check if a day has geographic distance conflicts"""
        locations = self._get_day_locations(day_data)
        
        # Simple heuristic: too many distinct location clusters
        location_clusters = set()
        for location in locations:
            location_lower = location.lower()
            if 'downtown' in location_lower or 'city center' in location_lower:
                location_clusters.add('downtown')
            elif 'airport' in location_lower:
                location_clusters.add('airport')
            elif 'beach' in location_lower or 'waterfront' in location_lower:
                location_clusters.add('waterfront')
            elif 'museum' in location_lower or 'historical' in location_lower:
                location_clusters.add('cultural')
            else:
                location_clusters.add('other')
        
        return len(location_clusters) > 2  # More than 2 distinct areas in one day
    
    def _get_day_locations(self, day_data: Dict) -> List[str]:
        """Extract all locations for a day"""
        locations = []
        for slot_activities in day_data.get('time_slots', {}).values():
            for activity in slot_activities:
                location = activity.get('location', '')
                if location:
                    locations.append(location)
        return locations
    
    def _analyze_preference_change(self, old_prefs: str, new_prefs: str) -> Dict[str, Any]:
        """Analyze the nature of preference changes"""
        old_set = set(old_prefs.split(','))
        new_set = set(new_prefs.split(','))
        
        added = new_set - old_set
        removed = old_set - new_set
        
        # Check for style changes
        style_changes = []
        if 'budget' in removed and 'luxury' in added:
            style_changes.append('budget_to_luxury')
        elif 'luxury' in removed and 'budget' in added:
            style_changes.append('luxury_to_budget')
        
        significant_change = len(added) > 0 or len(removed) > 0
        style_change = len(style_changes) > 0
        
        # Determine affected components
        affected_components = ['activities']
        if style_change:
            affected_components.extend(['hotel', 'budget'])
        
        return {
            'significant_change': significant_change,
            'style_change': style_change,
            'added_preferences': list(added),
            'removed_preferences': list(removed),
            'style_changes': style_changes,
            'description': f"Added: {', '.join(added)}; Removed: {', '.join(removed)}",
            'affected_components': affected_components
        }
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to numeric value"""
        try:
            if isinstance(price_str, str):
                match = re.search(r'[\d,]+', price_str.replace('$', '').replace(',', ''))
                if match:
                    return float(match.group())
            elif isinstance(price_str, (int, float)):
                return float(price_str)
        except:
            pass
        return 0.0
