#!/bin/bash

# GenAI Mediaplan User Authentication System Startup Script

echo "🚀 Starting GenAI Mediaplan User Authentication System..."
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required files exist
if [ ! -f "client_secret_drive.json" ]; then
    echo "⚠️  client_secret_drive.json not found in the current directory."
    echo "📝 This file is required for OAuth authentication."
    echo "   Please download your OAuth credentials from Google Cloud Console and rename it to client_secret_drive.json"
    echo ""
    echo "   You can still run the system without it, but user authentication features won't work."
    echo "   The original system will continue to work with your existing credentials."
    echo ""
    read -p "Do you want to continue without OAuth credentials? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating a template..."
    cat > .env << EOF
# Google Drive Configuration
SOURCE_FILE_ID=your_source_presentation_id_here
SOURCE_SHEET_ID=your_source_sheet_id_here
SHARED_FOLDER_ID=your_shared_folder_id_here

# Optional: Logging
LOG_LEVEL=INFO
EOF
    echo "📝 Please edit .env file with your actual Google Drive IDs"
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use."
        return 1
    fi
    return 0
}

# Function to find available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; do
        port=$((port + 1))
    done
    echo $port
}

# Check and find available ports
echo "🔍 Checking port availability..."

API_PORT=8000
FRONTEND_PORT=3000

if ! check_port $API_PORT; then
    API_PORT=$(find_available_port $API_PORT)
    echo "📊 API server will use port $API_PORT instead"
fi

if ! check_port $FRONTEND_PORT; then
    FRONTEND_PORT=$(find_available_port $FRONTEND_PORT)
    echo "🌐 Frontend server will use port $FRONTEND_PORT instead"
fi

echo "✅ Ports configured: API=$API_PORT, Frontend=$FRONTEND_PORT"

# Install dependencies if needed
echo "📦 Checking dependencies..."
if ! python3 -c "import google_auth_oauthlib" 2>/dev/null; then
    echo "📦 Installing Google OAuth dependencies..."
    pip3 install google-auth-oauthlib google-auth-httplib2
fi

# Set environment variables for ports
export API_PORT=$API_PORT
export FRONTEND_PORT=$FRONTEND_PORT

# Start API server in background
echo "🔧 Starting API server on port $API_PORT..."
cd src/genai_mediaplan
python3 api.py &
API_PID=$!
cd ../..

# Wait a moment for API server to start
sleep 3

# Check if API server started successfully
if ! lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "✅ API server started successfully"

# Start frontend server in background
echo "🌐 Starting frontend server on port $FRONTEND_PORT..."
cd frontend
# Update the frontend server to use the dynamic port
python3 -c "
import http.server
import socketserver
import os

PORT = int(os.environ.get('FRONTEND_PORT', 3000))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

with socketserver.TCPServer(('', PORT), MyHTTPRequestHandler) as httpd:
    print(f'Frontend server running at http://localhost:{PORT}')
    httpd.serve_forever()
" &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend server to start
sleep 2

# Check if frontend server started successfully
if ! lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Failed to start frontend server"
    kill $API_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend server started successfully"

echo ""
echo "🎉 System started successfully!"
echo "=================================================="
echo "📊 API Server: http://localhost:$API_PORT"
echo "🌐 Frontend: http://localhost:$FRONTEND_PORT"
echo "📚 API Documentation: http://localhost:$API_PORT/docs"
echo ""
if [ ! -f "client_secret_drive.json" ]; then
    echo "⚠️  Note: OAuth credentials not found. User authentication features are disabled."
    echo "   Original system functionality is still available."
fi
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $API_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop the servers
wait 