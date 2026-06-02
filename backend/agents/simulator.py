import random
import datetime
from typing import List
from models import TransportOption, AccommodationOption, Coordinates, Review, LocationDetail, Activity, DestinationSummary, PackageOffer

class ExternalServicesSimulator:
    def fetch_transport(self, origin: str, destination: str, date: str, budget: float, is_budget_pref: bool) -> List[TransportOption]:
        st_origin = origin[:3].upper() if len(origin) >= 3 else "DEL"
        st_dest = destination[:3].upper() if len(destination) >= 3 else "GOI"
        
        try:
             parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
             date_str = parsed_date.strftime("%y%m%d")
        except:
             date_str = "241225"
             
        skyscanner_url = f"https://www.skyscanner.co.in/transport/flights/{st_origin.lower()}/{st_dest.lower()}/{date_str}/?adults=1"
        ixigo_url = f"https://www.ixigo.com/trains/train-running-status"
        
        # Origin/Dest Mock Coordinates for Maps
        o_lat, o_lng = 28.61, 77.20
        d_lat, d_lng = 15.29, 74.12
        if destination.lower() != "goa":
            d_lat += 5; d_lng += 5

        flight_points = [Coordinates(lat=o_lat, lng=o_lng), Coordinates(lat=d_lat, lng=d_lng)]

        options = []
        # Flights
        options.append(TransportOption(type="Flight", provider="IndiGo Non-Stop", cost=4500, duration="2h 15m", departure="06:00 AM", arrival="08:15 AM", skyscanner_link=skyscanner_url, points=flight_points))
        options.append(TransportOption(type="Flight", provider="Air India", cost=5200, duration="2h 30m", departure="10:30 AM", arrival="01:00 PM", skyscanner_link=skyscanner_url, points=flight_points))
        options.append(TransportOption(type="Flight", provider="Vistara Premium", cost=6800, duration="2h 20m", departure="04:00 PM", arrival="06:20 PM", skyscanner_link=skyscanner_url, points=flight_points))
        
        # Trains
        options.append(TransportOption(type="Train", provider="Rajdhani Express (12431)", cost=1800, duration="12h 00m", departure="08:00 PM", arrival="08:00 AM", skyscanner_link=ixigo_url, points=flight_points))
        options.append(TransportOption(type="Train", provider="Shatabdi Fast (12011)", cost=1200, duration="14h 30m", departure="06:00 AM", arrival="08:30 PM", skyscanner_link=ixigo_url, points=flight_points))
        options.append(TransportOption(type="Train", provider="Garib Rath (12111)", cost=800, duration="16h 00m", departure="11:00 PM", arrival="03:00 PM", skyscanner_link=ixigo_url, points=flight_points))
        
        # Buses
        options.append(TransportOption(type="Bus", provider="IntrCity SmartBus Volvo", cost=1100, duration="14h", departure="09:00 PM", arrival="11:00 AM", skyscanner_link="https://www.redbus.in/", points=flight_points))
        options.append(TransportOption(type="Bus", provider="ZingBus AC Sleeper", cost=950, duration="15h", departure="10:00 PM", arrival="01:00 PM", skyscanner_link="https://www.redbus.in/", points=flight_points))
        options.append(TransportOption(type="Bus", provider="Orange Travels", cost=1300, duration="13h 30m", departure="08:30 PM", arrival="10:00 AM", skyscanner_link="https://www.redbus.in/", points=flight_points))
        
        return options

    def fetch_accommodation(self, destination: str, category: str) -> List[AccommodationOption]:
        lat = 15.2993 if destination.lower() == "goa" else 28.6139
        lng = 74.1240 if destination.lower() == "goa" else 77.2090
        
        luxury_reviews = [Review(user="Rajesh M.", rating=5.0, comment="Absolutely marvelous experience! The spa is top-notch.")]
        budget_reviews = [Review(user="Sam K.", rating=4.0, comment="Clean beds, good WiFi. Perfect for backpackers.")]

        options = [
            AccommodationOption(
                id="acc_lux_1", name=f"Taj {destination.capitalize()} Resort", type="5 Star Resort",
                cost_per_night=12000, rating=4.9, amenities=["Infinity Pool", "Spa", "Private Beach", "Fine Dining"],
                images=["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&auto=format&fit=crop"],
                coordinates=Coordinates(lat=lat, lng=lng), reviews=luxury_reviews
            ),
            AccommodationOption(
                id="acc_lux_2", name=f"Marriott {destination.capitalize()}", type="5 Star Hotel",
                cost_per_night=10500, rating=4.7, amenities=["Heated Pool", "Gym", "Lounge", "Valet"],
                images=["https://images.unsplash.com/photo-1517840901100-8179e982acb7?w=500&auto=format&fit=crop"],
                coordinates=Coordinates(lat=lat+0.02, lng=lng-0.01), reviews=luxury_reviews
            ),
            AccommodationOption(
                id="acc_bud_1", name=f"Zostel {destination.capitalize()}", type="Hostel",
                cost_per_night=800, rating=4.5, amenities=["Free WiFi", "AC", "Common Area"],
                images=["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=500&auto=format&fit=crop"],
                coordinates=Coordinates(lat=lat+0.01, lng=lng-0.01), reviews=budget_reviews
            ),
            AccommodationOption(
                id="acc_mid_1", name=f"Lemon Tree {destination.capitalize()}", type="4 Star Hotel",
                cost_per_night=3500, rating=4.3, amenities=["Pool", "Breakfast Included", "Gym"],
                images=["https://images.unsplash.com/photo-1522798514-97ceb8c4f1c8?w=500&auto=format&fit=crop"],
                coordinates=Coordinates(lat=lat-0.02, lng=lng+0.01), reviews=luxury_reviews
            )
        ]
        
        if category == "luxury":
            return [o for o in options if "5 Star" in o.type]
        elif category == "budget":
            return [o for o in options if "Hostel" in o.type]
        else:
            return options

    def fetch_activities(self, destination: str, category: str) -> List[dict]:
        lat = 15.2993 if destination.lower() == "goa" else 28.6139
        lng = 74.1240 if destination.lower() == "goa" else 77.2090
        
        return [
            {"name": "Heritage Walk", "cost": 0, "duration": "2h", "lat": lat+0.03, "lng": lng+0.02},
            {"name": "Boat Cruise with Music", "cost": 1500, "duration": "3h", "lat": lat-0.05, "lng": lng-0.03},
            {"name": "Scuba Diving", "cost": 3500, "duration": "4h", "lat": lat-0.08, "lng": lng-0.05},
            {"name": "Local Market Spices Tour", "cost": 500, "duration": "2h", "lat": lat, "lng": lng},
            {"name": "Sunset Viewpoint Dinner", "cost": 2500, "duration": "3h", "lat": lat+0.01, "lng": lng-0.06}
        ]

    def fetch_location_detail(self, destination: str) -> LocationDetail:
        return LocationDetail(
            name=destination.capitalize(),
            description=f"A mesmerizing journey awaits in {destination}. Known for its vibrant culture, stunning landscapes, and unforgettable experiences.",
            best_time="October to March",
            images=["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop"],
            top_attractions=["Beaches", "Historic Forts", "Night Markets", "Temples"]
        )

    def fetch_trending_destinations(self) -> List[DestinationSummary]:
        return [
            DestinationSummary(id="d1", name="Goa", snippet="Sunny beaches & vibrant nightlife", rating=4.6, image="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600&auto=format&fit=crop"),
            DestinationSummary(id="d2", name="Manali", snippet="Snow-capped Himalayan peaks", rating=4.8, image="https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=600&auto=format&fit=crop"),
            DestinationSummary(id="d3", name="Kerala", snippet="God's own backwaters", rating=4.9, image="https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600&auto=format&fit=crop"),
            DestinationSummary(id="d4", name="Jaipur", snippet="Pink city of royal palaces", rating=4.7, image="https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?w=600&auto=format&fit=crop"),
            DestinationSummary(id="d5", name="Varanasi", snippet="Spiritual heart of India", rating=4.5, image="https://images.unsplash.com/photo-1561361058-c24e0b84d00c?w=600&auto=format&fit=crop"),
            DestinationSummary(id="d6", name="Leh", snippet="High altitude adventure & stargazing", rating=4.8, image="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&auto=format&fit=crop"),
        ]

    def fetch_offers(self) -> List[PackageOffer]:
        return [
            PackageOffer(id="o1", title="Summer Sale on Domestic Flights", discount="Up to 15% OFF", image="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500&auto=format&fit=crop"),
            PackageOffer(id="o2", title="Luxury Resorts Deal", discount="Flat 20% OFF", image="https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=500&auto=format&fit=crop")
        ]

simulator = ExternalServicesSimulator()
