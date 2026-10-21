import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, Query, Depends
from fastapi.responses import FileResponse, JSONResponse

from ..services.jobs import JobManager
from ..services.video import VideoAnalyzer
from ..services.clips import ClipsClient
from ..schemas import (
    AnalysisRequestWeights,
    ClipScore,
    QueryClipsRequest,
    RankedClipsResponse,
    DownloadQueryRequest,
)
from .auth import get_current_active_user
from ..auth import User


router = APIRouter()
job_manager = JobManager()

# Initialize ClipsClient lazily to handle missing API key gracefully
_clips_client = None

def get_clips_client():
    """Get or create ClipsClient instance, handling missing API key gracefully."""
    global _clips_client
    if _clips_client is None:
        try:
            _clips_client = ClipsClient()
        except ValueError as e:
            # API key not set - this is OK for non-query features
            print(f"Warning: ClipsClient not initialized: {str(e)}")
            print("CLIPS Query feature will not be available until API key is set.")
            _clips_client = None
    return _clips_client


def _ensure_job_dir(job_id: str) -> Path:
    base = Path(tempfile.gettempdir()) / "vcsp" / job_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "clips").mkdir(parents=True, exist_ok=True)
    (base / "thumbs").mkdir(parents=True, exist_ok=True)
    (base / "cache").mkdir(parents=True, exist_ok=True)
    return base


@router.post("/upload-zip")
async def upload_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    blur_weight: float = Query(0.34, ge=0, le=1),
    motion_weight: float = Query(0.33, ge=0, le=1),
    face_weight: float = Query(0.33, ge=0, le=1),
    frame_sample_rate: int = Query(24, ge=1, le=100),
    resize_width: int = Query(320, ge=64, le=1920),
    motion_method: str = Query("diff"),  # 'diff' or 'flow'
    max_frames_per_video: int = Query(300, ge=10, le=1000),
    parallel_workers: int = Query(4, ge=1, le=16),
    current_user: User = Depends(get_current_active_user),
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided or filename is missing")
        if not file.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail=f"Only .zip files are supported for this endpoint. Received: {file.filename}")

        job_id = str(uuid.uuid4())
        base = _ensure_job_dir(job_id)

        # Sanitize filename to prevent path traversal
        safe_filename = Path(file.filename).name
        zip_path = base / safe_filename
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        with open(zip_path, "wb") as f:
            f.write(content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(base / "clips")

        weights = AnalysisRequestWeights(blur_weight=blur_weight, motion_weight=motion_weight, face_weight=face_weight)

        job_manager.init_job(job_id)

        def _process_job():
            analyzer = VideoAnalyzer(
                frame_sample_rate=frame_sample_rate,
                resize_width=resize_width,
                motion_method=motion_method,
                max_frames_per_video=max_frames_per_video,
                parallel_workers=parallel_workers,
            )
            results = analyzer.analyze_directory(base / "clips", base / "thumbs", weights)
            job_manager.complete_job(job_id, results)

        background_tasks.add_task(_process_job)
        return RankedClipsResponse(job_id=job_id, results=[])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@router.post("/upload-files")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    blur_weight: float = Query(0.34, ge=0, le=1),
    motion_weight: float = Query(0.33, ge=0, le=1),
    face_weight: float = Query(0.33, ge=0, le=1),
    frame_sample_rate: int = Query(24, ge=1, le=100),
    resize_width: int = Query(320, ge=64, le=1920),
    motion_method: str = Query("diff"),  # 'diff' or 'flow'
    max_frames_per_video: int = Query(300, ge=10, le=1000),
    parallel_workers: int = Query(4, ge=1, le=16),
    current_user: User = Depends(get_current_active_user),
):
    try:
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        job_id = str(uuid.uuid4())
        base = _ensure_job_dir(job_id)
        clips_dir = base / "clips"
        
        uploaded_count = 0
        for up in files:
            if not up.filename:
                continue
            suffix = Path(up.filename).suffix.lower()
            if suffix not in {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".mpeg"}:
                continue
            target = clips_dir / Path(up.filename).name
            try:
                content = await up.read()
                with open(target, "wb") as f:
                    f.write(content)
                uploaded_count += 1
            except Exception as e:
                continue
        
        if uploaded_count == 0:
            raise HTTPException(status_code=400, detail="No valid video files found. Supported formats: .mp4, .mov, .mkv, .avi, .webm")

        weights = AnalysisRequestWeights(blur_weight=blur_weight, motion_weight=motion_weight, face_weight=face_weight)
        job_manager.init_job(job_id)

        def _process_job():
            analyzer = VideoAnalyzer(
                frame_sample_rate=frame_sample_rate,
                resize_width=resize_width,
                motion_method=motion_method,
                max_frames_per_video=max_frames_per_video,
                parallel_workers=parallel_workers,
            )
            results = analyzer.analyze_directory(clips_dir, base / "thumbs", weights)
            job_manager.complete_job(job_id, results)

        background_tasks.add_task(_process_job)
        return RankedClipsResponse(job_id=job_id, results=[])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@router.get("/results/{job_id}", response_model=RankedClipsResponse)
async def get_results(job_id: str, current_user: User = Depends(get_current_active_user)):
    try:
        status = job_manager.get_status(job_id)
        if status is None:
            # Check if job directory exists (job might have been created but not completed)
            base = Path(tempfile.gettempdir()) / "vcsp" / job_id
            if base.exists():
                # Job exists but not in memory (server restart?)
                raise HTTPException(status_code=404, detail="Job not found in memory. Please re-upload your videos.")
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_results: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/thumbnail/{job_id}/{name}")
async def get_thumbnail(job_id: str, name: str, token: str = Query(...)):
    # Validate token manually
    from jose import jwt, JWTError
    from ..auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    base = Path(tempfile.gettempdir()) / "vcsp" / job_id / "thumbs"
    path = base / f"{name}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(str(path))


@router.get("/video/{job_id}/{name}")
async def get_video(job_id: str, name: str, token: str = Query(...)):
    # Validate token manually since <video> tag can't send headers
    # We import the auth logic here to avoid circular imports if possible, or use the existing dependency
    from .auth import get_current_user
    
    # We can't easily use the Depends(get_current_user) with query param without changing the dependency.
    # So we'll do a manual check using the same logic.
    from jose import jwt, JWTError
    from ..auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    base = Path(tempfile.gettempdir()) / "vcsp" / job_id / "clips"
    found_path = _find_clip_file(base, name)
    if not found_path or not found_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(str(found_path))


def _find_clip_file(clips_dir: Path, filename: str) -> Optional[Path]:
    """Find a clip file, searching recursively in subdirectories."""
    # First try direct path
    direct_path = clips_dir / filename
    if direct_path.exists() and direct_path.is_file():
        return direct_path
    
    # Search recursively
    for video_file in clips_dir.rglob(filename):
        if video_file.is_file():
            return video_file
    
    # Try with just the name (without path components)
    name_only = Path(filename).name
    for video_file in clips_dir.rglob(name_only):
        if video_file.is_file():
            return video_file
    
    return None


@router.post("/download-top/{job_id}")
async def download_top(job_id: str, k: int = Query(5), current_user: User = Depends(get_current_active_user)):
    try:
        status = job_manager.get_status(job_id)
        if status is None or not status.results:
            raise HTTPException(status_code=404, detail="Results not found")

        base = Path(tempfile.gettempdir()) / "vcsp" / job_id
        clips_dir = base / "clips"

        if not clips_dir.exists():
            raise HTTPException(status_code=404, detail="Clips directory not found")

        top = sorted(status.results, key=lambda r: r.final_score, reverse=True)[: max(1, k)]
        out_zip = base / f"top_{k}.zip"
        
        # Remove existing zip if it exists
        if out_zip.exists():
            out_zip.unlink()
        
        # Create zip file
        files_added = 0
        try:
            with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                for item in top:
                    clip_path = _find_clip_file(clips_dir, item.filename)
                    if clip_path and clip_path.exists() and clip_path.is_file():
                        # Use just the filename in the zip, not the full path
                        zf.write(clip_path, arcname=Path(item.filename).name)
                        files_added += 1
        except Exception as e:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to create zip file: {str(e)}")
        
        if files_added == 0:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=404, detail="No video files found to download")
        
        if not out_zip.exists() or out_zip.stat().st_size == 0:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=500, detail="Failed to create zip file (empty)")
        
        return FileResponse(
            str(out_zip),
            filename=f"top_{k}_clips.zip",
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=top_{k}_clips.zip"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in download_top: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/query-clips", response_model=RankedClipsResponse)
async def query_clips(payload: QueryClipsRequest, current_user: User = Depends(get_current_active_user)):
    try:
        if not payload.query or not payload.query.strip():
            raise HTTPException(status_code=400, detail="Query text is required")
        
        base = Path(tempfile.gettempdir()) / "vcsp" / payload.job_id
        status = job_manager.get_status(payload.job_id)
        
        if status is None:
            # Check if job directory exists
            if not base.exists():
                raise HTTPException(status_code=404, detail=f"Job {payload.job_id} not found. Please re-upload your videos.")
            # Job exists but not in memory (server restart), try to load from disk
            raise HTTPException(status_code=404, detail="Job not found in memory. Please re-upload your videos and analyze again.")
        
        if not status.results or len(status.results) == 0:
            raise HTTPException(status_code=404, detail="Job analysis not completed yet. Please wait for analysis to finish.")

        clips_dir = base / "clips"
        thumbs_dir = base / "thumbs"
        cache_dir = base / "cache"

        if not clips_dir.exists():
            raise HTTPException(status_code=404, detail="Clips directory not found")

        # Create metadata map - use filename (name only) as key for lookup
        # The rank_by_query function uses clip.name, so we need to map by filename
        metadata_map = {Path(r.filename).name: r for r in status.results}
        
        # Find actual clip files (handle subdirectories)
        clip_paths = []
        for r in status.results:
            clip_path = _find_clip_file(clips_dir, r.filename)
            if clip_path:
                clip_paths.append(clip_path)
        
        if not clip_paths:
            raise HTTPException(status_code=404, detail="No video clips found")
        
        # Call rank_by_query - it uses clip.name to look up in metadata_map
        clips_client = get_clips_client()
        if clips_client is None:
            # Fallback: pure text→metadata matching (independent of quality ranking)
            # Uses simple keyword features; does NOT use the original final_score at all.
            def _simple_score(item: ClipScore, q: str) -> float:
                ql = q.lower()
                name = Path(item.filename).stem.replace('_', ' ').replace('-', ' ').lower()
                score = 0.0
                # filename contains query tokens
                if ql and ql in name:
                    score += 0.4
                # faces intent
                if any(k in ql for k in ["face", "faces", "person", "people", "speaker"]):
                    score += min(0.6, 0.12 * max(0, int(item.face_count)))
                # sharpness intent
                if any(k in ql for k in ["sharp", "high quality", "clear", "hd", "detailed"]):
                    score += float(item.blur_score) * 0.6
                # stability intent (motion_score already favors stability)
                if any(k in ql for k in ["stable", "steady", "no shake", "tripod", "still"]):
                    score += float(item.motion_score) * 0.6
                # generic content words
                for kw in ["stage", "talk", "interview", "crowd", "screen", "slide"]:
                    if kw in ql and kw in name:
                        score += 0.2
                return float(score)

            ranked_local = [(Path(r.filename).name, _simple_score(r, payload.query)) for r in status.results]
            ranked_local.sort(key=lambda t: t[1], reverse=True)
            ranked = ranked_local
        else:
            try:
                ranked = clips_client.rank_by_query(
                    query_text=payload.query,
                    clips=clip_paths,
                    cache_dir=cache_dir,
                    metadata_map=metadata_map,
                )
            except Exception as e:
                error_msg = str(e)
                print(f"Error in rank_by_query: {error_msg}")
                # If embedding fails, return results sorted by original scores
                print("Falling back to original score-based ranking")
                ranked = [(Path(r.filename).name, r.final_score) for r in status.results]

        # Create mapping from filename to original result
        mapped = {Path(r.filename).name: r for r in status.results}
        reweighted = []
        for fname, score in ranked:
            # fname is clip.name from rank_by_query
            if fname in mapped:
                item = mapped[fname]
                # Create new instance with updated final_score
                reweighted.append(ClipScore(
                    filename=item.filename,
                    blur_score=item.blur_score,
                    motion_score=item.motion_score,
                    face_score=item.face_score,
                    face_count=item.face_count,
                    final_score=float(score),
                    thumbnail_name=item.thumbnail_name,
                ))

        return RankedClipsResponse(job_id=payload.job_id, results=sorted(reweighted, key=lambda r: r.final_score, reverse=True))
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a proper error response
        import traceback
        print(f"Error in query_clips: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/download-query/{job_id}")
async def download_query(job_id: str, payload: DownloadQueryRequest, current_user: User = Depends(get_current_active_user)):
    """Download top k clips from query results by filenames."""
    try:
        base = Path(tempfile.gettempdir()) / "vcsp" / job_id
        clips_dir = base / "clips"

        if not clips_dir.exists():
            raise HTTPException(status_code=404, detail="Clips directory not found")

        # Take top k filenames
        top_filenames = payload.filenames[:max(1, payload.k)]
        out_zip = base / f"query_top_{payload.k}.zip"
        
        # Remove existing zip if it exists
        if out_zip.exists():
            out_zip.unlink()
        
        # Create zip file
        files_added = 0
        try:
            with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                for filename in top_filenames:
                    clip_path = _find_clip_file(clips_dir, filename)
                    if clip_path and clip_path.exists() and clip_path.is_file():
                        # Use just the filename in the zip, not the full path
                        zf.write(clip_path, arcname=Path(filename).name)
                        files_added += 1
        except Exception as e:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to create zip file: {str(e)}")
        
        if files_added == 0:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=404, detail="No video files found to download")
        
        if not out_zip.exists() or out_zip.stat().st_size == 0:
            if out_zip.exists():
                out_zip.unlink()
            raise HTTPException(status_code=500, detail="Failed to create zip file (empty)")
        
        return FileResponse(
            str(out_zip),
            filename=f"query_top_{payload.k}_clips.zip",
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=query_top_{payload.k}_clips.zip"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in download_query: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/cleanup/{job_id}")
async def cleanup(job_id: str, current_user: User = Depends(get_current_active_user)):
    base = Path(tempfile.gettempdir()) / "vcsp" / job_id
    if base.exists():
        shutil.rmtree(base)
    job_manager.remove_job(job_id)
    return JSONResponse({"ok": True})


