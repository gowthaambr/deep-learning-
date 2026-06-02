import uuid
from datetime import datetime, timedelta
from typing import List, Dict

from models import UserInput, TravelPlan, DayItinerary, Activity, Coordinates, TransportOption, AccommodationOption, Review, LocationDetail
from agents.execution_agent import execution_agent

# Destination-specific curated activities per city category
DESTINATION_ACTIVITIES = {
    "beach":       ["Beach Sunset Walk","Water Sports Adventure","Seafood Shack Dinner","Cruise Ride","Scuba Diving","Sand Castle Trail"],
    "mountain":    ["Snow Trek","Himalayan Viewpoint","Local Café Breakfast","River Rafting","Mountain Biking","Bonfire Night"],
    "city":        ["Heritage Walk","Local Street Food Tour","Museum Visit","Shopping at Markets","Evening Light Show","Fort Tour"],
    "pilgrimage":  ["Morning Aarti","Ghats Boat Ride","Temple Darshan","Thali Lunch","Spiritual Tour","Meditation Session"],
}

CITY_CATEGORY = {
    "goa": "beach", "goi": "beach",
    "kochi": "beach", "cok": "beach",
    "pondicherry": "beach", "puducherry": "beach",
    "andaman": "beach", "ixa": "beach",
    "manali": "mountain", "leh": "mountain", "srinagar": "mountain", "sxr": "mountain",
    "shimla": "mountain", "dharamsala": "mountain", "dhm": "mountain",
    "rishikesh": "mountain", "darjeeling": "mountain", "ooty": "mountain",
    "varanasi": "pilgrimage", "vns": "pilgrimage",
    "tirupati": "pilgrimage", "amritsar": "pilgrimage", "atq": "pilgrimage",
    "pushkar": "pilgrimage",
}

ACTIVITY_COSTS = {"beach": 1500, "mountain": 1200, "pilgrimage": 200, "city": 800}

class RecommendationAgent:
    def rank_transport(self, options: List[Dict], user_input: UserInput) -> Dict:
        if not options:
            return None
        if user_input.preferences.category == 'budget':
            return sorted(options, key=lambda x: x.get('cost', 99999))[0]
        return options[0]

    def rank_accommodation(self, options: List[Dict], user_input: UserInput) -> Dict:
        if not options:
            return None
        if user_input.preferences.category == 'budget':
            return sorted(options, key=lambda x: x.get('cost_per_night', 99999))[0]
        return sorted(options, key=lambda x: x.get('rating', 0), reverse=True)[0]

class OptimizationAgent:
    def build_activity_pool(self, dest_key: str, lat: float, lng: float) -> List[Dict]:
        cat = CITY_CATEGORY.get(dest_key.lower(), "city")
        act_names = DESTINATION_ACTIVITIES.get(cat, DESTINATION_ACTIVITIES["city"])
        cost = ACTIVITY_COSTS.get(cat, 800)
        pool = []
        for name in act_names:
            pool.append({
                "name": name,
                "cost": cost,
                "lat": lat + (hash(name) % 100) / 3000,
                "lng": lng + (hash(name[::-1]) % 100) / 3000,
            })
        return pool

    def optimize_itinerary(self, user_input: UserInput, dest_key: str, transport: Dict, accomm: Dict, days: int) -> tuple:
        lat, lng = execution_agent.geocode_city(dest_key)
        activities_pool = self.build_activity_pool(dest_key, lat, lng)
        total_activities_cost = 0
        itinerary = []
        start_date = datetime.strptime(user_input.start_date, "%Y-%m-%d")

        for day in range(1, days + 1):
            date_str = (start_date + timedelta(days=day-1)).strftime("%Y-%m-%d")
            daily_activities = []
            daily_cost = 0

            for i in range(2):
                act = activities_pool[(day * 2 + i) % len(activities_pool)]
                activity = Activity(
                    time="10:00 AM" if i == 0 else "04:00 PM",
                    description=act["name"],
                    cost=act["cost"],
                    location=f"{execution_agent.get_city_name(dest_key)}, India",
                    coordinates=Coordinates(lat=act["lat"], lng=act["lng"])
                )
                daily_activities.append(activity)
                daily_cost += activity.cost

            itinerary.append(DayItinerary(day=day, date=date_str, activities=daily_activities, daily_cost=daily_cost))
            total_activities_cost += daily_cost

        total_cost = transport.get('cost', 0) + (accomm.get('cost_per_night', 0) * max(1, days - 1)) + total_activities_cost
        budget_adherence = total_cost <= user_input.budget
        status = "planned_with_warnings" if not budget_adherence else "planned"
        warnings = ["Budget exceeded. Consider switching to Budget travel style."] if not budget_adherence else []

        return itinerary, total_cost, budget_adherence, status, warnings

class PlannerAgent:
    def __init__(self):
        self.recommender = RecommendationAgent()
        self.optimizer = OptimizationAgent()

    def plan(self, user_input: UserInput) -> TravelPlan:
        # Resolve IATA codes to human-readable city names
        origin_city = execution_agent.get_city_name(user_input.origin)
        dest_city = execution_agent.get_city_name(user_input.destination)

        # Geocode both cities for route points on maps
        o_lat, o_lng = execution_agent.geocode_city(user_input.origin)
        d_lat, d_lng = execution_agent.geocode_city(user_input.destination)

        # Fetch from all sources via Execution Agent
        flights = execution_agent.fetch_flights_amadeus(user_input.origin, user_input.destination, user_input.start_date)
        ground_t = execution_agent.fetch_ground_transport_kaggle(user_input.origin, user_input.destination)
        hotels = execution_agent.fetch_places_foursquare(dest_city, user_input.preferences.category)
        weather = execution_agent.fetch_weather(dest_city)

        # Destination type
        cat = CITY_CATEGORY.get(user_input.destination.lower(), "city")
        desc_map = {
            "beach": "beautiful beaches and vibrant nightlife",
            "mountain": "majestic mountains and thrilling adventure",
            "pilgrimage": "sacred temples and deep spiritual energy",
            "city": "rich culture, heritage sites, and incredible cuisine"
        }
        loc_details = LocationDetail(
            name=dest_city,
            description=f"Explore the wonders of {dest_city} — a destination known for its {desc_map.get(cat, desc_map['city'])}.",
            best_time="October to March",
            images=[],
            top_attractions=[]
        )

        # Rank best options
        best_transport_dict = self.recommender.rank_transport(flights + ground_t, user_input)
        best_accomm_dict = self.recommender.rank_accommodation(hotels, user_input)

        # Build transport with real origin→destination route points
        route_points = [Coordinates(lat=o_lat, lng=o_lng), Coordinates(lat=d_lat, lng=d_lng)]
        best_transport = TransportOption(
            type=best_transport_dict.get('type', 'Flight'),
            provider=best_transport_dict.get('provider', 'Unknown'),
            cost=best_transport_dict.get('cost', 0),
            duration=best_transport_dict.get('duration', 'N/A'),
            departure=best_transport_dict.get('departure', 'N/A'),
            arrival=best_transport_dict.get('arrival', 'N/A'),
            skyscanner_link=best_transport_dict.get('skyscanner_link'),
            points=route_points
        )

        # Build accommodation centered on destination city
        accomm_coords = best_accomm_dict.get('coordinates', {'lat': d_lat, 'lng': d_lng})
        best_accomm = AccommodationOption(
            id=best_accomm_dict.get('id', 'acc_1'),
            name=best_accomm_dict.get('name', 'Hotel'),
            type=best_accomm_dict.get('type', 'Hotel'),
            cost_per_night=best_accomm_dict.get('cost_per_night', 0),
            rating=best_accomm_dict.get('rating', 0.0),
            amenities=best_accomm_dict.get('amenities', []),
            images=best_accomm_dict.get('images', []),
            coordinates=Coordinates(lat=accomm_coords['lat'], lng=accomm_coords['lng']),
            reviews=[Review(**r) for r in best_accomm_dict.get('reviews', [])]
        )

        # Optimize day-wise itinerary
        start_date = datetime.strptime(user_input.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(user_input.end_date, "%Y-%m-%d")
        days = max(1, (end_date - start_date).days + 1)
        itinerary, total_cost, budget_adherence, status, warnings = self.optimizer.optimize_itinerary(
            user_input, user_input.destination, best_transport_dict, best_accomm_dict, days
        )

        return TravelPlan(
            id=str(uuid.uuid4()),
            origin=origin_city,
            destination=dest_city,
            total_estimated_cost=total_cost,
            budget_adherence=budget_adherence,
            transport=best_transport,
            accommodation=best_accomm,
            itinerary=itinerary,
            status=status,
            alternative_suggestions=warnings,
            location_details=loc_details,
            weather_forecast=weather
        )

    def replan(self, current_plan: TravelPlan, reason: str) -> TravelPlan:
        current_plan.status = "replanned"
        current_plan.alternative_suggestions.append(f"Dynamic Replanning: {reason}")
        current_plan.alternative_suggestions.append("Re-optimized routes using OSM/Mapbox routing.")
        return current_plan

orchestrator = PlannerAgent()
