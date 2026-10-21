# Video Clip Selection Platform

AI-powered system to analyze, rank, and search video clips by quality and semantic content.

## Tech Stack
- Backend: FastAPI, OpenCV, NumPy, Requests, Tenacity, Pydantic
- Frontend: React (Vite) + Tailwind CSS
- Deployment: Docker / docker-compose

## Environment Setup

### API Key Configuration (Required for CLIPS Query)

The application uses OpenAI API for the CLIPS Query feature. **Never commit API keys to git.**

#### Option 1: Using .env file (Recommended)

1. Create a `.env` file in the `backend` directory:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   CLIPS_API_KEY=sk-your-openai-api-key-here
   ```

3. Get your API key from: https://platform.openai.com/api-keys

#### Option 2: Using Environment Variable

**Linux/macOS:**
```bash
export CLIPS_API_KEY='sk-your-openai-api-key-here'
```

**Windows:**
```cmd
set CLIPS_API_KEY=sk-your-openai-api-key-here
```

**Note:** The `.env` file is automatically ignored by git (see `.gitignore`).

See `API_KEY_SETUP.md` for detailed instructions.

## Run with Docker

```
docker compose up --build
```
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Local Dev (Backend)

1. Set up virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. Set up API key (see Environment Setup above)

3. Run the backend:
   ```bash
   uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints
- POST `/api/upload-zip` — upload a ZIP of clips
- POST `/api/upload-files` — upload multiple video files
- GET `/api/results/{job_id}` — get analysis results
- GET `/api/thumbnail/{job_id}/{name}` — get thumbnail jpeg
- POST `/api/download-top/{job_id}?k=5` — download top K as zip
- POST `/api/query-clips` — query by natural language (CLIPS)
- POST `/api/cleanup/{job_id}` — delete temporary job data

## Notes
- Face detection uses OpenCV Haar cascade for portability; swap with `mediapipe` or `face_recognition` for improved accuracy.
- CLIPS client includes simple caching of embeddings per video file.
- Video metrics: Laplacian variance (sharpness), optical flow magnitude (stability inverted), face count (presence).


