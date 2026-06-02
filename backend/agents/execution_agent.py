import json
import requests
import os
import datetime
import random
from typing import List, Dict

# Comprehensive IATA code → (lat, lng, city_name) for all major Indian airports
IATA_TO_CITY = {
    # South India
    "chn": (13.0827, 80.2707, "Chennai"),
    "maa": (13.0827, 80.2707, "Chennai"),
    "blr": (12.9716, 77.5946, "Bangalore"),
    "bom": (19.0760, 72.8777, "Mumbai"),
    "hyd": (17.3850, 78.4867, "Hyderabad"),
    "cok": (10.0261, 76.3083, "Kochi"),
    "trv": (8.5241,  76.9366, "Thiruvananthapuram"),
    "ixm": (9.8252,  78.0937, "Madurai"),
    "vga": (16.5303, 80.7972, "Vijayawada"),
    "vtz": (17.7242, 83.2244, "Visakhapatnam"),
    # North India
    "del": (28.6139, 77.2090, "Delhi"),
    "ixi": (27.2999, 94.9257, "Dibrugarh"),
    "ixr": (23.3143, 85.3217, "Ranchi"),
    "pat": (25.5940, 85.0999, "Patna"),
    "lko": (26.8467, 80.9462, "Lucknow"),
    "bho": (23.2599, 77.4126, "Bhopal"),
    "nag": (21.1458, 79.0882, "Nagpur"),
    "pnq": (18.5204, 73.8567, "Pune"),
    "jai": (26.9124, 75.7873, "Jaipur"),
    "jdh": (26.2389, 73.0243, "Jodhpur"),
    "vns": (25.3176, 82.9739, "Varanasi"),
    "agr": (27.1767, 78.0081, "Agra"),
    "amd": (23.0225, 72.5714, "Ahmedabad"),
    "sxr": (34.0836, 74.7973, "Srinagar"),
    "leh": (34.1526, 77.5771, "Leh"),
    "atq": (31.6340, 74.8723, "Amritsar"),
    "dhm": (32.4685, 76.2635, "Dharamsala"),
    # East India
    "ccu": (22.5726, 88.3639, "Kolkata"),
    "gau": (26.1445, 91.7362, "Guwahati"),
    "bbi": (20.2961, 85.8245, "Bhubaneswar"),
    # West/Coastal India
    "goi": (15.3800, 73.8300, "Goa"),
    "ixg": (15.4590, 75.0099, "Belagavi"),
    "ixa": (11.7401, 92.7339, "Port Blair"),
    # Northeast
    "ixa": (11.7401, 92.7339, "Port Blair"),
    "dim": (25.7006, 93.7720, "Dimapur"),
    "shil": (25.5788, 91.8933, "Shillong"),
    # Common city name aliases
    "goa":         (15.2993, 74.1240, "Goa"),
    "delhi":       (28.6139, 77.2090, "Delhi"),
    "mumbai":      (19.0760, 72.8777, "Mumbai"),
    "bangalore":   (12.9716, 77.5946, "Bangalore"),
    "bengaluru":   (12.9716, 77.5946, "Bangalore"),
    "hyderabad":   (17.3850, 78.4867, "Hyderabad"),
    "chennai":     (13.0827, 80.2707, "Chennai"),
    "kolkata":     (22.5726, 88.3639, "Kolkata"),
    "pune":        (18.5204, 73.8567, "Pune"),
    "ahmedabad":   (23.0225, 72.5714, "Ahmedabad"),
    "jaipur":      (26.9124, 75.7873, "Jaipur"),
    "srinagar":    (34.0836, 74.7973, "Srinagar"),
    "kochi":       (10.0261, 76.3083, "Kochi"),
    "udaipur":     (24.5854, 73.7125, "Udaipur"),
    "agra":        (27.1767, 78.0081, "Agra"),
    "varanasi":    (25.3176, 82.9739, "Varanasi"),
    "amritsar":    (31.6340, 74.8723, "Amritsar"),
    "lucknow":     (26.8467, 80.9462, "Lucknow"),
    "bhubaneswar": (20.2961, 85.8245, "Bhubaneswar"),
    "guwahati":    (26.1445, 91.7362, "Guwahati"),
    "leh":         (34.1526, 77.5771, "Leh"),
    "rishikesh":   (30.0869, 78.2676, "Rishikesh"),
    "darjeeling":  (27.0410, 88.2663, "Darjeeling"),
    "shimla":      (31.1048, 77.1734, "Shimla"),
    "manali":      (32.2432, 77.1892, "Manali"),
    "mysuru":      (12.2958, 76.6394, "Mysuru"),
    "mysore":      (12.2958, 76.6394, "Mysuru"),
    "coorg":       (12.3375, 75.8069, "Coorg"),
    "ooty":        (11.4102, 76.6950, "Ooty"),
    "tirupati":    (13.6288, 79.4192, "Tirupati"),
    "mumbai":      (19.0760, 72.8777, "Mumbai"),
    "nasik":       (19.9975, 73.7898, "Nashik"),
    "nashik":      (19.9975, 73.7898, "Nashik"),
    "nagpur":      (21.1458, 79.0882, "Nagpur"),
    "jodhpur":     (26.2389, 73.0243, "Jodhpur"),
    "bikaner":     (28.0229, 73.3119, "Bikaner"),
    "pushkar":     (26.4899, 74.5511, "Pushkar"),
    "ranchi":      (23.3143, 85.3217, "Ranchi"),
    "patna":       (25.5940, 85.0999, "Patna"),
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class ExecutionAgent:
    def __init__(self):
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.foursquare_api_key = os.getenv("FOURSQUARE_API_KEY", "")
        self.geo_cache = {}

    def geocode_city(self, city: str) -> tuple:
        key = city.strip().lower()
        if key in self.geo_cache:
            return self.geo_cache[key]

        # Step 1: Fast lookup from comprehensive IATA/city table
        if key in IATA_TO_CITY:
            lat, lng, _ = IATA_TO_CITY[key]
            self.geo_cache[key] = (lat, lng)
            return (lat, lng)

        # Step 2: OSM Nominatim free geocoding for any city in India
        try:
            headers = {"User-Agent": "AgenticTravelPlatform/1.0"}
            url = f"https://nominatim.openstreetmap.org/search?q={city},India&format=json&limit=1"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200 and len(res.json()) > 0:
                lat = float(res.json()[0]["lat"])
                lng = float(res.json()[0]["lon"])
                self.geo_cache[key] = (lat, lng)
                return (lat, lng)
        except Exception:
            pass

        # Step 3: Center of India as absolute last resort
        return (20.5937, 78.9629)

    def get_city_name(self, code: str) -> str:
        """Resolve IATA code or city name to a human-readable city name."""
        entry = IATA_TO_CITY.get(code.strip().lower())
        return entry[2] if entry else code.capitalize()

    def fetch_weather(self, destination: str) -> Dict:
        if self.openweather_api_key:
            try:
                res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={self.openweather_api_key}&units=metric")
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "temp": data["main"]["temp"],
                        "condition": data["weather"][0]["main"],
                        "description": data["weather"][0]["description"].title()
                    }
            except:
                pass
        return {"temp": 28.5, "condition": "Sunny", "description": "Clear skies with a gentle breeze."}

    def fetch_flights_amadeus(self, origin: str, dest: str, date: str) -> List[Dict]:
        o_lat, o_lng = self.geocode_city(origin)
        d_lat, d_lng = self.geocode_city(dest)
        points = [{"lat": o_lat, "lng": o_lng}, {"lat": d_lat, "lng": d_lng}]
        
        skyscanner_url = f"https://www.skyscanner.co.in/transport/flights/{origin.lower()}/{dest.lower()}/{date.replace('-','')[2:]}/?adults=1"
        return [
            {"type": "Flight", "provider": "IndiGo Non-Stop (API Fallback)", "cost": 4500, "duration": "2h 15m", "departure": "06:00 AM", "arrival": "08:15 AM", "skyscanner_link": skyscanner_url, "points": points},
            {"type": "Flight", "provider": "Air India (API Fallback)", "cost": 5200, "duration": "2h 30m", "departure": "10:30 AM", "arrival": "01:00 PM", "skyscanner_link": skyscanner_url, "points": points},
            {"type": "Flight", "provider": "Vistara Premium", "cost": 6800, "duration": "2h 20m", "departure": "04:00 PM", "arrival": "06:20 PM", "skyscanner_link": skyscanner_url, "points": points}
        ]

    def fetch_ground_transport_kaggle(self, origin: str, dest: str) -> List[Dict]:
        o_lat, o_lng = self.geocode_city(origin)
        d_lat, d_lng = self.geocode_city(dest)
        points = [{"lat": o_lat, "lng": o_lng}, {"lat": d_lat, "lng": d_lng}]

        try:
            with open(os.path.join(DATA_DIR, "transport_kag.json"), "r") as f:
                records = json.load(f)
                # Overwrite the origin/dest coordinates dynamically so maps work for ANY city inputted
                for r in records:
                    r["points"] = points
                return [r for r in records if r["type"] in ["Train", "Bus"]]
        except Exception as e:
            return []

    def fetch_places_foursquare(self, destination: str, category: str) -> List[Dict]:
        lat, lng = self.geocode_city(destination)
        city_key = destination.strip().lower()

        # --- Rich city-specific hotel database ---
        city_hotels = {
            "goa": [
                {"name": "Taj Exotica Resort Goa", "type": "5 Star Beach Resort", "cost_per_night": 18000, "rating": 4.9, 
                 "amenities": ["Private Beach", "Infinity Pool", "Spa", "Scuba Diving", "Water Sports"],
                 "images": ["https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Priya S.", "rating": 5.0, "comment": "Stunning beachfront resort - pure luxury!"}]},
                {"name": "Alila Diwa Goa", "type": "5 Star Resort", "cost_per_night": 15000, "rating": 4.8,
                 "amenities": ["Rooftop Pool", "Ayurveda Spa", "Beach Shuttle", "Fine Dining"],
                 "images": ["https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Amit K.", "rating": 4.8, "comment": "Exceptional service and tranquil vibes."}]},
                {"name": "Zostel Goa Palolem", "type": "Hostel", "cost_per_night": 700, "rating": 4.5,
                 "amenities": ["Beach View", "Common Kitchen", "Free WiFi", "Party Nights"],
                 "images": ["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Sam M.", "rating": 4.5, "comment": "Best hostel in South Goa, great vibes!"}]},
                {"name": "Lemon Tree Amarante Goa", "type": "4 Star Hotel", "cost_per_night": 4500, "rating": 4.3,
                 "amenities": ["Pool", "Restaurant", "Gym", "Bar"],
                 "images": ["https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Riya T.", "rating": 4.3, "comment": "Great value for money, good location."}]},
            ],
            "delhi": [
                {"name": "The Leela Palace New Delhi", "type": "5 Star Palace Hotel", "cost_per_night": 22000, "rating": 4.9,
                 "amenities": ["Royal Spa", "Concierge", "Rooftop Dining", "Limousine Service"],
                 "images": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Rohit M.", "rating": 5.0, "comment": "Absolute royalty, worth every rupee!"}]},
                {"name": "ITC Maurya Delhi", "type": "5 Star Hotel", "cost_per_night": 18000, "rating": 4.8,
                 "amenities": ["Dum Pukht Restaurant", "Club Floor", "Pool", "Business Centre"],
                 "images": ["https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Anita R.", "rating": 4.8, "comment": "Iconic Delhi hotel with legendary cuisine."}]},
                {"name": "Ibis New Delhi Aerocity", "type": "3 Star Hotel", "cost_per_night": 3500, "rating": 4.2,
                 "amenities": ["Airport Shuttle", "Restaurant", "WiFi", "Gym"],
                 "images": ["https://images.unsplash.com/photo-1455587734955-081b22074882?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Kiran P.", "rating": 4.2, "comment": "Great for transit, near the airport."}]},
                {"name": "Zostel Delhi", "type": "Hostel", "cost_per_night": 600, "rating": 4.4,
                 "amenities": ["Metro Nearby", "Common Area", "Free Breakfast", "WiFi"],
                 "images": ["https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Leo F.", "rating": 4.4, "comment": "Super central location, amazing staff!"}]},
            ],
            "mumbai": [
                {"name": "The Taj Mahal Palace Mumbai", "type": "5 Star Heritage Hotel", "cost_per_night": 25000, "rating": 5.0,
                 "amenities": ["Gateway of India View", "Heritage Rooms", "Royal Spa", "Fine Dining"],
                 "images": ["https://images.unsplash.com/photo-1573052905904-34ad8c27f0cc?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Raj K.", "rating": 5.0, "comment": "A living piece of India's history!"}]},
                {"name": "Trident Nariman Point", "type": "5 Star Hotel", "cost_per_night": 16000, "rating": 4.7,
                 "amenities": ["Sea View", "Pool", "Conference Rooms", "Spa"],
                 "images": ["https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Meera L.", "rating": 4.7, "comment": "Unbeatable sea views from every room."}]},
                {"name": "Hotel Bawa International", "type": "3 Star Hotel", "cost_per_night": 2800, "rating": 4.0,
                 "amenities": ["Central Mumbai", "AC Rooms", "Restaurant"],
                 "images": ["https://images.unsplash.com/photo-1522798514-97ceb8c4f1c8?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Priya N.", "rating": 4.0, "comment": "Value for money in expensive Mumbai!"}]},
            ],
            "bangalore": [
                {"name": "The Oberoi Bengaluru", "type": "5 Star Hotel", "cost_per_night": 19000, "rating": 4.9,
                 "amenities": ["Lap Pool", "World-class Spa", "Italian Restaurant", "Business Suite"],
                 "images": ["https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Vikram S.", "rating": 4.9, "comment": "Best hotel in Bengaluru, impeccable service!"}]},
                {"name": "Lemon Tree Premier Bangalore", "type": "4 Star Hotel", "cost_per_night": 5500, "rating": 4.4,
                 "amenities": ["Pool", "Gym", "Citrus Café", "Bar"],
                 "images": ["https://images.unsplash.com/photo-1517840901100-8179e982acb7?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Divya M.", "rating": 4.4, "comment": "Modern, clean and great location in Whitefield."}]},
                {"name": "Zostel Bangalore", "type": "Hostel", "cost_per_night": 750, "rating": 4.6,
                 "amenities": ["Rooftop Hangout", "Free WiFi", "24/7 Reception", "Travel Desk"],
                 "images": ["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Alex H.", "rating": 4.6, "comment": "Great social atmosphere, highly recommend!"}]},
            ],
            "manali": [
                {"name": "Span Resort & Spa Manali", "type": "5 Star Mountain Resort", "cost_per_night": 12000, "rating": 4.7,
                 "amenities": ["River View", "Spa", "Bonfire", "River Rafting Desk"],
                 "images": ["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Tanya R.", "rating": 4.7, "comment": "Riverside luxury surrounded by mountains!"}]},
                {"name": "Snow Valley Resorts Manali", "type": "4 Star Mountain Resort", "cost_per_night": 7500, "rating": 4.5,
                 "amenities": ["Mountain View", "Hot Tub", "Ski Storage", "Fireplace"],
                 "images": ["https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Harsh G.", "rating": 4.5, "comment": "Beautiful snow views from the balcony!"}]},
                {"name": "Backpacker Panda Manali", "type": "Hostel", "cost_per_night": 800, "rating": 4.3,
                 "amenities": ["Campfire", "Himalayan Treks Desk", "Free Breakfast", "WiFi"],
                 "images": ["https://images.unsplash.com/photo-1615460549969-36fa19521a4f?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Priya L.", "rating": 4.3, "comment": "Central location, great for trekkers!"}]},
            ],
            "jaipur": [
                {"name": "Rambagh Palace Jaipur", "type": "5 Star Heritage Palace", "cost_per_night": 35000, "rating": 5.0,
                 "amenities": ["Royal Suites", "Polo Ground", "Peacock Garden", "Heritage Spa"],
                 "images": ["https://images.unsplash.com/photo-1609766418204-94aae0ecfdfc?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Nikhil J.", "rating": 5.0, "comment": "Living like Maharaja - absolutely royal!"}]},
                {"name": "Hotel Pearl Palace Jaipur", "type": "Budget Hotel", "cost_per_night": 1200, "rating": 4.5,
                 "amenities": ["Rooftop Restaurant", "Free WiFi", "Travel Desk", "Jeep Safari"],
                 "images": ["https://images.unsplash.com/photo-1600011689032-8b628b8a8747?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Emily T.", "rating": 4.5, "comment": "Best budget hotel in Jaipur, surpassed expectations!"}]},
            ],
            "varanasi": [
                {"name": "BrijRama Palace Varanasi", "type": "Heritage Boutique Hotel", "cost_per_night": 12000, "rating": 4.8,
                 "amenities": ["Ganga View", "Yoga Deck", "Heritage Rooms", "Boat Ride Included"],
                 "images": ["https://images.unsplash.com/photo-1587474260584-136574528ed5?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Sunanda P.", "rating": 4.8, "comment": "Waking up to the Ganga every morning is divine!"}]},
                {"name": "Ganges View Guesthouse", "type": "Budget Guesthouse", "cost_per_night": 900, "rating": 4.4,
                 "amenities": ["River Facing Rooms", "Indian Meals", "Yoga Sessions"],
                 "images": ["https://images.unsplash.com/photo-1518684079-3c830dcef090?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Mark L.", "rating": 4.4, "comment": "Authentic Varanasi experience, very peaceful!"}]},
            ],
            "kochi": [
                {"name": "Brunton Boatyard Kochi", "type": "5 Star Heritage Hotel", "cost_per_night": 14000, "rating": 4.8,
                 "amenities": ["Harbour View", "Infinity Pool", "Spice Restaurant", "Heritage Architecture"],
                 "images": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Meera V.", "rating": 4.8, "comment": "Malayalam charm with luxury - perfect Kochi stay!"}]},
                {"name": "Zostel Kochi Fort", "type": "Hostel", "cost_per_night": 650, "rating": 4.5,
                 "amenities": ["Fort Kochi Location", "Common Room", "Cooking Classes", "Heritage Walk"],
                 "images": ["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Arjun N.", "rating": 4.5, "comment": "Perfect base for exploring Fort Kochi!"}]},
            ],
            "chennai": [
                {"name": "ITC Grand Chola Chennai", "type": "5 Star Hotel", "cost_per_night": 17000, "rating": 4.8,
                 "amenities": ["Chola Architecture Theme", "Multiple Restaurants", "Luxury Spa", "Grand Pool"],
                 "images": ["https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Lakshmi S.", "rating": 4.8, "comment": "Inspired by Chola dynasty - stunningly grand!"}]},
                {"name": "Hotel Saravana Bhavan Chennai", "type": "3 Star Hotel", "cost_per_night": 2200, "rating": 4.2,
                 "amenities": ["Central Location", "South Indian Restaurant", "AC Rooms"],
                 "images": ["https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Ganesan R.", "rating": 4.2, "comment": "Clean, well-connected to bus station."}]},
            ],
            "hyderabad": [
                {"name": "Taj Falaknuma Palace Hyderabad", "type": "5 Star Palace Hotel", "cost_per_night": 45000, "rating": 5.0,
                 "amenities": ["Nizam's Palace", "Jade Room", "Zenana Pool", "Horse Carriage"],
                 "images": ["https://images.unsplash.com/photo-1605640840605-14ac1855827b?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Salman K.", "rating": 5.0, "comment": "The most majestic hotel in India - bar none!"}]},
                {"name": "Golkonda Hotel Hyderabad", "type": "4 Star Hotel", "cost_per_night": 5500, "rating": 4.3,
                 "amenities": ["Multiple Restaurants", "Pool", "Banquet Halls"],
                 "images": ["https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Fatima B.", "rating": 4.3, "comment": "Classic Hyderabad hotel, great Biryani downstairs!"}]},
            ],
        }

        # Determine best city key
        result_hotels = None
        for ckey in [city_key, city_key[:3]]:
            if ckey in city_hotels:
                result_hotels = city_hotels[ckey]
                break

        # If city not in our curated list, generate contextual hotels using coordinates + city name
        if not result_hotels:
            result_hotels = [
                {"name": f"Grand {destination.capitalize()} Palace", "type": "4 Star Hotel", "cost_per_night": 8000, "rating": 4.5,
                 "amenities": ["Pool", "Restaurant", "Gym", "WiFi"],
                 "images": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Local Guest", "rating": 4.5, "comment": "Comfortable stay with great local feel."}]},
                {"name": f"Heritage Inn {destination.capitalize()}", "type": "3 Star Hotel", "cost_per_night": 3500, "rating": 4.1,
                 "amenities": ["AC Rooms", "Breakfast", "Parking"],
                 "images": ["https://images.unsplash.com/photo-1455587734955-081b22074882?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Traveller X", "rating": 4.1, "comment": "Good value property, centrally located."}]},
                {"name": f"Zostel {destination.capitalize()}", "type": "Hostel", "cost_per_night": 700, "rating": 4.3,
                 "amenities": ["Free WiFi", "Common Kitchen", "Travel Desk"],
                 "images": ["https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&auto=format&fit=crop"],
                 "reviews": [{"user": "Backpacker Y", "rating": 4.3, "comment": "Great for budget travellers!"}]},
            ]

        # Apply category filter and inject real coordinates with slight jitter
        if category == "luxury":
            result_hotels = [h for h in result_hotels if "5 Star" in h["type"] or "Palace" in h["type"] or h["cost_per_night"] > 8000]
        elif category == "budget":
            result_hotels = [h for h in result_hotels if "Hostel" in h["type"] or "Budget" in h["type"] or h["cost_per_night"] < 3000]

        if not result_hotels:
            result_hotels = city_hotels.get(city_key, [])[:3] or result_hotels

        # Inject fresh geocoded coordinates with jitter so each hotel appears distinctly on the map
        for i, h in enumerate(result_hotels):
            h["id"] = f"hotel_{city_key}_{i}"
            h["coordinates"] = {"lat": round(lat + (i - 1) * 0.015, 6), "lng": round(lng + (i - 1) * 0.015, 6)}

        return result_hotels

    def fetch_dynamic_activities(self, destination: str) -> List[Dict]:
        lat, lng = self.geocode_city(destination)
        return [
            {"name": "Heritage City Walk", "cost": 0, "duration": "2h", "lat": lat + random.uniform(-0.02, 0.02), "lng": lng + random.uniform(-0.02, 0.02)},
            {"name": "Local Gastronomic Tour", "cost": 1500, "duration": "3h", "lat": lat + random.uniform(-0.03, 0.03), "lng": lng + random.uniform(-0.03, 0.03)},
            {"name": "Museum & Historic Site", "cost": 300, "duration": "4h", "lat": lat + random.uniform(-0.04, 0.04), "lng": lng + random.uniform(-0.04, 0.04)},
            {"name": "Market Spices Tour", "cost": 500, "duration": "2h", "lat": lat + random.uniform(-0.01, 0.01), "lng": lng + random.uniform(-0.01, 0.01)},
            {"name": "Sunset Viewpoint", "cost": 250, "duration": "3h", "lat": lat + random.uniform(-0.05, 0.05), "lng": lng + random.uniform(-0.05, 0.05)},
        ]

execution_agent = ExecutionAgent()

