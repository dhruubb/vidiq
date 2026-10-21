import os
import cv2
import face_recognition
import numpy as np

# Constants
FRAME_SKIP = 10
EMBED_EVERY_N_FRAMES = 30
RESIZE_WIDTH = 640
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")


def variance_of_laplacian(image):
    """Measure blurriness using Laplacian variance"""
    return cv2.Laplacian(image, cv2.CV_64F).var()


def normalize(value, min_val, max_val, new_min=0, new_max=5):
    """Normalize a value into a new range [new_min, new_max]"""
    if max_val - min_val == 0:
        return new_min
    return new_min + (value - min_val) * (new_max - new_min) / (max_val - min_val)


def process_video(video_path):
    """Process a video file and return refined scoring results"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"video": os.path.basename(video_path), "path": video_path, "score": 0}

    ret, frame1 = cap.read()
    if not ret or frame1 is None:
        cap.release()
        return {"video": os.path.basename(video_path), "path": video_path, "score": 0}

    video_name = os.path.basename(video_path)
    blur_values = []
    motion_values = []
    known_faces = []

    frame_index = 0
    face_frame_index = 0

    while True:
        ret, frame2 = cap.read()
        if not ret or frame2 is None:
            break

        frame_index += 1
        if frame_index % FRAME_SKIP != 0:
            continue

        try:
            frame2 = cv2.resize(frame2, (RESIZE_WIDTH, int(frame2.shape[0] * RESIZE_WIDTH / frame2.shape[1])))
            frame1 = cv2.resize(frame1, frame2.shape[1::-1])
        except Exception:
            continue

        try:
            gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        except Exception:
            continue

        # Face detection
        try:
            rgb_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
        except Exception:
            face_locations = []

        # Blur detection
        fm_values = []
        for top, right, bottom, left in face_locations:
            face_region = gray[top:bottom, left:right]
            if face_region.size > 0:
                fm_values.append(variance_of_laplacian(face_region))

        if fm_values:
            avg_fm = np.mean(fm_values)  # use faces for blur if present
        else:
            avg_fm = variance_of_laplacian(gray)  # fallback to whole frame

        blur_values.append(avg_fm)

        # Motion detection
        try:
            diff = cv2.absdiff(frame1, frame2)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray_diff, (21, 21), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            frame_motion = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 1500)
            motion_values.append(frame_motion)
        except Exception:
            pass

        frame1 = frame2.copy()

        # Face embeddings (deduplication)
        if face_frame_index % EMBED_EVERY_N_FRAMES == 0:
            try:
                encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                for encoding in encodings:
                    matches = face_recognition.compare_faces(known_faces, encoding, tolerance=0.6)
                    if not any(matches):
                        known_faces.append(encoding)
            except Exception:
                pass
        face_frame_index += 1

    cap.release()
    cv2.destroyAllWindows()

    # ---- SCORING ----
    # Blur score (normalize Laplacian variance)
    if blur_values:
        blur_mean = np.mean(blur_values)
        blur_score = normalize(blur_mean, min(blur_values), max(blur_values), 0, 5)
    else:
        blur_score = 0

    # Motion score (prefer moderate movement)
    if motion_values:
        motion_mean = np.mean(motion_values)
        motion_score = normalize(motion_mean, min(motion_values), max(motion_values), 0, 5)

        # Penalize extremes: very low = static, very high = shaky
        if motion_score < 1:
            motion_score *= 0.5
        elif motion_score > 4:
            motion_score *= 0.7
    else:
        motion_score = 0

    # Face score (based on number of unique faces)
    face_score = min(len(known_faces) * 1.5, 5)  # cap at 5

    # Weighted final score
    final_score = round(0.4 * blur_score + 0.3 * motion_score + 0.3 * face_score, 2)

    return {
        "video": video_name,
        "path": video_path,
        "score": final_score,
        "blur_score": round(blur_score, 2),
        "motion_score": round(motion_score, 2),
        "face_score": round(face_score, 2)
    }
