#!/bin/bash

# Video Clip Selection Platform - Run Script
# This script helps you run the backend and frontend

echo "🎬 Video Clip Selection Platform - Startup Script"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Backend Server..."
echo "   Backend will run at: http://localhost:8000"
echo "   API Docs at: http://localhost:8000/docs"
echo ""
echo "📝 In a NEW terminal, run:"
echo "   cd frontend && npm run dev -- --host"
echo ""
echo "Press CTRL+C to stop the backend server"
echo "=================================================="
echo ""

# Start backend
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

