from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

from ..schemas import AnalysisRequestWeights, ClipScore

class FaceIdentifier:
    """
    Lightweight face deduplication using ORB descriptors.
    Matches faces based on feature descriptors to count unique people.
    """
    def __init__(self, threshold: float = 50.0):
        self.known_faces: List[np.ndarray] = []
        self.threshold = threshold
        self.orb = cv2.ORB_create(nfeatures=250, scoreType=cv2.ORB_FAST_SCORE)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def add_faces(self, descriptors: List[np.ndarray]):
        """
        Add new face descriptors to the known set if they are unique.
        """
        if not descriptors:
            return

        for desc in descriptors:
            if desc is None:
                continue
                
            is_new = True
            if self.known_faces:
                # Match against all known faces
                # We can't match one-to-many easily with BFMatcher in this structure without loop
                # or concatenating all known faces.
                # Let's do a simple loop for now as N is small
                for known in self.known_faces:
                    matches = self.matcher.match(desc, known)
                    if matches:
                        # Sort matches by distance
                        matches = sorted(matches, key=lambda x: x.distance)
                        # If good matches found, it's the same person
                        # Heuristic: if top match distance is low
                        if matches[0].distance < self.threshold:
                            is_new = False
                            break
            
            if is_new:
                self.known_faces.append(desc)

    def count_unique_faces(self) -> int:
        return len(self.known_faces)


class VideoAnalyzer:
    def __init__(
        self,
        frame_sample_rate: int = 24,
        resize_width: int = 320,
        motion_method: str = "diff",
        max_frames_per_video: int = 300,
        parallel_workers: int = 4,
    ) -> None:
        self.frame_sample_rate = frame_sample_rate
        self.resize_width = resize_width
        self.motion_method = motion_method
        self.max_frames_per_video = max_frames_per_video
        self.parallel_workers = parallel_workers

    def analyze_directory(self, clips_dir: Path, thumbs_dir: Path, weights: AnalysisRequestWeights) -> List[ClipScore]:
        results: List[ClipScore] = []
        thumbs_dir.mkdir(parents=True, exist_ok=True)

        video_exts = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
        files = sorted([p for p in clips_dir.rglob("*") if p.suffix.lower() in video_exts])
        if not files:
            return results

        raw_metrics = []
        
        # Parallel processing
        with ProcessPoolExecutor(max_workers=self.parallel_workers) as ex:
            futures = {ex.submit(self._analyze_single_process, p, thumbs_dir, self.resize_width, self.max_frames_per_video, self.frame_sample_rate): p for p in files}
            for fut in as_completed(futures):
                p = futures[fut]
                try:
                    metrics = fut.result()
                    raw_metrics.append((p.name, *metrics))
                except Exception as e:
                    print(f"Error analyzing {p.name}: {e}")
                    raw_metrics.append((p.name, 0.0, 1.0, 0, [], self._fallback_thumb(p, thumbs_dir)))

        # Global Face Deduplication using ORB
        face_identifier = FaceIdentifier()
        
        # Collect all descriptors
        for item in raw_metrics:
            descriptors = item[4] # face_descriptors
            face_identifier.add_faces(descriptors)
            
        # Calculate unique faces per video
        # This is tricky with the global add_faces approach.
        # The original logic likely counted unique faces *globally* or *per video*?
        # "picks the best ones using... deduplication"
        # Let's calculate unique faces PER VIDEO by creating a temporary identifier for each
        
        unique_counts_per_video = []
        for item in raw_metrics:
            descriptors = item[4]
            local_identifier = FaceIdentifier()
            local_identifier.add_faces(descriptors)
            unique_counts_per_video.append(local_identifier.count_unique_faces())
        
        # Normalization
        blur_vals = np.array([m[1] for m in raw_metrics], dtype=float)
        motion_vals = np.array([m[2] for m in raw_metrics], dtype=float)
        face_vals = np.array([m[3] for m in raw_metrics], dtype=float)
        unique_face_vals = np.array(unique_counts_per_video, dtype=float)

        blur_n = self._robust_norm(blur_vals)
        motion_n = 1.0 - self._robust_norm(motion_vals) # Lower motion is better
        face_n = self._robust_norm(face_vals)
        unique_face_n = self._robust_norm(unique_face_vals)

        for i, (fname, blur, mot, faces, _, thumb) in enumerate(raw_metrics):
            # Combined face score: raw count + unique count
            combined_face_score = (face_n[i] * 0.6 + unique_face_n[i] * 0.4)
            
            final_score = (
                float(blur_n[i]) * weights.blur_weight +
                float(motion_n[i]) * weights.motion_weight +
                float(combined_face_score) * weights.face_weight
            )
            
            results.append(ClipScore(
                filename=fname,
                blur_score=float(blur_n[i]),
                motion_score=float(motion_n[i]),
                face_score=float(combined_face_score),
                face_count=int(faces),
                unique_face_count=int(unique_counts_per_video[i]),
                final_score=float(final_score),
                thumbnail_name=thumb.stem,
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results

    @staticmethod
    def _analyze_single_process(video_path: Path, thumbs_dir: Path, resize_width: int, max_frames: int, sample_rate: int):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return 0.0, 1.0, 0, [], VideoAnalyzer._fallback_thumb(video_path, thumbs_dir)

        # Initialize detectors
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        orb = cv2.ORB_create(nfeatures=250, scoreType=cv2.ORB_FAST_SCORE)
        
        frame_idx = 0
        blur_scores = []
        motion_mags = []
        face_counts = []
        face_descriptors = []
        
        prev_gray = None
        best_frame = None
        best_blur_score = -1
        processed = 0
        
        while True:
            # Simple fixed sampling
            for _ in range(sample_rate - 1):
                cap.grab()
                frame_idx += 1
                
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1
            
            # Resize
            if resize_width and frame.shape[1] > resize_width:
                h, w = frame.shape[:2]
                new_h = int(h * (resize_width / w))
                frame = cv2.resize(frame, (resize_width, new_h), interpolation=cv2.INTER_AREA)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Blur (Laplacian variance)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_scores.append(blur_score)
            
            if blur_score > best_blur_score:
                best_blur_score = blur_score
                best_frame = frame.copy()

            # Motion
            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = float(np.mean(diff))
                motion_mags.append(motion_score)
            prev_gray = gray

            # Face Detection (Haar)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            face_counts.append(len(faces))
            
            # Face Descriptors (ORB)
            if len(faces) > 0:
                kp, des = orb.detectAndCompute(gray, None)
                if des is not None:
                    # Store descriptors for deduplication
                    # We just store a sample of descriptors from the frame
                    face_descriptors.append(des)

            processed += 1
            if max_frames and processed >= max_frames:
                break

        cap.release()

        if not blur_scores:
            return 0.0, 1.0, 0, [], VideoAnalyzer._fallback_thumb(video_path, thumbs_dir)

        blur_score = float(np.median(blur_scores))
        motion_avg = float(np.median(motion_mags)) if motion_mags else 0.0
        faces_avg = int(round(float(np.percentile(face_counts, 90)))) if face_counts else 0
        
        # Flatten descriptors list
        # face_descriptors is a list of numpy arrays (N, 32)
        # We want a list of single descriptors for the FaceIdentifier
        flat_descriptors = []
        if face_descriptors:
            # Limit to avoid memory issues
            if len(face_descriptors) > 50:
                import random
                face_descriptors = random.sample(face_descriptors, 50)
                
            for des in face_descriptors:
                if des is not None:
                    for d in des:
                        flat_descriptors.append(d)
                        
        if best_frame is not None:
            thumb_path = thumbs_dir / f"{video_path.stem}.jpg"
            cv2.imwrite(str(thumb_path), best_frame)
            thumb_written = thumb_path
        else:
            thumb_written = VideoAnalyzer._fallback_thumb(video_path, thumbs_dir)

        return blur_score, motion_avg, faces_avg, flat_descriptors, thumb_written

    @staticmethod
    def _fallback_thumb(video_path: Path, thumbs_dir: Path) -> Path:
        blank = np.zeros((180, 320, 3), dtype=np.uint8)
        path = thumbs_dir / f"{video_path.stem}.jpg"
        cv2.imwrite(str(path), blank)
        return path

    def _robust_norm(self, arr: np.ndarray) -> np.ndarray:
        if len(arr) == 0: return arr
        if len(arr) == 1: return np.ones_like(arr)
        p5, p95 = float(np.percentile(arr, 5)), float(np.percentile(arr, 95))
        if p95 - p5 < 1e-9:
            amin, amax = float(np.min(arr)), float(np.max(arr))
            if amax - amin < 1e-9: return np.ones_like(arr)
            return (arr - amin) / (amax - amin)
        return np.clip((arr - p5) / (p95 - p5), 0, 1)
