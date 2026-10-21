# Complete Run Guide - Video Clip Selection Platform

## Step 1: Setup Backend

Open Terminal 1 (Backend):

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"

# Create virtual environment (if not already created)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install all dependencies (including python-multipart)
pip install -r backend/requirements.txt

# If requirements.txt doesn't work, install manually:
pip install fastapi==0.115.0
pip install uvicorn[standard]==0.30.6
pip install python-multipart==0.0.9
pip install opencv-python==4.10.0.84
pip install numpy==2.1.1
pip install requests==2.32.3
pip install tenacity==9.0.0
pip install python-dotenv==1.0.1
pip install pydantic==2.8.2

# Verify python-multipart is installed
python -c "import multipart; print('✅ python-multipart installed')"

# Start the backend server
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['...']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Application startup complete.
```

**✅ Backend is running at:** http://localhost:8000  
**✅ API Docs at:** http://localhost:8000/docs

---

## Step 2: Setup Frontend

Open Terminal 2 (New Terminal Window):

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"

# Install dependencies (first time only)
npm install

# Start the frontend dev server
npm run dev -- --host
```

**Expected output:**
```
  VITE v5.4.10  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

**✅ Frontend is running at:** http://localhost:5173

---

## Step 3: Open the App

1. Open your browser and go to: **http://localhost:5173**
2. You should see the "Video Clip Selection Platform" interface

---

## Step 4: Test the Upload

1. Click "Choose File" or drag and drop video files
2. Select one or more video files (.mp4, .mov, .mkv, .avi, .webm) OR a .zip file
3. Adjust weight sliders if needed (Blur, Motion, Faces)
4. Click "Analyze Videos"
5. Wait for analysis to complete (progress will show)
6. Results will appear with thumbnails and scores

---

## Troubleshooting

### If you get "python-multipart not found":
```bash
source .venv/bin/activate
pip install python-multipart==0.0.9
```

### If you get "Module not found" errors:
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### If backend port 8000 is already in use:
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8001
```
Then update frontend `API_BASE` in `frontend/src/App.tsx` to `http://localhost:8001/api`

### If frontend port 5173 is already in use:
Vite will automatically use the next available port (5174, 5175, etc.)

### If upload fails:
1. Check backend terminal for error messages
2. Check browser console (F12 → Console tab)
3. Make sure both backend and frontend are running
4. Verify python-multipart is installed: `python -c "import multipart; print('OK')"`

---

## Quick Commands Reference

### Backend (Terminal 1):
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2):
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm run dev -- --host
```

### Stop Servers:
- Press `CTRL+C` in each terminal

---

## Verify Everything Works

1. ✅ Backend running: http://localhost:8000/docs shows API documentation
2. ✅ Frontend running: http://localhost:5173 shows the app
3. ✅ Upload test: Upload a video file and see it process

---

## Next Steps After First Run

**You only need to:**
1. Activate venv: `source .venv/bin/activate`
2. Start backend: `uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000`
3. Start frontend: `cd frontend && npm run dev -- --host`

**No need to reinstall packages unless you:**
- Delete the `.venv` folder
- Update `requirements.txt` or `package.json`
- Get dependency errors

---

## Notes

- **API Key**: Already configured in `backend/app/services/clips.py` (line 16)
- **No environment variables needed**: Everything is hardcoded
- **Files are stored temporarily**: They're cleaned up automatically
- **Analysis runs in background**: You can close the browser tab, results will be ready when you come back

