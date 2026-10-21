import os
import zipfile
import tempfile
import shutil
import streamlit as st
from score_video import process_video


def extract_zip(uploaded_file, extract_dir):
    zip_path = os.path.join(extract_dir, uploaded_file.name)
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.read())

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

  
    video_paths = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                video_paths.append(os.path.join(root, file))
    return video_paths



st.title("🎬 AI Video Quality & Search Tool")

st.sidebar.header("Upload Options")
upload_type = st.sidebar.radio("Choose upload type:", ["Individual Videos", "Folder (ZIP)"])

video_paths = []
temp_dir = os.path.join(os.getcwd(), "temp_videos")
os.makedirs(temp_dir, exist_ok=True)


if upload_type == "Individual Videos":
    uploaded_files = st.file_uploader("Upload video files", type=["mp4", "mov", "avi", "mkv"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())
            video_paths.append(file_path)

elif upload_type == "Folder (ZIP)":
    uploaded_zip = st.file_uploader("Upload a ZIP file containing videos", type=["zip"])
    if uploaded_zip:
        video_paths = extract_zip(uploaded_zip, temp_dir)


if video_paths:
    st.success(f"✅ Found {len(video_paths)} videos. Processing...")

    results = []
    for path in video_paths:
        results.append(process_video(path))

    
    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    st.subheader("📊 Video Ranking Results")
    for res in results:
        st.write(
            f"**{res.get('video','Unknown')}** — Final Score: {res.get('score',0)} "
            f"(Blur: {res.get('blur_score','N/A')}, "
            f"Motion: {res.get('motion_score','N/A')}, "
            f"Faces: {res.get('face_score','N/A')})"
        )
        if os.path.exists(res.get("path","")):
            st.video(res["path"])

   
    st.subheader("⬇️ Download Best Clips")

    percentage = st.slider("Select top percentage of videos to download:", 10, 50, 20, step=5)
    top_n = max(1, int(len(results) * (percentage / 100)))

    best_videos = results[:top_n]

    if st.button(f"Prepare Download (Top {percentage}% — {top_n} files)"):
        zip_path = os.path.join(temp_dir, "best_videos.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for res in best_videos:
                if os.path.exists(res.get("path","")):
                    zipf.write(res["path"], os.path.basename(res["path"]))

        with open(zip_path, "rb") as f:
            st.download_button("⬇️ Download ZIP", f, file_name="best_videos.zip")
