# 🚀 Quick Start Guide

## Step 1: Start Backend Server

Open **Terminal 1**:

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

✅ **Backend is running at:** http://localhost:8000  
✅ **API Docs at:** http://localhost:8000/docs

---

## Step 2: Start Frontend

Open **Terminal 2** (NEW TERMINAL WINDOW):

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm run dev -- --host
```

**Expected output:**
```
  VITE v5.4.10  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

✅ **Frontend is running at:** http://localhost:5173

---

## Step 3: Open the App

1. Open your browser
2. Go to: **http://localhost:5173**
3. You should see the beautiful Video Clip Selection Platform! 🎬

---

## 🎯 What You'll See

- **Dark gradient background** with animated particles
- **Drag & drop upload area** for videos
- **Real-time upload progress** with percentage
- **Interactive weight sliders** for analysis
- **Beautiful result cards** with thumbnails
- **CLIPS query search** for semantic search

---

## 📝 First Time Setup (Only if needed)

### If you haven't created virtual environment:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### If you haven't installed frontend dependencies:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm install
```

---

## 🎬 How to Use

1. **Upload Videos:**
   - Drag & drop videos or click to browse
   - Supports: .mp4, .mov, .mkv, .avi, .webm, or .zip
   - Watch upload progress in real-time!

2. **Adjust Weights** (optional):
   - Sharpness: How important is video clarity?
   - Stability: How important is steady camera?
   - Faces: How important are faces in videos?

3. **Click "Analyze Videos"**
   - Wait for upload to complete (see progress %)
   - Analysis runs in background
   - Results appear automatically!

4. **View Results:**
   - See ranked videos with thumbnails
   - Scores show quality ratings
   - Download top 3 or top 5 clips

5. **CLIPS Query** (optional):
   - Switch to "CLIPS Query" tab
   - Search by natural language
   - Find videos semantically!

---

## ⚠️ Troubleshooting

### Backend won't start:
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Check if port 8000 is free
lsof -ti:8000 | xargs kill -9
```

### Frontend won't start:
```bash
# Install dependencies
cd frontend
npm install

# If port 5173 is busy, Vite will use next available port
```

### "Module not found" errors:
- Backend: `pip install -r backend/requirements.txt`
- Frontend: `npm install`

### Upload fails:
- Make sure backend is running on port 8000
- Check browser console (F12) for errors
- Verify `python-multipart` is installed: `pip install python-multipart`

---

## 🛑 Stop Servers

- Press `CTRL+C` in each terminal window
- Or close the terminal windows

---

## 📦 Quick Commands Reference

### Backend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm run dev -- --host
```

---

## ✅ Verify Everything Works

1. ✅ Backend: http://localhost:8000/docs (should show API docs)
2. ✅ Frontend: http://localhost:5173 (should show beautiful UI)
3. ✅ Upload a test video file
4. ✅ See upload progress percentage
5. ✅ Wait for analysis to complete
6. ✅ See results with thumbnails

---

## 🎉 That's It!

You're ready to analyze videos! The app features:
- ✨ Beautiful modern UI
- 📊 Real-time upload progress
- 🎯 Accurate video analysis
- 🔍 Semantic search
- ⬇️ Download top clips

Enjoy! 🚀

