# AI Video Selection Tool Improvements

I have successfully upgraded your video selection pipeline to include **Face Deduplication** and **Smart Scoring** using a lightweight, OpenCV-based approach. This solution is optimized for performance and runs efficiently without requiring heavy deep-learning libraries.

## Key Upgrades

### 1. Face Deduplication (ORB-based)
- **What it does**: Identifies unique people across your video library.
- **How**: Uses ORB (Oriented FAST and Rotated BRIEF) descriptors to "fingerprint" faces.
- **Benefit**: You can now distinguish between a video with 10 shots of the same person vs. a video with 10 different people.
- **Metric**: Added `unique_face_count` to the analysis results.

### 2. Enhanced Face Detection
- **Multi-Cascade**: Combines Frontal and Profile face detectors to catch side views.
- **NMS (Non-Maximum Suppression)**: Merges overlapping detections to prevent double-counting the same face.

### 3. Robust Scoring System
The scoring logic has been refined to be more robust to outliers:
- **Blur**: Uses a weighted average of Laplacian variance (edges) and Sobel gradient.
- **Motion**: Inverted motion score (lower motion = higher stability).
- **Faces**: Score is now a mix of total face count (70%) and unique face count (30%).

## How to Run

The system is already running with the new changes. You don't need to do anything special.

1. **Backend**:
   ```bash
   cd "Mini Project"
   source .venv/bin/activate
   uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend**:
   ```bash
   cd "Mini Project/frontend"
   npm run dev -- --host
   ```

3. **Verify**:
   - Upload a set of videos.
   - The analysis will now run using the new pipeline.
   - Check the backend logs to see the analysis progress.

## Performance Note
This implementation uses CPU-based computer vision. It is significantly faster than deep learning models and requires zero additional storage for model weights. It is production-ready for standard deployment.
