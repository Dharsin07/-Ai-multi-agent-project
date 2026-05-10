"""
Reflection Agent for Multi-Agent Travel Planning System

This service performs comprehensive validation and reflection on generated itineraries
before returning them to the user. It acts as a self-critical layer that evaluates
and improves the travel plans through intelligent feedback loops.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import re
from dataclasses import dataclass
from enum import Enum
from services.itinerary_optimizer import ItineraryOptimizer

class ValidationIssue(Enum):
    BUDGET_EXCEEDED = "budget_exceeded"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    TIME_FLOW_VIOLATION = "time_flow_violation"
    DISTANCE_LOGIC_ERROR = "distance_logic_error"
    SCHEDULING_CONFLICT = "scheduling_conflict"

@dataclass
class ReflectionIssue:
    issue_type: ValidationIssue
    severity: str  # "high", "medium", "low"
    description: str
    affected_component: str  # "flight", "hotel", "activity", "schedule"
    suggested_fix: str
    day_number: Optional[int] = None

@dataclass
class ReflectionReport:
    confidence_score: float  # 0.0 to 1.0
    issues_found: List[ReflectionIssue]
    improvements_made: List[str]
    validation_summary: str
    budget_analysis: Dict[str, Any]
    schedule_analysis: Dict[str, Any]
    recommendations: List[str]

class ReflectionAgent:
    """Agent that reflects on and validates travel itineraries"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Reflection Agent initialized")
        self.itinerary_optimizer = ItineraryOptimizer()
        
        # Location proximity mapping for distance validation
        self.location_clusters = {
            'downtown': ['city center', 'downtown', 'central', 'main street', 'city square'],
            'airport': ['airport', 'airport terminal', 'airfield'],
            'waterfront': ['beach', 'harbor', 'marina', 'waterfront', 'river', 'coast'],
            'historical': ['old town', 'heritage', 'historical', 'ancient', 'museum district'],
            'shopping': ['mall', 'market', 'shopping district', 'boutique area'],
            'entertainment': ['theater district', 'entertainment area', 'nightlife district'],
            'nature': ['park', 'garden', 'nature reserve', 'hiking area', 'outdoor']
        }
        
        # Realistic time allocations for activities
        self.realistic_durations = {
            'morning': {'min_hours': 2, 'max_hours': 4},
            'afternoon': {'min_hours': 2, 'max_hours': 5},
            'evening': {'min_hours': 2, 'max_hours': 4}
        }
    
    def reflect_on_itinerary(self, itinerary_data: Dict[str, Any], 
                           budget: str, max_iterations: int = 1) -> Dict[str, Any]:
        """
        Main reflection function that validates and improves the itinerary
        """
        self.logger.info("Starting itinerary reflection process")
        
        current_itinerary = itinerary_data.copy()
        iteration = 0
        reflection_history = []
        
        while iteration <= max_iterations:
            self.logger.info(f"Reflection iteration {iteration + 1}")
            
            # Perform comprehensive validation
            reflection_report = self._validate_itinerary(current_itinerary, budget)
            reflection_history.append(reflection_report)
            
            # If no issues found or high confidence, return the result
            if not reflection_report.issues_found or reflection_report.confidence_score >= 0.85:
                self.logger.info(f"Itinerary validation complete. Confidence: {reflection_report.confidence_score:.2f}")
                break
            
            # Apply feedback and rebuild itinerary
            if iteration < max_iterations:
                self.logger.info("Applying feedback and rebuilding itinerary")
                current_itinerary = self._apply_feedback_and_rebuild(
                    current_itinerary, 
                    reflection_report.issues_found,
                    budget
                )
            
            iteration += 1
        
        # Generate final reflection report
        final_report = self._generate_final_report(reflection_history, current_itinerary)
        
        # Add reflection data to the itinerary
        current_itinerary['reflection_report'] = {
            'confidence_score': final_report.confidence_score,
            'validation_summary': final_report.validation_summary,
            'improvements_made': final_report.improvements_made,
            'recommendations': final_report.recommendations,
            'iterations_performed': iteration,
            'budget_analysis': final_report.budget_analysis,
            'schedule_analysis': final_report.schedule_analysis
        }
        
        self.logger.info(f"Reflection complete. Final confidence score: {final_report.confidence_score:.2f}")
        return current_itinerary
    
    def _validate_itinerary(self, itinerary_data: Dict[str, Any], budget: str) -> ReflectionReport:
        """Perform comprehensive validation of the itinerary"""
        issues = []
        improvements = []
        
        # 1. Budget Validation
        budget_issues = self._validate_budget(itinerary_data, budget)
        issues.extend(budget_issues)
        
        # 2. Logical Consistency Check
        logic_issues = self._validate_logical_consistency(itinerary_data)
        issues.extend(logic_issues)
        
        # 3. Time Flow Validation
        time_issues = self._validate_time_flow(itinerary_data)
        issues.extend(time_issues)
        
        # 4. Travel Distance Logic
        distance_issues = self._validate_travel_distances(itinerary_data)
        issues.extend(distance_issues)
        
        # 5. Scheduling Conflicts
        schedule_issues = self._validate_scheduling_conflicts(itinerary_data)
        issues.extend(schedule_issues)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(issues, itinerary_data)
        
        # Generate analysis summaries
        budget_analysis = self._analyze_budget_breakdown(itinerary_data, budget)
        schedule_analysis = self._analyze_schedule_quality(itinerary_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, itinerary_data)
        
        return ReflectionReport(
            confidence_score=confidence_score,
            issues_found=issues,
            improvements_made=improvements,
            validation_summary=self._create_validation_summary(issues, confidence_score),
            budget_analysis=budget_analysis,
            schedule_analysis=schedule_analysis,
            recommendations=recommendations
        )
    
    def _validate_budget(self, itinerary_data: Dict[str, Any], budget: str) -> List[ReflectionIssue]:
        """Validate budget compliance and identify overspending"""
        issues = []
        
        try:
            budget_amount = self._parse_budget(budget)
            budget_summary = itinerary_data.get('budget_summary', {})
            total_cost_str = budget_summary.get('total_estimated_cost', '0')
            total_cost = self._parse_price(total_cost_str)
            
            if total_cost > budget_amount:
                overspend = total_cost - budget_amount
                issues.append(ReflectionIssue(
                    issue_type=ValidationIssue.BUDGET_EXCEEDED,
                    severity="high",
                    description=f"Total cost ${total_cost:.2f} exceeds budget ${budget_amount:.2f} by ${overspend:.2f}",
                    affected_component="budget",
                    suggested_fix="Reduce activity costs or downgrade hotel/accommodation"
                ))
                
                # Identify specific overspending categories
                flights_cost = self._parse_price(budget_summary.get('flights_cost', '0'))
                hotel_cost = self._parse_price(budget_summary.get('accommodation_cost', '0'))
                activities_cost = self._parse_price(budget_summary.get('activities_food_cost', '0'))
                
                if hotel_cost > budget_amount * 0.4:
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.BUDGET_EXCEEDED,
                        severity="medium",
                        description=f"Hotel cost ${hotel_cost:.2f} is {((hotel_cost/budget_amount)*100):.1f}% of budget",
                        affected_component="hotel",
                        suggested_fix="Consider downgrading hotel or shorter stay"
                    ))
                
                if activities_cost > budget_amount * 0.3:
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.BUDGET_EXCEEDED,
                        severity="medium",
                        description=f"Activities cost ${activities_cost:.2f} exceeds recommended 30% of budget",
                        affected_component="activity",
                        suggested_fix="Remove or replace expensive activities"
                    ))
        
        except Exception as e:
            self.logger.error(f"Budget validation error: {e}")
        
        return issues
    
    def _validate_logical_consistency(self, itinerary_data: Dict[str, Any]) -> List[ReflectionIssue]:
        """Check logical consistency of the travel plan"""
        issues = []
        itinerary = itinerary_data.get('itinerary', [])
        selected_flight = itinerary_data.get('selected_flight', {})
        selected_hotel = itinerary_data.get('selected_hotel', {})
        
        # Check Day 1 alignment with arrival flight
        if itinerary and selected_flight:
            day1 = next((day for day in itinerary if day.get('day') == 1), None)
            if day1:
                morning_activities = day1.get('time_slots', {}).get('morning', [])
                if not any('arrival' in activity.get('title', '').lower() or 
                          'airport' in activity.get('description', '').lower() 
                          for activity in morning_activities):
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.LOGICAL_INCONSISTENCY,
                        severity="medium",
                        description="Day 1 morning activities don't account for flight arrival",
                        affected_component="schedule",
                        suggested_fix="Add airport arrival and transfer activity to Day 1 morning",
                        day_number=1
                    ))
        
        # Check departure day consistency
        if itinerary and selected_flight:
            last_day = max((day.get('day', 1) for day in itinerary), default=1)
            departure_day = next((day for day in itinerary if day.get('day') == last_day), None)
            if departure_day:
                afternoon_activities = departure_day.get('time_slots', {}).get('afternoon', [])
                if not any('departure' in activity.get('title', '').lower() or 
                          'check-out' in activity.get('description', '').lower()
                          for activity in afternoon_activities):
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.LOGICAL_INCONSISTENCY,
                        severity="medium",
                        description=f"Day {last_day} doesn't include departure preparation",
                        affected_component="schedule",
                        suggested_fix="Add hotel check-out and airport transfer to departure day",
                        day_number=last_day
                    ))
        
        # Check hotel continuity across days
        if itinerary and selected_hotel:
            hotel_name = selected_hotel.get('name', '')
            for day in itinerary:
                day_num = day.get('day')
                # Note: Current structure doesn't show hotel per day, but we should validate consistency
                # This would be enhanced if hotel info is stored per day
        
        return issues
    
    def _validate_time_flow(self, itinerary_data: Dict[str, Any]) -> List[ReflectionIssue]:
        """Validate realistic time flow and scheduling"""
        issues = []
        itinerary = itinerary_data.get('itinerary', [])
        
        for day in itinerary:
            day_num = day.get('day')
            time_slots = day.get('time_slots', {})
            
            # Check each time slot for realistic scheduling
            for slot_name, activities in time_slots.items():
                if not activities:
                    continue
                
                # Check for overloaded time slots
                if len(activities) > 2:
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.TIME_FLOW_VIOLATION,
                        severity="medium",
                        description=f"Day {day_num} {slot_name} has {len(activities)} activities - may be overloaded",
                        affected_component="schedule",
                        suggested_fix=f"Reduce activities in {slot_name} to 1-2 maximum",
                        day_number=day_num
                    ))
                
                # Check activity duration realism
                for activity in activities:
                    activity_type = activity.get('type', '').lower()
                    if activity_type in ['museum', 'tour', 'exploration']:
                        # These typically need more time
                        if slot_name == 'evening' and len(activities) > 1:
                            issues.append(ReflectionIssue(
                                issue_type=ValidationIssue.TIME_FLOW_VIOLATION,
                                severity="low",
                                description=f"Day {day_num} evening may be too crowded for {activity.get('title', 'activity')}",
                                affected_component="schedule",
                                suggested_fix="Move time-intensive activities to morning or afternoon",
                                day_number=day_num
                            ))
        
        return issues
    
    def _validate_travel_distances(self, itinerary_data: Dict[str, Any]) -> List[ReflectionIssue]:
        """Validate logical travel distances between activities"""
        issues = []
        itinerary = itinerary_data.get('itinerary', [])
        
        for day in itinerary:
            day_num = day.get('day')
            time_slots = day.get('time_slots', {})
            
            # Collect all activity locations for the day
            daily_locations = []
            for slot_activities in time_slots.values():
                for activity in slot_activities:
                    location = activity.get('location', '').lower()
                    if location:
                        daily_locations.append(location)
            
            # Check for unrealistic location combinations
            if len(daily_locations) >= 2:
                location_clusters = self._group_locations_by_proximity(daily_locations)
                
                # If activities are spread across distant clusters, flag it
                if len(location_clusters) > 2:
                    issues.append(ReflectionIssue(
                        issue_type=ValidationIssue.DISTANCE_LOGIC_ERROR,
                        severity="medium",
                        description=f"Day {day_num} activities span {len(location_clusters)} different location areas",
                        affected_component="schedule",
                        suggested_fix="Group activities by geographic proximity to reduce travel time",
                        day_number=day_num
                    ))
        
        return issues
    
    def _validate_scheduling_conflicts(self, itinerary_data: Dict[str, Any]) -> List[ReflectionIssue]:
        """Check for scheduling conflicts and overlaps"""
        issues = []
        itinerary = itinerary_data.get('itinerary', [])
        
        for day in itinerary:
            day_num = day.get('day')
            time_slots = day.get('time_slots', {})
            
            # Check for duplicate activity types in same time slot
            for slot_name, activities in time_slots.items():
                activity_types = [activity.get('type', '').lower() for activity in activities]
                
                # Count duplicates
                type_counts = {}
                for activity_type in activity_types:
                    if activity_type:
                        type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
                
                for activity_type, count in type_counts.items():
                    if count > 1 and activity_type not in ['dining', 'exploration']:
                        issues.append(ReflectionIssue(
                            issue_type=ValidationIssue.SCHEDULING_CONFLICT,
                            severity="low",
                            description=f"Day {day_num} {slot_name} has {count} {activity_type} activities",
                            affected_component="schedule",
                            suggested_fix="Vary activity types within time slots for better experience",
                            day_number=day_num
                        ))
        
        return issues
    
    def _group_locations_by_proximity(self, locations: List[str]) -> List[str]:
        """Group locations by geographic proximity"""
        clusters = []
        
        for location in locations:
            assigned_cluster = None
            
            for cluster_name, keywords in self.location_clusters.items():
                if any(keyword in location for keyword in keywords):
                    assigned_cluster = cluster_name
                    break
            
            if assigned_cluster and assigned_cluster not in clusters:
                clusters.append(assigned_cluster)
            elif not assigned_cluster and 'other' not in clusters:
                clusters.append('other')
        
        return clusters
    
    def _calculate_confidence_score(self, issues: List[ReflectionIssue], 
                                  itinerary_data: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on issues found"""
        base_score = 1.0
        
        # Deduct points based on issue severity
        for issue in issues:
            if issue.severity == "high":
                base_score -= 0.25
            elif issue.severity == "medium":
                base_score -= 0.15
            elif issue.severity == "low":
                base_score -= 0.05
        
        # Ensure score doesn't go below 0
        confidence_score = max(0.0, base_score)
        
        # Bonus points for having complete itinerary structure
        if itinerary_data.get('itinerary') and len(itinerary_data['itinerary']) > 0:
            confidence_score += 0.05
        
        if itinerary_data.get('selected_flight') and itinerary_data.get('selected_hotel'):
            confidence_score += 0.05
        
        return min(1.0, confidence_score)
    
    def _apply_feedback_and_rebuild(self, itinerary_data: Dict[str, Any], 
                                  issues: List[ReflectionIssue], 
                                  budget: str) -> Dict[str, Any]:
        """Apply feedback to rebuild improved itinerary"""
        self.logger.info("Applying feedback to rebuild itinerary")
        
        # Extract components for rebuilding
        ranked_flights = [itinerary_data.get('selected_flight', {})]
        ranked_hotels = [itinerary_data.get('selected_hotel', {})]
        
        # Rebuild with feedback
        feedback_enhanced_itinerary = self.itinerary_optimizer.optimize_itinerary(
            ranked_flights,
            ranked_hotels,
            self._extract_activities_from_feedback(itinerary_data, issues),
            budget,
            itinerary_data.get('duration', '3 days'),
            itinerary_data.get('destination', 'Unknown')
        )
        
        return feedback_enhanced_itinerary
    
    def _extract_activities_from_feedback(self, itinerary_data: Dict[str, Any], 
                                        issues: List[ReflectionIssue]) -> List[Dict[str, Any]]:
        """Extract and modify activities based on feedback"""
        # For now, return existing activities
        # In a more sophisticated implementation, this would modify activities
        # based on the specific issues found
        activities = []
        
        for day in itinerary_data.get('itinerary', []):
            for slot_activities in day.get('time_slots', {}).values():
                activities.extend(slot_activities)
        
        return activities
    
    def _generate_final_report(self, reflection_history: List[ReflectionReport], 
                             final_itinerary: Dict[str, Any]) -> ReflectionReport:
        """Generate final reflection report from all iterations"""
        if not reflection_history:
            return ReflectionReport(
                confidence_score=0.0,
                issues_found=[],
                improvements_made=[],
                validation_summary="No validation performed",
                budget_analysis={},
                schedule_analysis={},
                recommendations=[]
            )
        
        # Use the last report as final
        final_report = reflection_history[-1]
        
        # Compile improvements from all iterations
        all_improvements = []
        for report in reflection_history:
            all_improvements.extend(report.improvements_made)
        
        final_report.improvements_made = list(set(all_improvements))  # Remove duplicates
        
        return final_report
    
    def _create_validation_summary(self, issues: List[ReflectionIssue], 
                                 confidence_score: float) -> str:
        """Create a human-readable validation summary"""
        if not issues:
            return "✅ Itinerary passed all validation checks with high confidence."
        
        high_issues = [i for i in issues if i.severity == "high"]
        medium_issues = [i for i in issues if i.severity == "medium"]
        low_issues = [i for i in issues if i.severity == "low"]
        
        summary_parts = []
        
        if high_issues:
            summary_parts.append(f"⚠️ {len(high_issues)} high-priority issues found")
        if medium_issues:
            summary_parts.append(f"⚡ {len(medium_issues)} medium-priority issues found")
        if low_issues:
            summary_parts.append(f"💡 {len(low_issues)} minor suggestions")
        
        summary_parts.append(f"🎯 Overall confidence: {confidence_score:.1%}")
        
        return " | ".join(summary_parts)
    
    def _analyze_budget_breakdown(self, itinerary_data: Dict[str, Any], 
                                budget: str) -> Dict[str, Any]:
        """Analyze budget breakdown and provide insights"""
        budget_summary = itinerary_data.get('budget_summary', {})
        budget_amount = self._parse_budget(budget)
        total_cost = self._parse_price(budget_summary.get('total_estimated_cost', '0'))
        
        return {
            'budget_amount': budget_amount,
            'total_cost': total_cost,
            'remaining_budget': budget_amount - total_cost,
            'utilization_percentage': (total_cost / budget_amount * 100) if budget_amount > 0 else 0,
            'cost_breakdown': {
                'flights': self._parse_price(budget_summary.get('flights_cost', '0')),
                'accommodation': self._parse_price(budget_summary.get('accommodation_cost', '0')),
                'activities': self._parse_price(budget_summary.get('activities_food_cost', '0'))
            },
            'within_budget': total_cost <= budget_amount
        }
    
    def _analyze_schedule_quality(self, itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schedule quality and pacing"""
        itinerary = itinerary_data.get('itinerary', [])
        
        total_days = len(itinerary)
        total_activities = 0
        activities_per_day = []
        
        for day in itinerary:
            day_activities = 0
            for slot_activities in day.get('time_slots', {}).values():
                day_activities += len(slot_activities)
            activities_per_day.append(day_activities)
            total_activities += day_activities
        
        avg_activities_per_day = total_activities / total_days if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'total_activities': total_activities,
            'average_activities_per_day': avg_activities_per_day,
            'activities_per_day': activities_per_day,
            'schedule_density': 'balanced' if 2 <= avg_activities_per_day <= 4 else 
                              'light' if avg_activities_per_day < 2 else 'dense'
        }
    
    def _generate_recommendations(self, issues: List[ReflectionIssue], 
                                itinerary_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on issues"""
        recommendations = []
        
        # Group issues by type for comprehensive recommendations
        budget_issues = [i for i in issues if i.issue_type == ValidationIssue.BUDGET_EXCEEDED]
        schedule_issues = [i for i in issues if i.issue_type in [ValidationIssue.TIME_FLOW_VIOLATION, ValidationIssue.SCHEDULING_CONFLICT]]
        distance_issues = [i for i in issues if i.issue_type == ValidationIssue.DISTANCE_LOGIC_ERROR]
        
        if budget_issues:
            recommendations.append("💰 Consider reducing activity costs or choosing more budget-friendly accommodation options")
        
        if schedule_issues:
            recommendations.append("⏰ Review daily schedules to ensure realistic timing and avoid overloading")
        
        if distance_issues:
            recommendations.append("🗺️ Group activities by geographic proximity to minimize travel time")
        
        # General recommendations
        if not issues:
            recommendations.append("🎉 Excellent itinerary planning! Consider booking early for best prices")
        
        return recommendations
    
    def _parse_budget(self, budget: str) -> float:
        """Parse budget string to numeric amount"""
        try:
            match = re.search(r'[\d,]+', budget.replace('$', '').replace(',', ''))
            if match:
                return float(match.group())
        except:
            pass
        return 2000.0  # Default budget
    
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
