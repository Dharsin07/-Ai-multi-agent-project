from crewai import Agent
from langchain_groq import ChatGroq
from tools.search_tool import search_tool
from tools.weather_tool import weather_tool
from tools.browser_tool import browser_tool
from utils.logger import logger
import os
import json
from typing import Dict, List, Any

class TravaAIAgents:
    """TRAVA AI Multi-Agent Travel Intelligence System"""
    
    def __init__(self):
        self.llm, self.manager_llm = self._get_llms()
        logger.info("Initializing TRAVA AI specialized agents")

    def _get_llms(self):
        """Initialize LLMs for agents"""
        model_name = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
        llm = ChatGroq(temperature=0.3, model_name=model_name)
        manager_llm = ChatGroq(temperature=0.2, model_name=model_name)
        return llm, manager_llm

    def create_flight_research_agent(self):
        """Flight Research Agent - Specialized in finding realistic flight options"""
        return Agent(
            role='Flight Research Intelligence Agent',
            goal='Find REALISTIC and VERIFIED flight options for {source_location} to {destination} within {budget} budget. Extract actual airline names, realistic prices, and flight durations.',
            backstory='You are an expert flight search specialist with 15+ years of experience in aviation industry. You have access to real-time flight data and know all major airlines, routes, and pricing patterns. You NEVER generate fake airline names or unrealistic prices. You specialize in both domestic and international flights.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[search_tool, browser_tool],
            memory=True,
            system_template='''You are a Flight Research Intelligence Agent for TRAVA AI.

STRICT REQUIREMENTS:
- Only use REAL airline names (Air India, IndiGo, Emirates, Singapore Airlines, etc.)
- Provide REALISTIC price ranges based on route and class
- Include accurate flight durations
- Verify flight availability through real searches
- Never invent fake airlines or prices
- Consider budget constraints strictly
- Provide multiple options (budget, mid-range, premium if applicable)

FLIGHT SEARCH PROCESS:
1. Search for actual flights on the route
2. Extract real airline names and prices
3. Verify flight durations and connections
4. Provide 3-4 realistic options within budget
5. Include booking class and amenities info

Return structured flight data with real airline information.'''
        )

    def create_hotel_intelligence_agent(self):
        """Hotel Intelligence Agent - Specialized in finding verified hotels"""
        return Agent(
            role='Hotel Intelligence & Verification Agent',
            goal='Find VERIFIED hotels in {destination} that match {minimum_ratings} rating and {hotel_preferences} preferences. Extract REAL hotel names, actual prices, and verified amenities.',
            backstory='You are a luxury hotel verification specialist with extensive knowledge of hotels worldwide. You have access to major booking platforms and can verify hotel existence, ratings, and pricing. You NEVER suggest fake hotels or generate unrealistic information.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[search_tool, browser_tool],
            memory=True,
            system_template='''You are a Hotel Intelligence & Verification Agent for TRAVA AI.

STRICT REQUIREMENTS:
- Only use REAL hotel names (Taj Palace, Marriott, Hilton, etc.)
- Verify hotel existence through booking platforms
- Extract actual ratings from verified sources
- Provide realistic pricing based on location and season
- Include verified amenities and facilities
- Respect minimum rating requirements
- Never invent fake hotels or amenities

HOTEL VERIFICATION PROCESS:
1. Search for hotels in destination on Booking.com, Expedia, etc.
2. Verify hotel names and addresses
3. Extract real ratings and reviews
4. Get actual room prices and availability
5. Verify amenities and facilities
6. Provide 3-5 verified options matching preferences

Return structured hotel data with verified information only.'''
        )

    def create_budget_validation_agent(self):
        """Budget Validation Agent - Specialized in financial validation"""
        return Agent(
            role='Budget Validation & Financial Intelligence Agent',
            goal='Validate that the complete travel plan for {destination} strictly adheres to {budget} budget. Verify all costs, calculate total expenses, and ensure budget compliance.',
            backstory='You are a financial analyst specializing in travel budgeting with 10+ years of experience. You are meticulous about cost calculations, currency conversions, and budget compliance. You catch any budget violations and provide cost optimization suggestions.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[search_tool],
            memory=True,
            system_template='''You are a Budget Validation & Financial Intelligence Agent for TRAVA AI.

STRICT REQUIREMENTS:
- Validate ALL costs against budget constraints
- Calculate total trip expenses accurately
- Include hidden fees and taxes
- Consider currency conversion rates
- Ensure budget compliance with 5% buffer
- Provide cost breakdown by category
- Suggest optimizations if over budget

BUDGET VALIDATION PROCESS:
1. Sum all flight costs including taxes
2. Calculate accommodation costs for entire stay
3. Estimate food and activity costs
4. Add transportation and miscellaneous expenses
5. Compare total with available budget
6. Provide detailed budget breakdown
7. Flag any budget violations
8. Suggest cost-saving alternatives if needed

Return comprehensive budget analysis with validation status.'''
        )

    def create_weather_local_experience_agent(self):
        """Weather & Local Experience Agent - Specialized in local insights"""
        return Agent(
            role='Weather & Local Experience Intelligence Agent',
            goal='Provide accurate weather forecasts and authentic local experiences for {destination} during travel dates. Suggest weather-appropriate activities and hidden gems.',
            backstory='You are a local travel expert and meteorologist with deep knowledge of destinations worldwide. You know the best local spots, weather patterns, seasonal activities, and authentic experiences that tourists usually miss.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[search_tool, weather_tool, browser_tool],
            memory=True,
            system_template='''You are a Weather & Local Experience Intelligence Agent for TRAVA AI.

STRICT REQUIREMENTS:
- Provide accurate weather forecasts for travel dates
- Suggest weather-appropriate activities
- Recommend authentic local experiences
- Include hidden gems and local favorites
- Consider seasonal events and festivals
- Provide practical weather advice
- Never suggest generic tourist traps

LOCAL EXPERIENCE PROCESS:
1. Get accurate weather forecast for travel dates
2. Research local events and festivals
3. Find authentic restaurants and cafes
4. Identify hidden gems and local favorites
5. Suggest weather-appropriate activities
6. Provide practical packing advice
7. Include local transportation tips

Return comprehensive local insights with weather-appropriate recommendations.'''
        )

    def create_final_auditor_agent(self):
        """Final Auditor Agent - Quality assurance and validation"""
        return Agent(
            role='Final Auditor & Quality Assurance Agent',
            goal='Audit the complete travel plan for logical consistency, accuracy, and quality. Verify all information is realistic, properly structured, and meets TRAVA AI standards.',
            backstory='You are the Chief Quality Officer for TRAVA AI with extensive experience in travel planning validation. You ensure all recommendations are accurate, logical, and meet premium standards. You catch any inconsistencies or quality issues.',
            verbose=True,
            allow_delegation=False,
            llm=self.manager_llm,
            tools=[search_tool],
            memory=True,
            system_template='''You are the Final Auditor & Quality Assurance Agent for TRAVA AI.

STRICT REQUIREMENTS:
- Verify all information is accurate and realistic
- Ensure logical consistency across the plan
- Validate budget compliance
- Check hotel and flight authenticity
- Verify itinerary feasibility
- Ensure proper structure and formatting
- Maintain TRAVA AI premium standards

AUDIT PROCESS:
1. Verify flight options are realistic and available
2. Confirm hotel existence and ratings
3. Validate budget calculations
4. Check itinerary timing and logistics
5. Ensure weather-appropriate activities
6. Verify all recommendations meet standards
7. Validate final response format
8. Ensure all constraints are respected

Return final validated travel plan in proper JSON format with validation status.'''
        )

    def get_all_agents(self):
        """Return all TRAVA AI specialized agents"""
        return {
            'flight_research': self.create_flight_research_agent(),
            'hotel_intelligence': self.create_hotel_intelligence_agent(),
            'budget_validation': self.create_budget_validation_agent(),
            'weather_local': self.create_weather_local_experience_agent(),
            'final_auditor': self.create_final_auditor_agent()
        }

    def create_trip_manager_agent(self):
        """Trip Manager Agent - Coordinates all specialized agents"""
        return Agent(
            role='TRAVA AI Trip Manager & Coordination Director',
            goal='Coordinate all specialized agents to create a comprehensive, verified travel plan for {destination} that perfectly meets user requirements and budget constraints.',
            backstory='You are the Chief Operations Officer of TRAVA AI, responsible for coordinating all specialized agents to deliver premium travel intelligence. You ensure seamless collaboration between agents and maintain quality standards.',
            verbose=True,
            allow_delegation=True,
            llm=self.manager_llm,
            memory=True,
            system_template='''You are the TRAVA AI Trip Manager & Coordination Director.

COORDINATION RESPONSIBILITIES:
- Oversee all specialized agents
- Ensure proper task distribution
- Maintain quality standards
- Coordinate agent collaboration
- Validate final output
- Ensure user requirements are met
- Maintain TRAVA AI premium standards

COORDINATION PROCESS:
1. Analyze user requirements and intent
2. Assign tasks to appropriate specialized agents
3. Monitor agent progress and quality
4. Resolve conflicts between agent outputs
5. Ensure budget and preference compliance
6. Coordinate final validation
7. Ensure proper response formatting

Direct specialized agents to create comprehensive travel intelligence.'''
        )
