from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import datetime

from models import UserInput, TravelPlan, DestinationSummary, PackageOffer
from agents.orchestrator import orchestrator
from agents.execution_agent import execution_agent
from agents.simulator import simulator

app = FastAPI(title="Agentic Travel Planning API (Free Tier Integrations)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_plans: Dict[str, TravelPlan] = {}

@app.post("/plan-trip", response_model=TravelPlan)
async def plan_trip(user_input: UserInput):
    plan = orchestrator.plan(user_input)
    db_plans[plan.id] = plan
    return plan

@app.post("/update-plan/{plan_id}", response_model=TravelPlan)
async def update_plan(plan_id: str, reason: str):
    if plan_id not in db_plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    current_plan = db_plans[plan_id]
    updated_plan = orchestrator.replan(current_plan, reason)
    db_plans[plan_id] = updated_plan
    return updated_plan

@app.get("/trending-destinations", response_model=List[DestinationSummary])
async def get_trending_destinations():
    return simulator.fetch_trending_destinations()

@app.get("/offers", response_model=List[PackageOffer])
async def get_offers():
    return simulator.fetch_offers()

@app.get("/search-transport")
async def search_transport(origin: str, destination: str, type: str):
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Utilizing Agent Execution layer
    flights = execution_agent.fetch_flights_amadeus(origin, destination, date)
    ground = execution_agent.fetch_ground_transport_kaggle(origin, destination)
    all_options = flights + ground
    
    filtered = [opt for opt in all_options if opt.get("type", "").lower() == type.lower()]
    return filtered

@app.get("/search-hotels")
async def search_hotels(destination: str):
    return execution_agent.fetch_places_foursquare(destination, "luxury") + execution_agent.fetch_places_foursquare(destination, "budget")

@app.get("/weather")
async def get_weather(destination: str):
    return execution_agent.fetch_weather(destination)

@app.get("/my-trips")
async def my_trips():
    return list(db_plans.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
