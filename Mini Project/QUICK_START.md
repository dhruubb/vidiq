# Quick Start Guide

## Step 1: Add Your OpenAI API Key

1. Open `backend/app/services/clips.py`
2. Find line 16: `DEFAULT_API_KEY = "sk-REPLACE_WITH_YOUR_OPENAI_API_KEY"`
3. Replace `sk-REPLACE_WITH_YOUR_OPENAI_API_KEY` with your actual OpenAI API key
4. Save the file

## Step 2: Run Backend

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate  # if you haven't created venv: python3 -m venv .venv
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

Backend will run at: http://localhost:8000

## Step 3: Run Frontend (in a new terminal)

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm install
npm run dev -- --host
```

Frontend will run at: http://localhost:5173

## That's it!

- No environment variables needed
- Everything is configured in code
- Just replace the API key in `clips.py` and run!

## Usage

1. Open http://localhost:5173 in your browser
2. Upload video files (zip or multiple files)
3. Adjust weight sliders if needed
4. Click "Analyze Videos"
5. Wait for results to appear
6. Use "CLIPS Query" tab to search by semantic similarity

