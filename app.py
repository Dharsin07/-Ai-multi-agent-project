from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import json
import asyncio
from typing import Dict, Any, Optional
import os
from pathlib import Path

# Import our existing services
from services.working_crew_manager import WorkingCrewManager
from services.autonomous_booking_agent import AutonomousBookingAgent
from utils.logger import logger

app = FastAPI(title="TRAVA AI - Professional Travel Planning System", version="2.0")

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
crew_manager = WorkingCrewManager()
booking_agent = AutonomousBookingAgent()

class NaturalLanguageRequest(BaseModel):
    travel_plan: str
    request_type: str = "natural_language_planning"

class TravelRequest(BaseModel):
    destination: str
    budget: str
    duration: str
    preferences: str
    request_type: str = "travel_planning"

class AnalysisRequest(BaseModel):
    user_input: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Professional travel planning homepage"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-natural-language")
async def process_natural_language(request_data: NaturalLanguageRequest):
    """Process natural language travel request"""
    try:
        logger.info(f"Processing natural language request: {request_data.travel_plan[:100]}...")
        
        # Use the working crew manager
        result = crew_manager.run_travel_planning(request_data.travel_plan)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Error processing natural language request: {e}")
        return {"success": False, "error": str(e)}

@app.post("/analyze-request")
async def analyze_request(request_data: AnalysisRequest):
    """Analyze user request and determine which tools/APIs are needed"""
    try:
        # Use the autonomous booking agent for analysis
        result = booking_agent.process_travel_request(request_data.user_input)
        
        return {"success": True, "analysis": result}
        
    except Exception as e:
        logger.error(f"Error analyzing request: {e}")
        return {"success": False, "error": str(e)}

@app.post("/generate-travel-plan")
async def generate_travel_plan(request_data: TravelRequest):
    """Generate comprehensive travel plan using multi-agent system"""
    try:
        # Prepare inputs for the crew
        inputs = {
            "destination": request_data.destination,
            "budget": request_data.budget,
            "duration": request_data.duration,
            "preferences": request_data.preferences
        }
        
        logger.info(f"Generating travel plan for: {inputs}")
        
        # Execute the crew manager
        result = crew_manager.run_travel_planning(f"Plan a trip to {request_data.destination} with budget {request_data.budget} for {request_data.duration}")
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Error generating travel plan: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "TRAVA AI Travel Planning System"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
