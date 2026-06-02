from pydantic import BaseModel
from typing import List, Optional, Dict

class UserPreferences(BaseModel):
    category: str  # luxury, budget, adventure, cultural
    flexibility: bool
    dietary: Optional[str] = None

class UserInput(BaseModel):
    origin: str = "DEL" # Default origin New Delhi
    destination: str
    start_date: str
    end_date: str
    budget: float
    preferences: UserPreferences

class Coordinates(BaseModel):
    lat: float
    lng: float

class TransportOption(BaseModel):
    type: str  # flight, train, bus
    provider: str
    cost: float
    duration: str
    departure: str
    arrival: str
    points: List[Coordinates] = []
    skyscanner_link: Optional[str] = None # Added for real-time tracking

class Review(BaseModel):
    user: str
    rating: float
    comment: str

class AccommodationOption(BaseModel):
    id: str
    name: str
    type: str
    cost_per_night: float
    rating: float
    amenities: List[str]
    images: List[str]
    coordinates: Coordinates
    reviews: List[Review]

class Activity(BaseModel):
    time: str
    description: str
    cost: float
    location: str
    coordinates: Optional[Coordinates] = None

class DayItinerary(BaseModel):
    day: int
    date: str
    activities: List[Activity]
    daily_cost: float

class LocationDetail(BaseModel):
    name: str
    description: str
    best_time: str
    images: List[str]
    top_attractions: List[str]

class TravelPlan(BaseModel):
    id: str
    origin: str = "DEL"
    destination: str
    total_estimated_cost: float
    budget_adherence: bool
    transport: TransportOption
    accommodation: AccommodationOption
    itinerary: List[DayItinerary]
    status: str 
    alternative_suggestions: List[str] = []
    location_details: Optional[LocationDetail] = None
    weather_forecast: Optional[Dict] = None

class DestinationSummary(BaseModel):
    id: str
    name: str
    image: str
    rating: float
    snippet: str

class PackageOffer(BaseModel):
    id: str
    title: str
    discount: str
    image: str
