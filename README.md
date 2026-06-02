# Agentic Travel Planning and Execution System

An autonomous AI-driven system capable of planning, optimizing, and dynamically managing travel itineraries based on user-defined goals, constraints, and preferences.

## Features

- **Agentic Loop**: Employs an iterative Plan -> Act -> Observe -> Refine loop conceptually to build and re-optimize itineraries based on budget and user preferences.
- **Dynamic Replanning**: Ability to handle price surges and dynamically alter plans on the fly.
- **Budget Optimization**: Chooses optimal transportation and accommodation based on available budget constraints using simulated APIs.
- **Beautiful Interface**: Modern, responsive, glassmorphism UI offering a day-wise itinerary map and cost breakdowns.

## Tech Stack

- **Frontend**: Vite + React, TypeScript, Framer Motion, Vanilla CSS (Glassmorphism aesthetics).
- **Backend**: Python FastAPI, Pydantic.

## How to Run

1. **Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   # Ensure dependencies are installed: pip install fastapi uvicorn pydantic
   uvicorn main:app --reload --port 8000
   ```

2. **Frontend**:
   ```bash
   cd frontend
   # Ensure dependencies are installed: npm install
   npm run dev
   ```

## Demonstration
1. Open the frontend URL in your browser (usually `http://localhost:5173`).
2. Input `Goa` as destination, enter a budget of `10000` (₹) with `Budget` as the travel style.
3. Click **Generate Plan**. The Agent will output transport, accommodation, and day-wise itineraries that sum up correctly to respect constraints.
4. If you hit `Simulate Fluctuation & Re-optimize`, the system simulates a flight price surge, recalculates the budgets, adds relevant warnings and re-adjusts to the execution loop constraints.

Enjoy autonomous travel planning!
