from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from genai_mediaplan.crew import GenaiMediaplan
from genai_mediaplan.utils.forecast_data import export_table_as_json
from genai_mediaplan.utils.helper import extract_json_from_markdown_or_json
from genai_mediaplan.utils.update_google_slides_content import get_copy_of_presentation

# Load environment variables
load_dotenv(override=True)

app = FastAPI(
    title="GenAI Mediaplan API",
    description="API for running CrewAI mediaplan generation",
    version="1.0.0"
)

# Pydantic models for request/response
class CohortRequest(BaseModel):
    cohort_name: str
    audience_data: Optional[Dict[str, Any]] = None
    forecast_data: Optional[Dict[str, Any]] = None

class CohortResponse(BaseModel):
    status: str
    message: str
    cohort_name: str
    google_slides_url: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Global variable to store task status
task_status = {}

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.post("/generate-mediaplan", response_model=CohortResponse)
async def generate_mediaplan(request: CohortRequest):
    """
    Generate a mediaplan for a specific cohort.
    
    This endpoint will:
    1. Run the CrewAI agents to generate insights
    2. Create a Google Slides presentation
    3. Return the presentation URL
    """
    try:
        # Use provided data or fetch from database
        if request.audience_data and request.forecast_data:
            audience_data = request.audience_data
            forecast_data = request.forecast_data
        else:
            # Fetch data from database
            data = export_table_as_json(request.cohort_name)
            audience_data = data['abvr']
            forecast_data = data['results']
        
        # Prepare inputs for CrewAI
        inputs = {
            'cohort_name': request.cohort_name,
            'audience_data': audience_data
        }
        
        # Run CrewAI
        crew = GenaiMediaplan().crew()
        result = crew.kickoff(inputs=inputs)
        
        # Extract JSON from the generated report
        model_output_json = extract_json_from_markdown_or_json("final_report.md")
        
        # Create Google Slides presentation
        google_slides_url = get_copy_of_presentation(
            request.cohort_name, 
            model_output_json, 
            forecast_data
        )
        
        return CohortResponse(
            status="success",
            message=f"Mediaplan generated successfully for {request.cohort_name}",
            cohort_name=request.cohort_name,
            google_slides_url=google_slides_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating mediaplan: {str(e)}"
        )

@app.post("/generate-mediaplan-async")
async def generate_mediaplan_async(request: CohortRequest, background_tasks: BackgroundTasks):
    """
    Generate a mediaplan asynchronously.
    
    This endpoint starts the generation process in the background
    and returns a task ID that can be used to check status.
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.cohort_name}"
    
    # Initialize task status
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "Starting mediaplan generation...",
        "cohort_name": request.cohort_name,
        "created_at": datetime.now().isoformat(),
        "google_slides_url": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(
        run_mediaplan_generation,
        task_id,
        request.cohort_name,
        request.audience_data,
        request.forecast_data
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Mediaplan generation started in background"
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background task.
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_status[task_id]

@app.get("/available-cohorts")
async def get_available_cohorts():
    """
    Get list of available cohorts.
    """
    # This would typically query your database
    # For now, returning a static list
    cohorts = [
        "Shopping",
        "Education", 
        "Travel",
        "Finance",
        "Healthcare",
        "Technology"
    ]
    
    return {
        "cohorts": cohorts,
        "total": len(cohorts)
    }

async def run_mediaplan_generation(task_id: str, cohort_name: str, audience_data: Optional[Dict], forecast_data: Optional[Dict]):
    """
    Background task to run mediaplan generation.
    """
    try:
        # Update status
        task_status[task_id]["progress"] = 10
        task_status[task_id]["message"] = "Fetching data..."
        
        # Use provided data or fetch from database
        if audience_data and forecast_data:
            audience_data = audience_data
            forecast_data = forecast_data
        else:
            # Fetch data from database
            data = export_table_as_json(cohort_name)
            audience_data = data['abvr']
            forecast_data = data['results']
        
        task_status[task_id]["progress"] = 20
        task_status[task_id]["message"] = "Running CrewAI agents..."
        
        # Prepare inputs for CrewAI
        inputs = {
            'cohort_name': cohort_name,
            'audience_data': audience_data
        }
        
        # Run CrewAI
        crew = GenaiMediaplan().crew()
        result = crew.kickoff(inputs=inputs)
        
        task_status[task_id]["progress"] = 80
        task_status[task_id]["message"] = "Creating Google Slides presentation..."
        
        # Extract JSON from the generated report
        model_output_json = extract_json_from_markdown_or_json("final_report.md")
        
        # Create Google Slides presentation
        google_slides_url = get_copy_of_presentation(
            cohort_name, 
            model_output_json, 
            forecast_data
        )
        
        # Update final status
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "Mediaplan generated successfully"
        task_status[task_id]["google_slides_url"] = google_slides_url
        task_status[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Update error status
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["message"] = f"Error: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["failed_at"] = datetime.now().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 