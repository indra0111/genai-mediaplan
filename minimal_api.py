from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="GenAI Mediaplan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CohortRequest(BaseModel):
    cohort_name: str
    audience_data: Optional[Dict[str, Any]] = None
    forecast_data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "GenAI Mediaplan API is working!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "API server is running"}

@app.get("/available-cohorts")
async def get_available_cohorts():
    cohorts = ["Shopping", "Education", "Travel", "Finance", "Healthcare", "Technology"]
    return {"cohorts": cohorts, "total": len(cohorts)}

if __name__ == "__main__":
    import uvicorn
    print("Starting GenAI Mediaplan API server on port 8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000) 