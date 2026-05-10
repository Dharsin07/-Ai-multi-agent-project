import re
import json
from typing import Dict, Any, List
from utils.logger import logger
from langchain_groq import ChatGroq
import os

class NaturalLanguageTravelProcessor:
    def __init__(self):
        """Initialize the LLM for natural language processing"""
        self.llm = ChatGroq(
            temperature=0.3,
            model_name=os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
        )
        logger.info("Natural Language Travel Processor initialized")
    
    def process_travel_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language travel request through complete pipeline:
        1. Intent Understanding
        2. Data Extraction  
        3. Tool Decision
        4. Task Splitting
        5. Final Plan Generation
        """
        logger.info(f"Processing natural language request: {user_input[:100]}...")
        
        try:
            # Step 1: Intent Understanding
            intent_result = self.understand_intent(user_input)
            
            # Step 2: Data Extraction
            extracted_data = self.extract_travel_data(user_input, intent_result)
            
            # Step 3: Tool Decision
            tool_decisions = self.decide_tools(extracted_data, intent_result)
            
            # Step 4: Task Splitting
            task_split = self.split_tasks(extracted_data, tool_decisions)
            
            # Step 5: Final Plan Generation
            final_plan = self.generate_final_plan(extracted_data, task_split)
            
            return {
                "success": True,
                "processing_pipeline": {
                    "step_1_intent": intent_result,
                    "step_2_extraction": extracted_data,
                    "step_3_tools": tool_decisions,
                    "step_4_tasks": task_split,
                    "step_5_plan": final_plan
                },
                "extracted_data": extracted_data,
                "tool_decisions": tool_decisions,
                "task_split": task_split,
                "final_plan": final_plan
            }
            
        except Exception as e:
            logger.error(f"Error processing natural language request: {e}")
            return self.get_fallback_response(user_input)
    
    def understand_intent(self, user_input: str) -> Dict[str, Any]:
        """Step 1: Understand user intent"""
        input_lower = user_input.lower()
        
        # Intent classification
        intents = {
            "travel_planning": 0,
            "vacation": 0,
            "business_trip": 0,
            "romantic_getaway": 0,
            "family_vacation": 0,
            "adventure_travel": 0,
            "cultural_tourism": 0,
            "budget_travel": 0,
            "luxury_travel": 0
        }
        
        # Keyword matching for intent
        intent_keywords = {
            "travel_planning": ["plan", "trip", "travel", "visit", "go to"],
            "vacation": ["vacation", "holiday", "break", "getaway", "relax"],
            "business_trip": ["business", "work", "conference", "meeting", "professional"],
            "romantic_getaway": ["romantic", "anniversary", "honeymoon", "couple", "romance"],
            "family_vacation": ["family", "kids", "children", "parents", "family vacation"],
            "adventure_travel": ["adventure", "hiking", "trekking", "extreme", "sports"],
            "cultural_tourism": ["culture", "museums", "historical", "art", "heritage"],
            "budget_travel": ["budget", "cheap", "affordable", "save money", "economy"],
            "luxury_travel": ["luxury", "premium", "5-star", "deluxe", "high-end"]
        }
        
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in input_lower:
                    intents[intent] += 1
        
        # Determine primary intent
        primary_intent = max(intents, key=intents.get)
        confidence = min(intents[primary_intent] / 3.0, 1.0)  # Normalize confidence
        
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "all_intents": intents,
            "travel_type": self._classify_travel_type(input_lower),
            "urgency": self._detect_urgency(input_lower),
            "complexity": self._assess_complexity(user_input)
        }
    
    def extract_travel_data(self, user_input: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Extract structured travel data"""
        extracted = {
            "destination": self._extract_destination(user_input),
            "budget": self._extract_budget(user_input),
            "duration": self._extract_duration(user_input),
            "dates": self._extract_dates(user_input),
            "travelers": self._extract_travelers(user_input),
            "preferences": self._extract_preferences(user_input),
            "accommodation_type": self._extract_accommodation(user_input),
            "transportation": self._extract_transportation(user_input),
            "activities": self._extract_activities(user_input),
            "special_requirements": self._extract_special_requirements(user_input)
        }
        
        # Enhance with intent-based defaults
        if not extracted["preferences"]:
            extracted["preferences"] = self._get_default_preferences(intent_result["primary_intent"])
        
        return extracted
    
    def decide_tools(self, extracted_data: Dict[str, Any], intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Decide which tools and APIs to use"""
        tools_needed = []
        apis_needed = []
        
        # Core tools always needed
        tools_needed.extend(["general_search", "data_validation"])
        apis_needed.extend(["google_search_api"])
        
        # Destination-based tools
        if extracted_data["destination"]:
            tools_needed.extend(["flight_search", "hotel_search"])
            apis_needed.extend(["amadeus_api", "booking_api", "expedia_api"])
        
        # Weather tools
        if extracted_data["destination"] and extracted_data["duration"]:
            tools_needed.append("weather_forecast")
            apis_needed.append("openweather_api")
        
        # Budget analysis tools
        if extracted_data["budget"]:
            tools_needed.extend(["budget_calculator", "price_comparison"])
            apis_needed.extend(["currency_api", "cost_of_living_api"])
        
        # Activity-specific tools
        if extracted_data["activities"]:
            if any("museum" in act.lower() for act in extracted_data["activities"]):
                tools_needed.append("museum_finder")
                apis_needed.append("museum_api")
            
            if any("restaurant" in act.lower() or "food" in act.lower() for act in extracted_data["activities"]):
                tools_needed.append("restaurant_finder")
                apis_needed.append(["yelp_api", "google_places_api"])
        
        # Special requirement tools
        if extracted_data["special_requirements"]:
            if "accessibility" in str(extracted_data["special_requirements"]).lower():
                tools_needed.append("accessibility_checker")
                apis_needed.append("accessibility_api")
            
            if "visa" in str(extracted_data["special_requirements"]).lower():
                tools_needed.append("visa_checker")
                apis_needed.append("visa_api")
        
        return {
            "tools_required": list(set(tools_needed)),
            "apis_required": list(set(apis_needed)),
            "tool_priority": self._prioritize_tools(tools_needed, intent_result),
            "estimated_processing_time": self._estimate_processing_time(tools_needed),
            "data_sources": self._identify_data_sources(extracted_data)
        }
    
    def split_tasks(self, extracted_data: Dict[str, Any], tool_decisions: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Split into coordinated tasks for agents"""
        tasks = []
        
        # Research Agent Tasks
        if extracted_data["destination"]:
            tasks.append({
                "agent": "travel_researcher",
                "priority": "high",
                "task": f"Research destination: {extracted_data['destination']}",
                "tools": ["flight_search", "hotel_search", "general_search"],
                "estimated_time": "2-3 minutes",
                "dependencies": []
            })
        
        # Local Expert Tasks
        if extracted_data["preferences"] or extracted_data["activities"]:
            tasks.append({
                "agent": "local_vibe_expert",
                "priority": "high",
                "task": f"Find local experiences for: {', '.join(extracted_data.get('preferences', []))}",
                "tools": ["restaurant_finder", "museum_finder", "weather_forecast"],
                "estimated_time": "1-2 minutes",
                "dependencies": ["travel_researcher"]
            })
        
        # Budget Auditor Tasks
        if extracted_data["budget"]:
            tasks.append({
                "agent": "logic_auditor",
                "priority": "medium",
                "task": f"Validate budget constraints: {extracted_data['budget']}",
                "tools": ["budget_calculator", "price_comparison"],
                "estimated_time": "1 minute",
                "dependencies": ["travel_researcher", "local_vibe_expert"]
            })
        
        # Trip Manager Tasks
        tasks.append({
            "agent": "trip_manager",
            "priority": "high",
            "task": "Coordinate final itinerary and optimize schedule",
            "tools": ["data_validation", "itinerary_optimizer"],
            "estimated_time": "1-2 minutes",
            "dependencies": ["travel_researcher", "local_vibe_expert", "logic_auditor"]
        })
        
        return {
            "tasks": tasks,
            "total_estimated_time": self._calculate_total_time(tasks),
            "execution_order": self._determine_execution_order(tasks),
            "parallel_tasks": self._identify_parallel_tasks(tasks)
        }
    
    def generate_final_plan(self, extracted_data: Dict[str, Any], task_split: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Generate final structured travel plan"""
        return {
            "plan_type": "comprehensive_travel_plan",
            "summary": f"Travel plan for {extracted_data.get('destination', 'selected destination')} - {extracted_data.get('duration', 'duration specified')}",
            "key_components": {
                "destination": extracted_data.get("destination"),
                "duration": extracted_data.get("duration"),
                "budget": extracted_data.get("budget"),
                "travelers": extracted_data.get("travelers", "Not specified"),
                "preferences": extracted_data.get("preferences", []),
                "special_requirements": extracted_data.get("special_requirements", [])
            },
            "execution_strategy": {
                "approach": "multi_agent_coordination",
                "agents_involved": [task["agent"] for task in task_split["tasks"]],
                "estimated_completion": task_split["total_estimated_time"],
                "quality_assurance": "automated_validation"
            },
            "expected_outputs": [
                "Flight recommendations and pricing",
                "Hotel options with availability",
                "Day-by-day itinerary",
                "Budget breakdown and optimization",
                "Weather forecast and packing suggestions",
                "Local attractions and experiences"
            ]
        }
    
    # Helper methods for extraction and analysis
    def _extract_destination(self, text: str) -> str:
        """Extract destination from text"""
        # Common destination patterns
        patterns = [
            r'(?:to|in|visit|going to|travel to)\s+([A-Z][a-zA-Z\s]+,?\s*[A-Z]{2,3})',
            r'([A-Z][a-zA-Z\s]+),?\s*[A-Z]{2,3}',
            r'(?:destination|place|city|country):\s*([A-Z][a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"
    
    def _extract_budget(self, text: str) -> str:
        """Extract budget from text"""
        patterns = [
            r'\$?(\d{1,6}(?:,\d{3})*)\s*(?:dollars?|usd|budget)',
            r'budget\s*(?:of|is)?\s*\$?(\d{1,6}(?:,\d{3})*)',
            r'(?:spend|cost|price)\s*(?:up to)?\s*\$?(\d{1,6}(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
        
        return "Not specified"
    
    def _extract_duration(self, text: str) -> str:
        """Extract duration from text"""
        patterns = [
            r'(\d+)\s*(?:days?|d)',
            r'(\d+)\s*(?:weeks?|w)',
            r'(\d+)\s*(?:nights?)',
            r'from\s+(\d{1,2})/\d{1,2}/\d{2,4}\s+to\s+\d{1,2}/\d{1,2}/\d{2,4}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'week' in pattern:
                    return f"{match.group(1)} weeks"
                else:
                    return f"{match.group(1)} days"
        
        return "Not specified"
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s*\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates if dates else []
    
    def _extract_travelers(self, text: str) -> str:
        """Extract number/type of travelers"""
        patterns = [
            r'(\d+)\s*(?:people|person|travelers?|adults?)',
            r'(family|couple|solo|alone|group)',
            r'(?:with|for)\s+(?:my|our)?\s*(family|kids?|children|partner|spouse|friends?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Not specified"
    
    def _extract_preferences(self, text: str) -> List[str]:
        """Extract travel preferences"""
        preference_keywords = {
            "cultural": ["museum", "art", "culture", "historical", "heritage"],
            "adventure": ["adventure", "hiking", "sports", "extreme", "outdoor"],
            "food": ["food", "restaurant", "dining", "cuisine", "local food"],
            "relaxation": ["relax", "beach", "spa", "peaceful", "quiet"],
            "nightlife": ["nightlife", "bars", "clubs", "entertainment"],
            "shopping": ["shopping", "malls", "markets", "souvenirs"],
            "nature": ["nature", "parks", "wildlife", "scenic"],
            "luxury": ["luxury", "premium", "5-star", "deluxe", "high-end"]
        }
        
        found_preferences = []
        text_lower = text.lower()
        
        for preference, keywords in preference_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_preferences.append(preference)
        
        return found_preferences if found_preferences else ["general tourism"]
    
    def _extract_accommodation(self, text: str) -> str:
        """Extract accommodation preferences"""
        accommodation_types = {
            "hotel": ["hotel", "resort", "accommodation"],
            "apartment": ["apartment", "flat", "rental"],
            "hostel": ["hostel", "budget accommodation"],
            "villa": ["villa", "house", "rental house"],
            "resort": ["resort", "all-inclusive"]
        }
        
        text_lower = text.lower()
        for acc_type, keywords in accommodation_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return acc_type
        
        return "Not specified"
    
    def _extract_transportation(self, text: str) -> str:
        """Extract transportation preferences"""
        transport_types = {
            "flight": ["flight", "fly", "airplane", "air travel"],
            "train": ["train", "rail", "railway"],
            "car": ["car", "drive", "rental car", "road trip"],
            "bus": ["bus", "coach"],
            "cruise": ["cruise", "ship", "boat"]
        }
        
        text_lower = text.lower()
        for transport, keywords in transport_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return transport
        
        return "Not specified"
    
    def _extract_activities(self, text: str) -> List[str]:
        """Extract specific activities"""
        activities = []
        
        # Common activity patterns
        activity_patterns = [
            r'(?:visit|see|explore)\s+([a-zA-Z\s]+)',
            r'(?:go|do|try)\s+([a-zA-Z\s]+)',
            r'(?:interested in|want to|like)\s+([a-zA-Z\s]+)'
        ]
        
        for pattern in activity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            activities.extend([match.strip() for match in matches if len(match.strip()) > 2])
        
        return list(set(activities))  # Remove duplicates
    
    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special requirements"""
        requirements = []
        
        special_keywords = {
            "accessibility": ["wheelchair", "disabled", "accessibility", "special needs"],
            "visa": ["visa", "passport", "documentation"],
            "dietary": ["vegetarian", "vegan", "halal", "kosher", "gluten-free"],
            "medical": ["medical", "medication", "doctor", "hospital"],
            "pet": ["pet", "dog", "cat", "animal"]
        }
        
        text_lower = text.lower()
        for requirement, keywords in special_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                requirements.append(requirement)
        
        return requirements
    
    def _classify_travel_type(self, text: str) -> str:
        """Classify type of travel"""
        if any(word in text for word in ["business", "work", "conference"]):
            return "business"
        elif any(word in text for word in ["family", "kids", "children"]):
            return "family"
        elif any(word in text for word in ["romantic", "anniversary", "honeymoon"]):
            return "romantic"
        elif any(word in text for word in ["adventure", "extreme", "sports"]):
            return "adventure"
        else:
            return "leisure"
    
    def _detect_urgency(self, text: str) -> str:
        """Detect urgency level"""
        urgent_words = ["urgent", "asap", "immediately", "soon", "quickly"]
        if any(word in text.lower() for word in urgent_words):
            return "high"
        elif any(word in text.lower() for word in ["soon", "this week", "next week"]):
            return "medium"
        else:
            return "low"
    
    def _assess_complexity(self, text: str) -> str:
        """Assess complexity of request"""
        complexity_indicators = {
            "high": ["multi-city", "complex", "detailed", "comprehensive", "custom"],
            "medium": ["specific", "particular", "certain"],
            "low": ["simple", "basic", "general"]
        }
        
        text_lower = text.lower()
        for complexity, keywords in complexity_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                return complexity
        
        return "medium"
    
    def _get_default_preferences(self, intent: str) -> List[str]:
        """Get default preferences based on intent"""
        defaults = {
            "business_trip": ["efficient schedule", "business amenities", "conference facilities"],
            "romantic_getaway": ["romantic dining", "scenic views", "couple activities"],
            "family_vacation": ["family-friendly", "kids activities", "safe neighborhoods"],
            "adventure_travel": ["outdoor activities", "adventure sports", "nature"],
            "cultural_tourism": ["museums", "historical sites", "cultural experiences"],
            "luxury_travel": ["luxury hotels", "fine dining", "premium experiences"]
        }
        
        return defaults.get(intent, ["general tourism", "local experiences"])
    
    def _prioritize_tools(self, tools: List[str], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize tools based on intent and requirements"""
        priority_weights = {
            "flight_search": 10,
            "hotel_search": 10,
            "weather_forecast": 8,
            "budget_calculator": 7,
            "restaurant_finder": 6,
            "museum_finder": 5,
            "general_search": 4
        }
        
        prioritized = []
        for tool in set(tools):
            prioritized.append({
                "tool": tool,
                "priority": priority_weights.get(tool, 1),
                "reason": self._get_tool_reason(tool, intent)
            })
        
        return sorted(prioritized, key=lambda x: x["priority"], reverse=True)
    
    def _get_tool_reason(self, tool: str, intent: Dict[str, Any]) -> str:
        """Get reason for using a specific tool"""
        reasons = {
            "flight_search": "Essential for transportation planning",
            "hotel_search": "Required for accommodation booking",
            "weather_forecast": "Important for packing and activity planning",
            "budget_calculator": "Critical for cost management",
            "restaurant_finder": "Enhances dining experience",
            "museum_finder": "Supports cultural interests",
            "general_search": "Provides comprehensive destination information"
        }
        return reasons.get(tool, "Supports travel planning process")
    
    def _estimate_processing_time(self, tools: List[str]) -> str:
        """Estimate total processing time"""
        time_per_tool = {
            "flight_search": 30,
            "hotel_search": 25,
            "weather_forecast": 10,
            "budget_calculator": 15,
            "restaurant_finder": 20,
            "museum_finder": 15,
            "general_search": 10
        }
        
        total_time = sum(time_per_tool.get(tool, 10) for tool in tools)
        return f"{total_time} seconds"
    
    def _identify_data_sources(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Identify potential data sources"""
        sources = ["Google Search API", "OpenStreetMap"]
        
        if extracted_data.get("destination"):
            sources.extend(["Amadeus GDS", "Booking.com", "Expedia"])
        
        if extracted_data.get("budget"):
            sources.append("Currency Exchange API")
        
        return list(set(sources))
    
    def _calculate_total_time(self, tasks: List[Dict[str, Any]]) -> str:
        """Calculate total estimated time for all tasks"""
        # Extract time in minutes and sum up
        total_minutes = 0
        for task in tasks:
            time_str = task.get("estimated_time", "1 minute")
            if "minute" in time_str:
                minutes = int(re.search(r'(\d+)', time_str).group(1))
                total_minutes += minutes
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _determine_execution_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Determine optimal execution order"""
        # Simple dependency-based ordering
        order = []
        remaining_tasks = tasks.copy()
        
        # Add tasks with no dependencies first
        for task in remaining_tasks:
            if not task.get("dependencies"):
                order.append(task["agent"])
                remaining_tasks.remove(task)
        
        # Add remaining tasks
        for task in remaining_tasks:
            order.append(task["agent"])
        
        return order
    
    def _identify_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[List[str]]:
        """Identify tasks that can run in parallel"""
        # Tasks with no dependencies can run in parallel
        parallel_tasks = []
        no_dep_tasks = [task["agent"] for task in tasks if not task.get("dependencies")]
        
        if len(no_dep_tasks) > 1:
            parallel_tasks.append(no_dep_tasks)
        
        return parallel_tasks
    
    def get_fallback_response(self, user_input: str) -> Dict[str, Any]:
        """Fallback response when processing fails"""
        return {
            "success": False,
            "error": "Natural language processing failed",
            "fallback_data": {
                "destination": self._extract_destination(user_input),
                "budget": self._extract_budget(user_input),
                "duration": self._extract_duration(user_input),
                "preferences": ["general tourism"]
            },
            "processing_pipeline": {
                "step_1_intent": {"primary_intent": "travel_planning", "confidence": 0.5},
                "step_2_extraction": {},
                "step_3_tools": {"tools_required": ["general_search"]},
                "step_4_tasks": {"tasks": []},
                "step_5_plan": {}
            }
        }
