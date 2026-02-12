#!/bin/bash
# Start script for ASFS Web UI

echo "========================================="
echo "ASFS Web UI Startup"
echo "========================================="
echo ""

# Check if in correct directory
if [ ! -f "web/backend_app.py" ]; then
    echo "Error: Please run this script from the repository root"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q fastapi uvicorn python-multipart websockets pydantic || {
    echo "Error: Failed to install Python dependencies"
    exit 1
}

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg not found. Video metadata extraction may not work."
fi

# Start backend
echo ""
echo "Starting FastAPI backend on http://localhost:5000..."
cd web
python3 backend_app.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait a bit for backend to start
sleep 2

echo ""
echo "========================================="
echo "Backend started successfully!"
echo "API: http://localhost:5000"
echo "========================================="
echo ""
echo "To start the React frontend:"
echo "  cd web/frontend"
echo "  npm install"
echo "  npm start"
echo ""
echo "To stop the backend:"
echo "  kill $BACKEND_PID"
echo ""

# Keep script running
wait $BACKEND_PID
