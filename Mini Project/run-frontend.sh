#!/bin/bash

# Frontend Run Script
echo "🎨 Starting Frontend..."
echo "Frontend will run at: http://localhost:5173"
echo ""
echo "Press CTRL+C to stop"
echo ""

cd frontend
npm run dev -- --host

