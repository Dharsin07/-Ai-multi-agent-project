"""
Dynamic Replanning Coordinator

This service coordinates the entire dynamic replanning process, integrating
disruption detection, impact analysis, targeted replanning, and version management
into a unified, intelligent travel planning system.
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger
import json
from dataclasses import dataclass
from datetime import datetime

from services.disruption_detector import DisruptionDetector, DisruptionEvent, ImpactAnalysis
from services.dynamic_replanner import DynamicReplanner, ReplanRequest, ReplanResult
from services.version_manager import VersionManager, ItineraryVersion
from services.reflection_agent import ReflectionAgent

@dataclass
class ReplanningRequest:
    current_itinerary: Dict[str, Any]
    updated_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    trigger_source: str  # "external_disruption", "internal_violation", "user_preference"
    original_budget: str

@dataclass
class ReplanningResponse:
    success: bool
    updated_itinerary: Dict[str, Any]
    version_number: int
    change_log: List[Dict[str, Any]]
    confidence_score: float
    disruption_summary: Dict[str, Any]
    impact_analysis: Dict[str, Any]
    affected_sections: List[str]
    preserved_sections: List[str]
    recommendations: List[str]

class DynamicReplanningCoordinator:
    """Main coordinator for dynamic travel itinerary replanning"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Dynamic Replanning Coordinator initialized")
        
        # Initialize components
        self.disruption_detector = DisruptionDetector()
        self.dynamic_replanner = DynamicReplanner()
        self.version_manager = VersionManager()
        self.reflection_agent = ReflectionAgent()
        
        # Initialize with empty state
        self.current_session_id = None
        self.initialized = False
    
    def initialize_itinerary(self, initial_itinerary: Dict[str, Any], 
                           confidence_score: float = 0.0) -> int:
        """Initialize the system with an initial itinerary"""
        self.logger.info("Initializing dynamic replanning system with initial itinerary")
        
        # Store original budget for future reference
        if 'budget' in initial_itinerary:
            initial_itinerary['original_budget'] = initial_itinerary['budget']
        
        # Create initial version
        version_number = self.version_manager.create_initial_version(
            initial_itinerary, 
            confidence_score
        )
        
        self.initialized = True
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"System initialized with version {version_number}")
        return version_number
    
    def process_replanning_trigger(self, request: ReplanningRequest) -> ReplanningResponse:
        """
        Process a replanning trigger and return the updated itinerary
        """
        self.logger.info(f"Processing replanning trigger from {request.trigger_source}")
        
        try:
            # Step 1: Detect disruptions
            disruptions = self.disruption_detector.detect_disruptions(
                request.current_itinerary,
                request.updated_data,
                request.user_preferences
            )
            
            if not disruptions:
                self.logger.info("No disruptions detected, no replanning needed")
                return self._create_no_change_response(request)
            
            # Step 2: Analyze impact (use the highest severity disruption)
            primary_disruption = self._get_primary_disruption(disruptions)
            impact_analysis = self.disruption_detector.analyze_impact(
                primary_disruption, 
                request.current_itinerary
            )
            
            # Step 3: Execute targeted replanning
            replan_request = ReplanRequest(
                disruption_event=primary_disruption,
                impact_analysis=impact_analysis,
                current_itinerary=request.current_itinerary,
                updated_data=request.updated_data,
                user_preferences=request.user_preferences
            )
            
            replan_result = self.dynamic_replanner.execute_replan(replan_request)
            
            if not replan_result.success:
                self.logger.error("Replanning failed")
                return self._create_failure_response(request, primary_disruption, replan_result)
            
            # Step 4: Create new version
            new_version_number = self.version_manager.create_new_version(
                replan_result.updated_itinerary,
                replan_result.change_log,
                replan_result.confidence_score,
                replan_result.replan_reason
            )
            
            # Step 5: Generate comprehensive response
            response = self._create_success_response(
                request,
                primary_disruption,
                impact_analysis,
                replan_result,
                new_version_number
            )
            
            self.logger.info(f"Replanning completed successfully. New version: {new_version_number}")
            return response
            
        except Exception as e:
            self.logger.error(f"Replanning process failed: {e}")
            return self._create_error_response(request, str(e))
    
    def handle_flight_disruption(self, current_itinerary: Dict[str, Any],
                               flight_update: Dict[str, Any],
                               user_preferences: Dict[str, Any]) -> ReplanningResponse:
        """Handle flight-specific disruption"""
        request = ReplanningRequest(
            current_itinerary=current_itinerary,
            updated_data={'flight_update': flight_update},
            user_preferences=user_preferences,
            trigger_source="external_disruption",
            original_budget=current_itinerary.get('original_budget', '$2000')
        )
        
        return self.process_replanning_trigger(request)
    
    def handle_hotel_disruption(self, current_itinerary: Dict[str, Any],
                              hotel_update: Dict[str, Any],
                              user_preferences: Dict[str, Any]) -> ReplanningResponse:
        """Handle hotel-specific disruption"""
        request = ReplanningRequest(
            current_itinerary=current_itinerary,
            updated_data={'hotel_update': hotel_update},
            user_preferences=user_preferences,
            trigger_source="external_disruption",
            original_budget=current_itinerary.get('original_budget', '$2000')
        )
        
        return self.process_replanning_trigger(request)
    
    def handle_weather_disruption(self, current_itinerary: Dict[str, Any],
                                weather_update: Dict[str, Any],
                                user_preferences: Dict[str, Any]) -> ReplanningResponse:
        """Handle weather-specific disruption"""
        request = ReplanningRequest(
            current_itinerary=current_itinerary,
            updated_data={'weather_update': weather_update},
            user_preferences=user_preferences,
            trigger_source="external_disruption",
            original_budget=current_itinerary.get('original_budget', '$2000')
        )
        
        return self.process_replanning_trigger(request)
    
    def handle_budget_violation(self, current_itinerary: Dict[str, Any],
                             user_preferences: Dict[str, Any]) -> ReplanningResponse:
        """Handle internal budget violation"""
        request = ReplanningRequest(
            current_itinerary=current_itinerary,
            updated_data={},
            user_preferences=user_preferences,
            trigger_source="internal_violation",
            original_budget=current_itinerary.get('original_budget', '$2000')
        )
        
        return self.process_replanning_trigger(request)
    
    def handle_preference_change(self, current_itinerary: Dict[str, Any],
                               new_preferences: Dict[str, Any]) -> ReplanningResponse:
        """Handle user preference changes"""
        request = ReplanningRequest(
            current_itinerary=current_itinerary,
            updated_data={},
            user_preferences=new_preferences,
            trigger_source="user_preference",
            original_budget=current_itinerary.get('original_budget', '$2000')
        )
        
        return self.process_replanning_trigger(request)
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get the complete version history"""
        versions = self.version_manager.get_version_history()
        
        history = []
        for version in versions:
            version_info = {
                "version_number": version.version_number,
                "timestamp": version.timestamp.isoformat(),
                "change_summary": version.change_summary,
                "confidence_score": version.confidence_score,
                "disruption_reason": version.disruption_reason,
                "parent_version": version.parent_version,
                "change_count": len(version.change_log)
            }
            history.append(version_info)
        
        return history
    
    def get_version_comparison(self, version1: int, version2: int) -> Optional[Dict[str, Any]]:
        """Compare two versions and return differences"""
        comparison = self.version_manager.compare_versions(version1, version2)
        
        if not comparison:
            return None
        
        return {
            "version1": version1,
            "version2": version2,
            "added_items": comparison.added_items,
            "removed_items": comparison.removed_items,
            "modified_items": comparison.modified_items,
            "cost_changes": comparison.cost_changes,
            "summary": comparison.summary
        }
    
    def rollback_to_version(self, target_version: int) -> bool:
        """Rollback to a previous version"""
        success = self.version_manager.rollback_to_version(target_version)
        
        if success:
            self.logger.info(f"Successfully rolled back to version {target_version}")
        else:
            self.logger.error(f"Failed to rollback to version {target_version}")
        
        return success
    
    def get_current_itinerary(self) -> Optional[Dict[str, Any]]:
        """Get the current version of the itinerary"""
        current_version = self.version_manager.get_current_version()
        
        if current_version:
            return current_version.itinerary_data
        
        return None
    
    def generate_replanning_report(self) -> Dict[str, Any]:
        """Generate a comprehensive replanning report"""
        current_version = self.version_manager.get_current_version()
        
        if not current_version:
            return {"error": "No current version available"}
        
        version_report = self.version_manager.generate_change_report()
        version_history = self.get_version_history()
        
        return {
            "session_info": {
                "session_id": self.current_session_id,
                "initialized": self.initialized,
                "current_version": current_version.version_number
            },
            "current_version_report": version_report,
            "version_history": version_history,
            "total_versions": len(version_history),
            "system_status": "active"
        }
    
    # Private helper methods
    
    def _get_primary_disruption(self, disruptions: List[DisruptionEvent]) -> DisruptionEvent:
        """Select the primary disruption to handle (highest severity)"""
        if not disruptions:
            raise ValueError("No disruptions provided")
        
        # Sort by severity (critical > high > medium > low)
        severity_order = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        primary_disruption = max(disruptions, 
                               key=lambda d: severity_order.get(d.severity.value, 0))
        
        return primary_disruption
    
    def _create_success_response(self, request: ReplanningRequest,
                               disruption: DisruptionEvent,
                               impact: ImpactAnalysis,
                               result: ReplanResult,
                               version_number: int) -> ReplanningResponse:
        """Create a successful replanning response"""
        
        # Generate recommendations based on the changes
        recommendations = self._generate_recommendations(disruption, impact, result)
        
        return ReplanningResponse(
            success=True,
            updated_itinerary=result.updated_itinerary,
            version_number=version_number,
            change_log=result.change_log,
            confidence_score=result.confidence_score,
            disruption_summary={
                "type": disruption.disruption_type.value,
                "severity": disruption.severity.value,
                "description": disruption.description,
                "trigger_source": disruption.trigger_source
            },
            impact_analysis={
                "affected_days": impact.affected_days,
                "affected_components": impact.affected_components,
                "requires_full_replan": impact.requires_full_replan,
                "estimated_replan_time": impact.estimated_replan_time
            },
            affected_sections=result.affected_sections,
            preserved_sections=result.preserved_sections,
            recommendations=recommendations
        )
    
    def _create_no_change_response(self, request: ReplanningRequest) -> ReplanningResponse:
        """Create a response when no changes are needed"""
        current_version = self.version_manager.get_current_version()
        
        return ReplanningResponse(
            success=True,
            updated_itinerary=request.current_itinerary,
            version_number=current_version.version_number if current_version else 0,
            change_log=[],
            confidence_score=current_version.confidence_score if current_version else 0.0,
            disruption_summary={},
            impact_analysis={},
            affected_sections=[],
            preserved_sections=["all"],
            recommendations=["No changes needed - itinerary is optimal"]
        )
    
    def _create_failure_response(self, request: ReplanningRequest,
                               disruption: DisruptionEvent,
                               result: ReplanResult) -> ReplanningResponse:
        """Create a response when replanning fails"""
        return ReplanningResponse(
            success=False,
            updated_itinerary=request.current_itinerary,
            version_number=self.version_manager.current_version,
            change_log=result.change_log,
            confidence_score=0.0,
            disruption_summary={
                "type": disruption.disruption_type.value,
                "severity": disruption.severity.value,
                "description": disruption.description,
                "error": "Replanning failed"
            },
            impact_analysis={},
            affected_sections=[],
            preserved_sections=[],
            recommendations=["Manual review required - automatic replanning failed"]
        )
    
    def _create_error_response(self, request: ReplanningRequest, error: str) -> ReplanningResponse:
        """Create a response when an error occurs"""
        return ReplanningResponse(
            success=False,
            updated_itinerary=request.current_itinerary,
            version_number=self.version_manager.current_version,
            change_log=[{"error": error}],
            confidence_score=0.0,
            disruption_summary={},
            impact_analysis={},
            affected_sections=[],
            preserved_sections=[],
            recommendations=[f"Error occurred: {error}"]
        )
    
    def _generate_recommendations(self, disruption: DisruptionEvent,
                                impact: ImpactAnalysis,
                                result: ReplanResult) -> List[str]:
        """Generate recommendations based on the replanning results"""
        recommendations = []
        
        # Based on disruption type
        if disruption.disruption_type.value == "external_flight":
            recommendations.append("Monitor flight status for further updates")
            recommendations.append("Consider travel insurance for future trips")
        
        elif disruption.disruption_type.value == "external_hotel":
            recommendations.append("Confirm new hotel booking immediately")
            recommendations.append("Update hotel information in travel documents")
        
        elif disruption.disruption_type.value == "external_weather":
            recommendations.append("Pack appropriate clothing for weather conditions")
            recommendations.append("Have indoor backup activities ready")
        
        elif disruption.disruption_type.value == "internal_budget":
            recommendations.append("Track expenses carefully during trip")
            recommendations.append("Consider additional budget for unexpected costs")
        
        elif disruption.disruption_type.value == "user_preference":
            recommendations.append("Review updated itinerary for preference alignment")
            recommendations.append("Provide feedback on preference changes")
        
        # Based on confidence score
        if result.confidence_score < 0.7:
            recommendations.append("Manual review of updated itinerary recommended")
        elif result.confidence_score < 0.9:
            recommendations.append("Monitor for any additional disruptions")
        
        # Based on impact
        if impact.requires_full_replan:
            recommendations.append("Major changes made - review entire itinerary")
        else:
            recommendations.append("Targeted changes applied - most of itinerary preserved")
        
        return recommendations
