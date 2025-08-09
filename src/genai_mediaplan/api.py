from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from genai_mediaplan.schedulers.scheduler import scheduler
from genai_mediaplan.crew import GenaiMediaplan
from genai_mediaplan.utils.forecast_data_api_based import export_table_as_json
from genai_mediaplan.utils.helper import extract_json_from_markdown_or_json
from genai_mediaplan.utils.update_google_slides_content import get_copy_of_presentation
from genai_mediaplan.utils.update_forecast_data_in_slides import update_forecast_data_for_cohort

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

class UpdatePresentationRequest(BaseModel):
    cohort_name: str
    presentation_id: str
    forecast_data: Optional[Dict[str, Any]] = None

class CohortResponse(BaseModel):
    status: str
    message: str
    cohort_name: str
    google_slides_url: Optional[str] = None
    error: Optional[str] = None

class UpdatePresentationResponse(BaseModel):
    status: str
    message: str
    cohort_name: str
    presentation_id: str
    google_slides_url: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Global variable to store task status
task_status = {}

# Startup event to start the scheduler
@app.on_event("startup")
async def start_scheduler():
    """Start the scheduler when the FastAPI app starts"""
    scheduler.start()

# Shutdown event to stop the scheduler
@app.on_event("shutdown")
async def stop_scheduler():
    """Stop the scheduler when the FastAPI app shuts down"""
    scheduler.stop()
    
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

@app.post("/update-numerical-data-in-presentation", response_model=UpdatePresentationResponse)
async def update_numerical_data_in_presentation(request: UpdatePresentationRequest):
    """
    Update an existing Google Slides presentation with new cohort data.
    
    This endpoint will:
    1. Update the existing presentation with new forecast data
    2. Return the updated presentation URL
    """
    try:
        if request.forecast_data:
            forecast_data = request.forecast_data
        else:
            data = export_table_as_json(request.cohort_name)
            forecast_data = data['results']
        update_forecast_data_for_cohort(forecast_data, request.presentation_id)
        
        google_slides_url = f"https://drive.google.com/file/d/{request.presentation_id}"
        
        return UpdatePresentationResponse(
            status="success",
            message=f"Presentation updated successfully for {request.cohort_name}",
            cohort_name=request.cohort_name,
            presentation_id=request.presentation_id,
            google_slides_url=google_slides_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating presentation: {str(e)}"
        )
        
@app.get("/refresh-all-cohort-data")
async def refresh_all_cohort_data():
    """
    Refresh data for all cohorts.
    
    This endpoint will:
    1. Fetch all cohorts from the database
    2. Update their presentations with the latest forecast data
    """
    try:
        with open('mediaplan_responses.json', 'r') as f:
            data = json.loads(f.read())
        print("Starting to refresh all cohort data...", data)
        for cohort_name in data.keys():
            print(f"Processing cohort: {cohort_name}")
            try:
                presentation_id = data[cohort_name].get('google_slides_url', '').replace("https://docs.google.com/presentation/d/", "")
                if not presentation_id:
                    continue
                data_to_update = export_table_as_json(cohort_name)
                forecast_data = data_to_update['results']
                print(f"Updating data for {cohort_name} with presentation ID {presentation_id}")
                print(forecast_data)
                print(len(forecast_data.keys()), "forecast data keys")
                update_forecast_data_for_cohort(forecast_data, presentation_id)
            except Exception as e:
                print(f"❌ Failed to update data for {cohort_name}: {str(e)}")
                continue
        print("✅ Successfully refreshed all cohort data.")
        return JSONResponse(
            status_code=200,
            content={"message": "Cohort data refreshed successfully"}
        )
    
    except Exception as e:
        print(f"❌ Failed to refresh cohort data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing cohort data: {str(e)}"
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

@app.get("/scheduler-status")
async def get_scheduler_status():
    """Get the current status of the scheduler and its jobs"""
    try:
        return scheduler.get_status()
    except Exception as e:
        print(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
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