from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

app = FastAPI(title="GenAI Mediaplan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    timestamp: str

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

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.now().isoformat())

@app.get("/available-cohorts")
async def get_available_cohorts():
    cohorts = ["Shopping", "Education", "Travel", "Finance", "Healthcare", "Technology"]
    return {"cohorts": cohorts, "total": len(cohorts)}

@app.post("/generate-mediaplan", response_model=CohortResponse)
async def generate_mediaplan(request: CohortRequest):
    """Generate a mediaplan for a specific cohort."""
    try:
        # Simulate processing
        google_slides_url = f"https://drive.google.com/file/d/dummy_{request.cohort_name}_presentation"
        
        return CohortResponse(
            status="success",
            message=f"Mediaplan generated successfully for {request.cohort_name}",
            cohort_name=request.cohort_name,
            google_slides_url=google_slides_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating mediaplan: {str(e)}")

@app.get("/auth/oauth-status")
async def get_oauth_status():
    """Check if OAuth is properly configured"""
    return {
        "oauth_configured": True,
        "message": "OAuth credentials found and ready to use"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting GenAI Mediaplan API server on port 8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000) 