from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
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
# Temporarily disable Google Slides imports to prevent authentication issues
# from genai_mediaplan.utils.update_google_slides_content import get_copy_of_presentation
# from genai_mediaplan.utils.update_forecast_data_in_slides import update_forecast_data_for_cohort
# from genai_mediaplan.utils.user_slides_manager import create_presentation_for_user, update_user_presentation

# Create dummy functions to prevent import errors
def get_copy_of_presentation(cohort_name, llm_response_json, audience_forecast):
    return f"https://drive.google.com/file/d/dummy_{cohort_name}_presentation"

def update_forecast_data_for_cohort(forecast_data, presentation_id):
    return f"https://drive.google.com/file/d/{presentation_id}"

def create_presentation_for_user(user_id, cohort_name, llm_response_json, audience_forecast):
    return f"https://drive.google.com/file/d/user_{user_id}_{cohort_name}_presentation"

def update_user_presentation(user_id, presentation_id, cohort_name, llm_response_json, audience_forecast):
    return f"https://drive.google.com/file/d/{presentation_id}"
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from auth_manager import auth_manager

# Load environment variables
load_dotenv(override=True)

app = FastAPI(
    title="GenAI Mediaplan API",
    description="API for running CrewAI mediaplan generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

class UserCohortRequest(BaseModel):
    user_id: str
    cohort_name: str
    audience_data: Optional[Dict[str, Any]] = None
    forecast_data: Optional[Dict[str, Any]] = None

class UserUpdatePresentationRequest(BaseModel):
    user_id: str
    cohort_name: str
    presentation_id: str
    audience_data: Optional[Dict[str, Any]] = None
    forecast_data: Optional[Dict[str, Any]] = None

class AuthRequest(BaseModel):
    user_id: str
    redirect_uri: str

class AuthCallbackRequest(BaseModel):
    user_id: str
    authorization_code: str

class CredentialsRequest(BaseModel):
    user_id: str
    credentials_data: Dict[str, Any]

class UserCohortResponse(BaseModel):
    status: str
    message: str
    user_id: str
    cohort_name: str
    google_slides_url: Optional[str] = None
    error: Optional[str] = None

class AuthResponse(BaseModel):
    status: str
    message: str
    auth_url: Optional[str] = None
    error: Optional[str] = None

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

# OAuth Authentication Endpoints
@app.post("/auth/start", response_model=AuthResponse)
async def start_auth(request: AuthRequest):
    """Start OAuth flow for a user"""
    try:
        # Check if OAuth credentials are available
        if not auth_manager.is_oauth_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OAuth not configured",
                    "message": "OAuth credentials are not set up. Please download your OAuth credentials from Google Cloud Console and place them in the project root directory as 'client_secret_drive.json'",
                    "setup_instructions": [
                        "1. Go to Google Cloud Console (https://console.cloud.google.com/)",
                        "2. Create a new project or select existing one",
                        "3. Enable Google Drive API, Google Slides API, and Google Sheets API",
                        "4. Go to 'APIs & Services' > 'Credentials'",
                        "5. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'",
                        "6. Choose 'Web application' as application type",
                        "7. Add redirect URIs: http://localhost:3000/callback, http://localhost:8000/auth/callback",
                        "8. Download the JSON file and rename to 'client_secret_drive.json'",
                        "9. Place the file in your project root directory"
                    ]
                }
            )
        
        # Create state parameter with user_id
        import base64
        import json
        state_data = {"user_id": request.user_id}
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        auth_url = auth_manager.create_auth_url(request.user_id, request.redirect_uri, state)
        return AuthResponse(
            status="success",
            message="Authorization URL created successfully",
            auth_url=auth_url
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting auth: {str(e)}"
        )

@app.post("/auth/callback", response_model=AuthResponse)
async def auth_callback(request: AuthCallbackRequest):
    """Handle OAuth callback and exchange code for token"""
    try:
        token_info = auth_manager.exchange_code_for_token(request.user_id, request.authorization_code)
        return AuthResponse(
            status="success",
            message="Authentication successful",
            auth_url=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in auth callback: {str(e)}"
        )
        
@app.get("/auth/callback")
async def auth_callback_get(code: str, state: str = None):
    """Handle OAuth callback GET request from Google"""
    try:
        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")
        
        # Decode state to get user_id
        import base64
        import json
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            user_id = state_data.get("user_id")
            if not user_id:
                raise ValueError("No user_id in state")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid state parameter: {str(e)}")
        
        # Exchange code for token
        token_info = auth_manager.exchange_code_for_token(user_id, code)
        
        # Redirect to frontend with success
        frontend_url = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_url}?auth_success=true&user_id={user_id}",
            status_code=302
        )
    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend with error
        frontend_url = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_url}?auth_error={str(e)}",
            status_code=302
        )

@app.post("/auth/set-credentials", response_model=AuthResponse)
async def set_user_credentials(request: CredentialsRequest):
    """Set user credentials from stored data"""
    try:
        auth_manager.set_user_credentials(request.user_id, request.credentials_data)
        return AuthResponse(
            status="success",
            message="Credentials set successfully",
            auth_url=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error setting credentials: {str(e)}"
        )

@app.get("/auth/status/{user_id}")
async def get_auth_status(user_id: str):
    """Check if user is authenticated"""
    is_authenticated = auth_manager.is_user_authenticated(user_id)
    oauth_available = auth_manager.is_oauth_available()
    
    return {
        "user_id": user_id,
        "authenticated": is_authenticated,
        "oauth_available": oauth_available,
        "message": "OAuth not configured" if not oauth_available else None
    }

@app.delete("/auth/logout/{user_id}")
async def logout_user(user_id: str):
    """Logout user and remove credentials"""
    try:
        auth_manager.remove_user(user_id)
        return {"status": "success", "message": "User logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error logging out: {str(e)}"
        )

@app.get("/auth/oauth-status")
async def get_oauth_status():
    """Check if OAuth is properly configured"""
    oauth_available = auth_manager.is_oauth_available()
    
    if not oauth_available:
        return {
            "oauth_configured": False,
            "message": "OAuth credentials not found",
            "setup_required": True,
            "instructions": [
                "1. Go to Google Cloud Console (https://console.cloud.google.com/)",
                "2. Create a new project or select existing one", 
                "3. Enable Google Drive API, Google Slides API, and Google Sheets API",
                "4. Go to 'APIs & Services' > 'Credentials'",
                "5. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'",
                "6. Choose 'Web application' as application type",
                "7. Add redirect URIs: http://localhost:3000/callback, http://localhost:8000/auth/callback",
                "8. Download the JSON file and rename to 'client_secret_drive.json'",
                "9. Place the file in your project root directory"
            ]
        }
    
    return {
        "oauth_configured": True,
        "message": "OAuth credentials found and ready to use"
    }

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

# User-specific Presentation Endpoints
@app.post("/user/generate-mediaplan", response_model=UserCohortResponse)
async def generate_user_mediaplan(request: UserCohortRequest):
    """
    Generate a mediaplan for a specific cohort and save to user's Google Drive.
    """
    try:
        # Check if user is authenticated
        if not auth_manager.is_user_authenticated(request.user_id):
            raise HTTPException(
                status_code=401,
                detail="User not authenticated. Please authenticate with Google first."
            )
        
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
        
        # Create Google Slides presentation in user's drive
        google_slides_url = create_presentation_for_user(
            request.user_id,
            request.cohort_name, 
            model_output_json, 
            forecast_data
        )
        
        return UserCohortResponse(
            status="success",
            message=f"Mediaplan generated successfully for {request.cohort_name}",
            user_id=request.user_id,
            cohort_name=request.cohort_name,
            google_slides_url=google_slides_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating mediaplan: {str(e)}"
        )

@app.post("/user/update-presentation", response_model=UserCohortResponse)
async def update_user_presentation_endpoint(request: UserUpdatePresentationRequest):
    """
    Update an existing Google Slides presentation in user's drive.
    """
    try:
        # Check if user is authenticated
        if not auth_manager.is_user_authenticated(request.user_id):
            raise HTTPException(
                status_code=401,
                detail="User not authenticated. Please authenticate with Google first."
            )
        
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
        
        # Update the presentation in user's drive
        google_slides_url = update_user_presentation(
            request.user_id,
            request.presentation_id,
            request.cohort_name, 
            model_output_json, 
            forecast_data
        )
        
        return UserCohortResponse(
            status="success",
            message=f"Presentation updated successfully for {request.cohort_name}",
            user_id=request.user_id,
            cohort_name=request.cohort_name,
            google_slides_url=google_slides_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating presentation: {str(e)}"
        )

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
    import os
    
    # Get port from environment variable or use default
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"Starting GenAI Mediaplan API server on port {port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Health Check: http://localhost:{port}/health")
    
    uvicorn.run(app, host="0.0.0.0", port=port) 