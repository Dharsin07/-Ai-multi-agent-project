from crewai import Task
from models.schemas import FinalTravelPlan

def create_tasks(agents):
    """Creates and returns the tasks for the crew, enforcing structured outputs."""
    travel_researcher, local_vibe_expert, logic_auditor, _ = agents

    research_task = Task(
        description="Conduct thorough research for a {duration} trip to {destination} with a budget of {budget}. User preferences: {preferences}. Find current estimated costs for travel (from major cities) and accommodation. Identify the best modes of transport and reasonably priced stays that fit the budget dynamically.",
        expected_output="A comprehensive data compilation of flights and hotels that fit within the {budget} budget for a {duration} trip to {destination}.",
        agent=travel_researcher
    )

    itinerary_task = Task(
        description="Create a detailed, day-by-day itinerary for a {duration} trip to {destination}. Incorporate user preferences seamlessly: {preferences}. Include popular locations but focus heavily on hidden spots, unique cafes, and weather-appropriate activities based on current conditions. Provide markdown image links to venues where possible. Ensure the plan gives a true local 'vibe' experience.",
        expected_output="A detailed day-by-day {duration} itinerary with activities and estimated costs, mapped out logically.",
        agent=local_vibe_expert,
        context=[research_task]
    )

    validation_task = Task(
        description="Review the research findings and the generated itinerary for the {duration} trip to {destination} with a budget of {budget}. SELF-CORRECTION: Use your search tool to explicitly verify that the suggested hotels and cafes actually exist, are operational, and are within the price range found by the Researcher. Validate logical travel times between activities, and ensure all expenses plausibly fit within the {budget} budget. Adjust the itinerary if it's too packed, too expensive, or contains fabricated locations. Output MUST perfectly match the FinalTravelPlan JSON schema.",
        expected_output="A finalized, verified JSON object matching the FinalTravelPlan schema perfectly, with no extra text.",
        agent=logic_auditor,
        context=[research_task, itinerary_task],
        output_pydantic=FinalTravelPlan
    )

    return research_task, itinerary_task, validation_task
