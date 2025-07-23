# GenAI Mediaplan API

A FastAPI-based REST API for generating mediaplans using CrewAI agents.

## Features

- **Synchronous Mediaplan Generation**: Generate mediaplans immediately
- **Asynchronous Mediaplan Generation**: Start background tasks and poll for status
- **Health Checks**: Monitor API health
- **Cohort Management**: Get available cohorts
- **Google Slides Integration**: Automatically create presentations

## Installation

1. Install dependencies:
```bash
uv add fastapi uvicorn[standard] pydantic
```

2. Set up environment variables in `.env`:
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4

# Optional: OpenAI fallback
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the API

### Option 1: Using the startup script
```bash
python run_api.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn src.genai_mediaplan.api:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using the project script
```bash
uv run api
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

### Get Available Cohorts
```http
GET /available-cohorts
```

Response:
```json
{
  "cohorts": ["Shopping", "Education", "Travel", "Finance", "Healthcare", "Technology"],
  "total": 6
}
```

### Generate Mediaplan (Synchronous)
```http
POST /generate-mediaplan
Content-Type: application/json

{
  "cohort_name": "Shopping"
}
```

Response:
```json
{
  "status": "success",
  "message": "Mediaplan generated successfully for Shopping",
  "cohort_name": "Shopping",
  "google_slides_url": "https://drive.google.com/file/d/...",
  "error": null
}
```

### Generate Mediaplan (Asynchronous)
```http
POST /generate-mediaplan-async
Content-Type: application/json

{
  "cohort_name": "Shopping"
}
```

Response:
```json
{
  "task_id": "task_20240115_103000_Shopping",
  "status": "started",
  "message": "Mediaplan generation started in background"
}
```

### Check Task Status
```http
GET /task-status/{task_id}
```

Response:
```json
{
  "status": "running",
  "progress": 50,
  "message": "Running CrewAI agents...",
  "cohort_name": "Shopping",
  "created_at": "2024-01-15T10:30:00",
  "google_slides_url": null,
  "error": null
}
```

## Usage Examples

### Python Client
```python
import requests

# Generate mediaplan synchronously
response = requests.post("http://localhost:8000/generate-mediaplan", 
                        json={"cohort_name": "Shopping"})
result = response.json()
print(f"Google Slides URL: {result['google_slides_url']}")

# Generate mediaplan asynchronously
response = requests.post("http://localhost:8000/generate-mediaplan-async", 
                        json={"cohort_name": "Shopping"})
task_id = response.json()['task_id']

# Poll for status
while True:
    status = requests.get(f"http://localhost:8000/task-status/{task_id}").json()
    if status['status'] == 'completed':
        print(f"Done! URL: {status['google_slides_url']}")
        break
    elif status['status'] == 'failed':
        print(f"Failed: {status['error']}")
        break
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Get available cohorts
curl http://localhost:8000/available-cohorts

# Generate mediaplan synchronously
curl -X POST http://localhost:8000/generate-mediaplan \
  -H "Content-Type: application/json" \
  -d '{"cohort_name": "Shopping"}'

# Generate mediaplan asynchronously
curl -X POST http://localhost:8000/generate-mediaplan-async \
  -H "Content-Type: application/json" \
  -d '{"cohort_name": "Shopping"}'

# Check task status
curl http://localhost:8000/task-status/task_20240115_103000_Shopping
```

## Testing

Run the test script to verify the API is working:
```bash
python test_api.py
```

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `404`: Task not found
- `500`: Internal server error

Error responses include detailed error messages:
```json
{
  "detail": "Error generating mediaplan: [specific error message]"
}
```

## Configuration

### Environment Variables
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_API_VERSION`: API version (default: 2024-02-15-preview)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Your deployment name
- `AZURE_OPENAI_MODEL`: Model name (default: gpt-4)
- `OPENAI_API_KEY`: Fallback OpenAI API key

### Server Configuration
- **Host**: 0.0.0.0 (accessible from any IP)
- **Port**: 8000
- **Reload**: Enabled for development
- **Log Level**: info

## Production Deployment

For production deployment, consider:
1. Using a production ASGI server like Gunicorn
2. Setting up proper logging
3. Adding authentication/authorization
4. Using environment-specific configurations
5. Setting up monitoring and health checks

Example production command:
```bash
gunicorn src.genai_mediaplan.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
``` 