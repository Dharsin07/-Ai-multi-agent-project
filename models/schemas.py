from pydantic import BaseModel, Field
from typing import List, Optional

class Flight(BaseModel):
    airline: str = Field(description="Name of the airline")
    price_estimate: str = Field(description="Estimated price of the flight")
    duration: str = Field(description="Estimated flight duration")
    notes: Optional[str] = Field(description="Any additional notes about the flight")

class Hotel(BaseModel):
    name: str = Field(description="Name of the hotel or accommodation")
    price_per_night: str = Field(description="Estimated price per night")
    rating: str = Field(description="Star rating or guest rating")
    amenities: List[str] = Field(description="Key amenities offered")
    booking_url_mock: Optional[str] = Field(description="Mock URL or search term for booking")

class Activity(BaseModel):
    time: str = Field(description="Time of the activity (e.g., 'Morning', '10:00 AM')")
    title: str = Field(description="Title of the activity")
    description: str = Field(description="Detailed description of what the user will do")
    cost_estimate: str = Field(description="Estimated cost of the activity")
    location: str = Field(description="Specific location or area")

class DailyItinerary(BaseModel):
    day: int = Field(description="Day number of the trip")
    theme: str = Field(description="Theme for the day (e.g., 'Historical Exploration')")
    activities: List[Activity] = Field(description="List of activities for the day")

class BudgetSummary(BaseModel):
    total_estimated_cost: str = Field(description="Total estimated cost of the entire trip")
    flights_cost: str = Field(description="Total estimated cost for flights")
    accommodation_cost: str = Field(description="Total estimated cost for accommodation")
    activities_food_cost: str = Field(description="Total estimated cost for activities and food")
    is_within_budget: bool = Field(description="Whether the total cost is within the user's budget")
    saving_tips: List[str] = Field(description="Tips on how to save money on this trip")

class FinalTravelPlan(BaseModel):
    destination: str = Field(description="The travel destination")
    duration: str = Field(description="Duration of the trip")
    flights: List[Flight] = Field(description="Recommended flight options")
    hotels: List[Hotel] = Field(description="Recommended hotel options")
    itinerary: List[DailyItinerary] = Field(description="Day-by-day itinerary")
    budget: BudgetSummary = Field(description="Comprehensive budget breakdown")
    weather_advisory: str = Field(description="Notes on expected weather and packing advice")
