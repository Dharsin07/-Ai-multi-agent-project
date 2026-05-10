"""
Versioned Itinerary Management System

This service manages multiple versions of travel itineraries, tracks changes,
and provides comprehensive change logging for dynamic replanning scenarios.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import json
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class ItineraryVersion:
    version_number: int
    itinerary_data: Dict[str, Any]
    timestamp: datetime
    change_summary: str
    change_log: List[Dict[str, Any]]
    confidence_score: float
    disruption_reason: Optional[str]
    parent_version: Optional[int]

@dataclass
class ChangeComparison:
    added_items: List[Dict[str, Any]]
    removed_items: List[Dict[str, Any]]
    modified_items: List[Dict[str, Any]]
    cost_changes: Dict[str, float]
    summary: str

class VersionManager:
    """Manages versioned itineraries with comprehensive change tracking"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Version Manager initialized")
        
        # Store versions in memory (in production, this would be a database)
        self.versions: Dict[int, ItineraryVersion] = {}
        self.current_version: int = 0
        
        # Maximum versions to keep in memory
        self.max_versions = 10
    
    def create_initial_version(self, itinerary_data: Dict[str, Any], 
                             confidence_score: float = 0.0) -> int:
        """Create the initial version of an itinerary"""
        self.logger.info("Creating initial itinerary version")
        
        version = ItineraryVersion(
            version_number=1,
            itinerary_data=json.loads(json.dumps(itinerary_data)),  # Deep copy
            timestamp=datetime.now(),
            change_summary="Initial itinerary created",
            change_log=[],
            confidence_score=confidence_score,
            disruption_reason=None,
            parent_version=None
        )
        
        self.versions[1] = version
        self.current_version = 1
        
        self.logger.info(f"Created initial version {version.version_number}")
        return 1
    
    def create_new_version(self, updated_itinerary: Dict[str, Any],
                         change_log: List[Dict[str, Any]],
                         confidence_score: float,
                         disruption_reason: str,
                         parent_version: Optional[int] = None) -> int:
        """Create a new version based on changes"""
        
        if parent_version is None:
            parent_version = self.current_version
        
        new_version_number = parent_version + 1
        
        # Generate change summary
        change_summary = self._generate_change_summary(change_log, disruption_reason)
        
        version = ItineraryVersion(
            version_number=new_version_number,
            itinerary_data=json.loads(json.dumps(updated_itinerary)),  # Deep copy
            timestamp=datetime.now(),
            change_summary=change_summary,
            change_log=change_log.copy(),
            confidence_score=confidence_score,
            disruption_reason=disruption_reason,
            parent_version=parent_version
        )
        
        self.versions[new_version_number] = version
        self.current_version = new_version_number
        
        # Clean up old versions if necessary
        self._cleanup_old_versions()
        
        self.logger.info(f"Created new version {new_version_number} based on version {parent_version}")
        return new_version_number
    
    def get_version(self, version_number: int) -> Optional[ItineraryVersion]:
        """Get a specific version of the itinerary"""
        return self.versions.get(version_number)
    
    def get_current_version(self) -> Optional[ItineraryVersion]:
        """Get the current version of the itinerary"""
        return self.versions.get(self.current_version)
    
    def get_version_history(self) -> List[ItineraryVersion]:
        """Get the complete version history"""
        return sorted(self.versions.values(), key=lambda v: v.version_number)
    
    def compare_versions(self, version1: int, version2: int) -> Optional[ChangeComparison]:
        """Compare two versions and highlight differences"""
        v1_data = self.versions.get(version1)
        v2_data = self.versions.get(version2)
        
        if not v1_data or not v2_data:
            return None
        
        comparison = self._perform_comparison(v1_data.itinerary_data, v2_data.itinerary_data)
        return comparison
    
    def get_latest_changes(self, from_version: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all changes since a specific version"""
        if from_version is None:
            # Get changes from previous version
            from_version = self.current_version - 1
        
        changes = []
        current_ver = self.get_current_version()
        
        if current_ver and current_ver.version_number > from_version:
            changes = current_ver.change_log
        
        return changes
    
    def rollback_to_version(self, target_version: int) -> bool:
        """Rollback to a previous version"""
        target = self.versions.get(target_version)
        
        if not target:
            self.logger.error(f"Version {target_version} not found")
            return False
        
        # Create a new version based on the rollback
        rollback_change_log = [{
            "type": "rollback",
            "action": "rolled_back_to_version",
            "target_version": target_version,
            "previous_version": self.current_version,
            "timestamp": datetime.now().isoformat()
        }]
        
        self.create_new_version(
            target.itinerary_data,
            rollback_change_log,
            target.confidence_score,
            f"Rollback to version {target_version}"
        )
        
        self.logger.info(f"Rolled back from version {self.current_version - 1} to version {target_version}")
        return True
    
    def generate_change_report(self, version_number: Optional[int] = None) -> Dict[str, Any]:
        """Generate a comprehensive change report"""
        if version_number is None:
            version_number = self.current_version
        
        version = self.versions.get(version_number)
        if not version:
            return {"error": f"Version {version_number} not found"}
        
        # Get parent version for comparison
        parent_version = None
        if version.parent_version:
            parent_version = self.versions.get(version.parent_version)
        
        report = {
            "version_info": {
                "version_number": version.version_number,
                "timestamp": version.timestamp.isoformat(),
                "confidence_score": version.confidence_score,
                "disruption_reason": version.disruption_reason,
                "parent_version": version.parent_version
            },
            "change_summary": version.change_summary,
            "change_count": len(version.change_log),
            "changes_by_type": self._categorize_changes(version.change_log)
        }
        
        # Add comparison with parent if available
        if parent_version:
            comparison = self.compare_versions(parent_version.version_number, version.version_number)
            if comparison:
                report["comparison"] = {
                    "added_items": len(comparison.added_items),
                    "removed_items": len(comparison.removed_items),
                    "modified_items": len(comparison.modified_items),
                    "cost_changes": comparison.cost_changes,
                    "summary": comparison.summary
                }
        
        return report
    
    def _generate_change_summary(self, change_log: List[Dict[str, Any]], disruption_reason: str) -> str:
        """Generate a human-readable summary of changes"""
        if not change_log:
            return f"Itinerary updated due to: {disruption_reason}"
        
        # Count change types
        change_types = {}
        for change in change_log:
            change_type = change.get('type', 'unknown')
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        # Build summary
        summary_parts = []
        
        if change_types.get('flight_update', 0) > 0:
            summary_parts.append("Flight updated")
        
        if change_types.get('hotel_update', 0) > 0:
            summary_parts.append("Hotel changed")
        
        if change_types.get('activity_replacement', 0) > 0:
            count = change_types['activity_replacement']
            summary_parts.append(f"{count} activities replaced")
        
        if change_types.get('cost_reduction', 0) > 0:
            summary_parts.append("Costs optimized")
        
        if change_types.get('preference_update', 0) > 0:
            summary_parts.append("Preferences updated")
        
        if change_types.get('rollback', 0) > 0:
            summary_parts.append("Rolled back to previous version")
        
        if summary_parts:
            return f"Updated due to {disruption_reason}: {', '.join(summary_parts)}"
        else:
            return f"Itinerary updated due to: {disruption_reason}"
    
    def _perform_comparison(self, old_itinerary: Dict[str, Any], new_itinerary: Dict[str, Any]) -> ChangeComparison:
        """Perform detailed comparison between two itineraries"""
        added_items = []
        removed_items = []
        modified_items = []
        cost_changes = {}
        
        # Compare flights
        old_flight = old_itinerary.get('selected_flight', {})
        new_flight = new_itinerary.get('selected_flight', {})
        
        if old_flight.get('airline') != new_flight.get('airline'):
            if old_flight and not new_flight:
                removed_items.append({"type": "flight", "data": old_flight})
            elif new_flight and not old_flight:
                added_items.append({"type": "flight", "data": new_flight})
            else:
                modified_items.append({
                    "type": "flight",
                    "old": old_flight,
                    "new": new_flight
                })
        
        # Compare hotels
        old_hotel = old_itinerary.get('selected_hotel', {})
        new_hotel = new_itinerary.get('selected_hotel', {})
        
        if old_hotel.get('name') != new_hotel.get('name'):
            if old_hotel and not new_hotel:
                removed_items.append({"type": "hotel", "data": old_hotel})
            elif new_hotel and not old_hotel:
                added_items.append({"type": "hotel", "data": new_hotel})
            else:
                modified_items.append({
                    "type": "hotel",
                    "old": old_hotel,
                    "new": new_hotel
                })
        
        # Compare itineraries (day-by-day)
        old_days = {day.get('day'): day for day in old_itinerary.get('itinerary', [])}
        new_days = {day.get('day'): day for day in new_itinerary.get('itinerary', [])}
        
        all_day_numbers = set(old_days.keys()) | set(new_days.keys())
        
        for day_num in sorted(all_day_numbers):
            old_day = old_days.get(day_num)
            new_day = new_days.get(day_num)
            
            if old_day and not new_day:
                removed_items.append({"type": "day", "day": day_num, "data": old_day})
            elif new_day and not old_day:
                added_items.append({"type": "day", "day": day_num, "data": new_day})
            elif old_day and new_day:
                # Compare activities within the day
                day_changes = self._compare_day_activities(old_day, new_day, day_num)
                added_items.extend(day_changes['added'])
                removed_items.extend(day_changes['removed'])
                modified_items.extend(day_changes['modified'])
        
        # Calculate cost changes
        old_budget = old_itinerary.get('budget_summary', {})
        new_budget = new_itinerary.get('budget_summary', {})
        
        old_total = self._parse_price(old_budget.get('total_estimated_cost', '0'))
        new_total = self._parse_price(new_budget.get('total_estimated_cost', '0'))
        
        cost_changes['total_cost_change'] = new_total - old_total
        cost_changes['percentage_change'] = ((new_total - old_total) / old_total * 100) if old_total > 0 else 0
        
        # Generate summary
        summary_parts = []
        if added_items:
            summary_parts.append(f"Added {len(added_items)} items")
        if removed_items:
            summary_parts.append(f"Removed {len(removed_items)} items")
        if modified_items:
            summary_parts.append(f"Modified {len(modified_items)} items")
        
        if cost_changes['total_cost_change'] != 0:
            change_amount = abs(cost_changes['total_cost_change'])
            direction = "increased" if cost_changes['total_cost_change'] > 0 else "decreased"
            summary_parts.append(f"Total cost {direction} by ${change_amount:.2f}")
        
        summary = "; ".join(summary_parts) if summary_parts else "No significant changes"
        
        return ChangeComparison(
            added_items=added_items,
            removed_items=removed_items,
            modified_items=modified_items,
            cost_changes=cost_changes,
            summary=summary
        )
    
    def _compare_day_activities(self, old_day: Dict, new_day: Dict, day_num: int) -> Dict[str, List[Dict]]:
        """Compare activities between two days"""
        added = []
        removed = []
        modified = []
        
        old_activities = self._extract_activities_from_day(old_day)
        new_activities = self._extract_activities_from_day(new_day)
        
        # Simple comparison by title (in production, would use more sophisticated matching)
        old_activity_titles = {act.get('title', ''): act for act in old_activities}
        new_activity_titles = {act.get('title', ''): act for act in new_activities}
        
        # Find added activities
        for title, activity in new_activity_titles.items():
            if title not in old_activity_titles:
                added.append({
                    "type": "activity",
                    "day": day_num,
                    "data": activity
                })
        
        # Find removed activities
        for title, activity in old_activity_titles.items():
            if title not in new_activity_titles:
                removed.append({
                    "type": "activity",
                    "day": day_num,
                    "data": activity
                })
        
        # Find modified activities (same title, different details)
        for title in old_activity_titles:
            if title in new_activity_titles:
                old_act = old_activity_titles[title]
                new_act = new_activity_titles[title]
                
                if (old_act.get('description') != new_act.get('description') or
                    old_act.get('cost_estimate') != new_act.get('cost_estimate') or
                    old_act.get('location') != new_act.get('location')):
                    
                    modified.append({
                        "type": "activity",
                        "day": day_num,
                        "title": title,
                        "old": old_act,
                        "new": new_act
                    })
        
        return {"added": added, "removed": removed, "modified": modified}
    
    def _extract_activities_from_day(self, day_data: Dict) -> List[Dict]:
        """Extract all activities from a day"""
        activities = []
        for slot_activities in day_data.get('time_slots', {}).values():
            activities.extend(slot_activities)
        return activities
    
    def _categorize_changes(self, change_log: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize changes by type"""
        categories = {}
        
        for change in change_log:
            change_type = change.get('type', 'unknown')
            categories[change_type] = categories.get(change_type, 0) + 1
        
        return categories
    
    def _cleanup_old_versions(self):
        """Remove old versions to maintain memory limits"""
        if len(self.versions) > self.max_versions:
            # Sort versions by number and remove oldest
            sorted_versions = sorted(self.versions.keys())
            versions_to_remove = sorted_versions[:-self.max_versions]
            
            for version_num in versions_to_remove:
                del self.versions[version_num]
                self.logger.info(f"Removed old version {version_num}")
    
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
    
    def get_version_checksum(self, version_number: int) -> Optional[str]:
        """Generate checksum for version integrity verification"""
        version = self.versions.get(version_number)
        if not version:
            return None
        
        # Create checksum from itinerary data
        itinerary_json = json.dumps(version.itinerary_data, sort_keys=True)
        checksum = hashlib.md5(itinerary_json.encode()).hexdigest()
        
        return checksum
    
    def export_version_history(self) -> Dict[str, Any]:
        """Export complete version history for backup/analysis"""
        history = {
            "export_timestamp": datetime.now().isoformat(),
            "current_version": self.current_version,
            "total_versions": len(self.versions),
            "versions": []
        }
        
        for version in sorted(self.versions.values(), key=lambda v: v.version_number):
            version_data = {
                "version_number": version.version_number,
                "timestamp": version.timestamp.isoformat(),
                "change_summary": version.change_summary,
                "confidence_score": version.confidence_score,
                "disruption_reason": version.disruption_reason,
                "parent_version": version.parent_version,
                "change_count": len(version.change_log),
                "checksum": self.get_version_checksum(version.version_number)
            }
            history["versions"].append(version_data)
        
        return history
