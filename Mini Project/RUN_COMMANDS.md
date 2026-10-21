# 🚀 Copy-Paste Commands to Run

## Option 1: Use the Run Scripts (Easiest)

### Terminal 1 - Backend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
./run.sh
```

### Terminal 2 - Frontend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
./run-frontend.sh
```

---

## Option 2: Manual Commands (Step by Step)

### Terminal 1 - Backend:

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend (NEW TERMINAL):

```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm run dev -- --host
```

---

## Option 3: One-Time Setup (If First Time)

### Setup Backend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Setup Frontend:
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm install
```

### Then Run (Terminal 1):
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project"
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### Then Run (Terminal 2):
```bash
cd "/Users/dhruubb/Desktop/Video Selection Project/Mini Project/frontend"
npm run dev -- --host
```

---

## ✅ What You Should See

### Backend Terminal:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

### Frontend Terminal:
```
  VITE v5.4.10  ready in 500 ms

  ➜  Local:   http://localhost:5173/
```

---

## 🌐 Open Browser

Go to: **http://localhost:5173**

---

## 🛑 Stop Servers

Press `CTRL+C` in each terminal

