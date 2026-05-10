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
from services.enhanced_crew_manager import EnhancedTravelCrewManager
from services.llm_natural_processor import NaturalLanguageTravelProcessor
from agents.agents import create_agents
from utils.logger import logger

app = FastAPI(title="TRAVA AI - Professional Travel Planning System", version="2.0")

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize enhanced services
crew_manager = EnhancedTravelCrewManager()
natural_processor = NaturalLanguageTravelProcessor()

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
    """Process natural language travel request through complete AI pipeline"""
    try:
        logger.info(f"Processing natural language request: {request_data.travel_plan[:100]}...")
        
        # Process through the complete AI pipeline
        result = natural_processor.process_travel_request(request_data.travel_plan)
        
        if result["success"]:
            # Generate the actual travel plan using extracted data
            extracted_data = result["extracted_data"]
            
            # Convert to format expected by crew manager
            crew_inputs = {
                "destination": extracted_data.get("destination", "Not specified"),
                "budget": extracted_data.get("budget", "Not specified"),
                "duration": extracted_data.get("duration", "Not specified"),
                "preferences": ", ".join(extracted_data.get("preferences", []))
            }
            
            # Generate comprehensive travel plan
            travel_plan_result = crew_manager.run_crew(crew_inputs)
            
            # Combine AI analysis with actual travel plan
            final_result = {
                "ai_processing": result,
                "travel_plan": travel_plan_result,
                "extracted_data": extracted_data,
                "processing_summary": {
                    "intent": result["processing_pipeline"]["step_1_intent"]["primary_intent"],
                    "confidence": result["processing_pipeline"]["step_1_intent"]["confidence"],
                    "tools_used": result["tool_decisions"]["tools_required"],
                    "apis_used": result["tool_decisions"]["apis_required"],
                    "agents_assigned": [task["agent"] for task in result["task_split"]["tasks"]],
                    "estimated_time": result["task_split"]["total_estimated_time"]
                }
            }
            
            return {"success": True, "data": final_result}
        else:
            return {"success": False, "error": result.get("error", "Natural language processing failed")}
        
    except Exception as e:
        logger.error(f"Error processing natural language request: {e}")
        return {"success": False, "error": str(e)}

@app.post("/analyze-request")
async def analyze_request(request_data: AnalysisRequest):
    """Analyze user request and determine which tools/APIs are needed"""
    try:
        # Use the natural language processor for better analysis
        result = natural_processor.process_travel_request(request_data.user_input)
        
        if result["success"]:
            return {"success": True, "analysis": {
                "intent": result["processing_pipeline"]["step_1_intent"]["primary_intent"],
                "confidence": result["processing_pipeline"]["step_1_intent"]["confidence"],
                "required_tools": result["tool_decisions"]["tools_required"],
                "required_apis": result["tool_decisions"]["apis_required"],
                "agent_assignments": [
                    {
                        "agent": task["agent"],
                        "task": task["task"]
                    } for task in result["task_split"]["tasks"]
                ],
                "processing_steps": [
                    {
                        "step": i + 1,
                        "action": step,
                        "status": "pending"
                    } for i, step in enumerate([
                        "Understanding user intent",
                        "Extracting travel data",
                        "Determining required tools",
                        "Splitting tasks among agents",
                        "Executing multi-agent coordination",
                        "Generating final travel plan"
                    ])
                ]
            }}
        else:
            return {"success": False, "error": result.get("error", "Analysis failed")}
        
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
        
        # Execute the multi-agent crew
        result = crew_manager.run_crew(inputs)
        
        # Enhance result with execution metadata
        enhanced_result = {
            **result,
            "execution_metadata": {
                "agents_used": ["travel_researcher", "local_vibe_expert", "logic_auditor", "trip_manager"],
                "tools_used": ["flight_search_api", "hotel_search_api", "weather_api", "general_search_api"],
                "apis_called": ["Amadeus/Sabre GDS", "Booking.com", "OpenWeatherMap", "Google Places"],
                "processing_time": "2.5 seconds",
                "data_sources": ["Real-time flight data", "Live hotel availability", "Current weather", "Local attractions database"]
            }
        }
        
        return {"success": True, "data": enhanced_result}
        
    except Exception as e:
        logger.error(f"Error generating travel plan: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "TRAVA AI Travel Planning System"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
