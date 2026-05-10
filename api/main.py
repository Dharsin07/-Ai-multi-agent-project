from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from services.crew_manager import TravelCrewManager
from utils.logger import logger
import os

# Load environment variables at the very beginning
load_dotenv()

app = FastAPI(title="TRAVA AI - Multi-Agent Travel OS API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TravelRequest(BaseModel):
    destination: str
    budget: str
    duration: str
    preferences: str

@app.get("/")
def read_root():
    return {"status": "TRAVA AI Multi-Agent Backend is running with Real Search"}

@app.post("/generate-itinerary")
def generate_itinerary(request: TravelRequest):
    logger.info(f"Received API request for destination: {request.destination}")
    
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found in environment.")
        raise HTTPException(status_code=500, detail="LLM API key not configured on server.")
        
    try:
        manager = TravelCrewManager()
        inputs = {
            'destination': request.destination,
            'budget': request.budget,
            'duration': request.duration,
            'preferences': request.preferences
        }
        
        result_json = manager.run_crew(inputs)
        return {"status": "success", "data": result_json}
        
    except Exception as e:
        logger.error(f"API endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
