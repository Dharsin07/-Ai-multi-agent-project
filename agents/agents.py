from crewai import Agent
from langchain_groq import ChatGroq
from tools.search_tool import flight_search_tool, hotel_search_tool, general_search_tool
from tools.weather_tool import weather_tool
from tools.browser_tool import browser_tool
import os

def get_llms():
    """Initializes and returns the LLMs used by the agents."""
    model_name = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
    llm = ChatGroq(temperature=0.7, model_name=model_name)
    manager_llm = ChatGroq(temperature=0.5, model_name=model_name)
    return llm, manager_llm

def create_agents():
    """Creates and returns the crew agents."""
    llm, manager_llm = get_llms()

    travel_researcher = Agent(
        role='Expert Travel Researcher',
        goal='Find real-time flight trends, hotel prices, and travel information for {destination} using API-driven tools only.',
        backstory='You are a seasoned travel agent with years of experience using structured APIs to find the best deals on flights and hotels. You rely only on official API responses and never parse unstructured text.',
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[flight_search_tool, hotel_search_tool, general_search_tool],
        memory=True
    )

    local_vibe_expert = Agent(
        role='Local Vibe & Experience Expert',
        goal='Uncover hidden gems, local cafes, unique cultural spots, and weather-appropriate activities for {destination} using API-driven tools only. Carefully respect user preferences: {preferences}.',
        backstory='You are a well-traveled digital nomad and lifestyle blogger. You know all the best off-the-beaten-path spots, trendiest cafes, and authentic local experiences. You rely only on structured API responses and weather data.',
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[general_search_tool, weather_tool],
        memory=True
    )

    logic_auditor = Agent(
        role='Logistics & Budget Auditor',
        goal='Double-check travel times between spots, verify suggested hotels actually exist, and validate the itinerary fits the {budget} budget smoothly using API-driven tools only.',
        backstory='You are an ex-accountant turned travel auditor. You independently verify all hotel suggestions and prices using structured API responses. You make sure the travel plans are realistic, locations exist, and catch logistical errors before they happen.',
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[general_search_tool],
        memory=True
    )

    custom_manager = Agent(
        role='Trip Manager & Itinerary Director',
        goal='Manage the crew to produce the highest quality {duration} itinerary for {destination} that perfectly adheres to the {budget} budget and user preferences: {preferences}.',
        backstory='You are the Director of a high-end luxury travel agency. You oversee a team of specialists and ensure that the final product presented to the client is flawless, logically sound, and perfectly tailored to their desires.',
        verbose=True,
        allow_delegation=True,
        llm=manager_llm
    )

    return travel_researcher, local_vibe_expert, logic_auditor, custom_manager
