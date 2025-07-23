#!/usr/bin/env python3
"""
FastAPI server entry point for GenAI Mediaplan API
"""
import uvicorn
from genai_mediaplan.api import app

def main():
    """Run the FastAPI server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 