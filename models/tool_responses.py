from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class DataSource(str, Enum):
    SERPERDEV = "serperdev"
    OPENWEATHER = "openweather"
    MOCK = "mock"

class ResponseType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    WEATHER = "weather"
    GENERAL = "general"

class BaseToolResponse(BaseModel):
    """Base response for all tool outputs"""
    type: ResponseType
    source: DataSource
    success: bool
    message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class FlightResponse(BaseToolResponse):
    """Structured flight response"""
    type: ResponseType = ResponseType.FLIGHT
    airline: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    duration: Optional[str] = None
    flight_type: Optional[str] = None
    source_location: Optional[str] = None
    destination: Optional[str] = None
    notes: Optional[str] = None
    booking_url: Optional[str] = None

class HotelResponse(BaseToolResponse):
    """Structured hotel response"""
    type: ResponseType = ResponseType.HOTEL
    name: Optional[str] = None
    price_per_night: Optional[str] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    amenities: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    verified: Optional[bool] = None
    booking_url: Optional[str] = None
    hotel_type: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None

class WeatherResponse(BaseToolResponse):
    """Structured weather response"""
    type: ResponseType = ResponseType.WEATHER
    location: Optional[str] = None
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    pressure: Optional[int] = None
    description: Optional[str] = None
    wind_speed: Optional[float] = None
    visibility: Optional[float] = None
    uv_index: Optional[float] = None

class SearchResponse(BaseToolResponse):
    """General search response"""
    type: ResponseType = ResponseType.GENERAL
    query: Optional[str] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total_results: Optional[int] = None
    search_time: Optional[float] = None

class ToolError(BaseModel):
    """Standardized error response"""
    error_type: str
    message: str
    api_source: Optional[str] = None
    status_code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
