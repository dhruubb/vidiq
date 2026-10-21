import requests
import time
import subprocess
import sys
import os
import cv2
import numpy as np
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
AUTH_URL = "http://localhost:8000/api/auth"

def create_dummy_video(filename):
    height, width = 320, 320
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
    for _ in range(30): # 1 second
        frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    print(f"Created dummy video: {filename}")

def test_pipeline():
    # Start server
    print("Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd="backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for server
        for _ in range(30):
            try:
                requests.get("http://localhost:8000/docs")
                print("Server is up!")
                break
            except:
                time.sleep(1)
        else:
            print("Server failed to start")
            return

        # Login
        print("Logging in...")
        resp = requests.post(f"{AUTH_URL}/token", data={"username": "admin", "password": "password123"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful")

        # Create video
        video_path = "test_video.mp4"
        create_dummy_video(video_path)

        # Upload
        print("Uploading video...")
        with open(video_path, "rb") as f:
            files = {"files": (video_path, f, "video/mp4")}
            resp = requests.post(f"{BASE_URL}/upload-files", headers=headers, files=files)
        
        if resp.status_code != 200:
            print(f"Upload failed: {resp.text}")
            return
        
        job_id = resp.json()["job_id"]
        print(f"Job ID: {job_id}")

        # Poll results
        print("Polling results...")
        for _ in range(60):
            resp = requests.get(f"{BASE_URL}/results/{job_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data["results"]:
                    print("Analysis complete!")
                    print(f"Results: {data['results']}")
                    break
            time.sleep(1)
        else:
            print("Analysis timed out")
            return

        # Download top 1
        print("Downloading top 1...")
        resp = requests.post(f"{BASE_URL}/download-top/{job_id}?k=1", headers=headers)
        if resp.status_code == 200:
            print("Download successful!")
            with open("top_1.zip", "wb") as f:
                f.write(resp.content)
            print("Saved top_1.zip")
        else:
            print(f"Download failed: {resp.text}")

        # Test Video Preview Auth
        print("Testing Video Preview Auth...")
        video_name = data["results"][0]["filename"]
        # Try without token (should fail? No, we used query param)
        # Try with token
        resp = requests.get(f"{BASE_URL}/video/{job_id}/{video_name}?token={token}")
        if resp.status_code == 200:
            print("Video preview fetch successful")
        else:
            print(f"Video preview fetch failed: {resp.status_code}")

    finally:
        server_process.terminate()
        if os.path.exists("test_video.mp4"):
            os.remove("test_video.mp4")
        if os.path.exists("top_1.zip"):
            os.remove("top_1.zip")

if __name__ == "__main__":
    test_pipeline()
