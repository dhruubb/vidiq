from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Tuple

import hashlib
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it


class ClipsClient:
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self) -> None:
        # Read API key; if missing, operate in local-fallback mode (no exceptions)
        api_key = os.getenv("CLIPS_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.api_key = api_key.strip() if api_key else None
        # For OpenAI, default to https://api.openai.com/v1
        self.base_url = os.getenv("CLIPS_API_BASE", self.DEFAULT_BASE_URL)

    def _auth_headers(self) -> dict:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    @retry(wait=wait_exponential(multiplier=1, min=1, max=6), stop=stop_after_attempt(2))
    def _embed_text(self, text: str) -> List[float]:
        """Embedding with graceful fallback: try OpenAI (if key present), else local hashing."""
        text = (text or "").strip()
        if not text:
            return self._embed_text_local("")

        if self.api_key:
            try:
                url = f"{self.base_url}/embeddings"
                payload = {
                    "model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                    "input": text,
                }
                headers = self._auth_headers() | {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                emb = data.get("data", [{}])[0].get("embedding", [])
                if emb:
                    return emb
                print("Warn: Empty embedding from API; using local fallback")
            except Exception as e:
                print(f"Warn: OpenAI embed failed, using local fallback. Reason: {e}")

        return self._embed_text_local(text)

    def _embed_text_local(self, text: str, dim: int = 512) -> List[float]:
        """Simple hashed bag-of-words embedding to ensure search never blocks."""
        import re, math
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return [0.0] * dim
        vec = [0.0] * dim
        for tok in tokens:
            h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [float(v / norm) for v in vec]

    def _embed_video(self, video_path: Path, metadata: dict = None) -> List[float]:
        """Create enhanced video description from filename and metadata."""
        name = video_path.stem.replace("_", " ").replace("-", " ")
        
        # Build description from available metadata
        desc_parts = [f"video clip named '{name}'"]
        
        if metadata:
            # Add face information
            face_count = metadata.get('face_count', 0)
            if face_count > 0:
                desc_parts.append(f"containing {face_count} {'face' if face_count == 1 else 'faces'}")
            
            # Add quality indicators
            blur_score = metadata.get('blur_score', 0)
            if blur_score > 0.7:
                desc_parts.append("high quality sharp footage")
            elif blur_score < 0.3:
                desc_parts.append("blurry or low quality")
            
            motion_score = metadata.get('motion_score', 0)
            if motion_score < 0.3:
                desc_parts.append("stable camera work")
            elif motion_score > 0.7:
                desc_parts.append("dynamic or moving footage")
        
        desc = ". ".join(desc_parts) + "."
        return self._embed_text(desc)

    def _cache_path(self, cache_dir: Path, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{digest}.json"

    def _get_or_create_video_embedding(self, clip: Path, cache_dir: Path, metadata: dict = None) -> List[float]:
        # Include metadata in cache key if available
        meta_str = json.dumps(metadata, sort_keys=True) if metadata else ""
        key = f"video_text_embed::{clip.resolve()}::{clip.stat().st_mtime}::{meta_str}"
        cp = self._cache_path(cache_dir, key)
        if cp.exists():
            try:
                return json.loads(cp.read_text()).get("embedding", [])
            except Exception:
                pass
        embedding = self._embed_video(clip, metadata)
        cp.write_text(json.dumps({"embedding": embedding}))
        return embedding

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        import math
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        na = math.sqrt(sum(a * a for a in vec_a))
        nb = math.sqrt(sum(b * b for b in vec_b))
        if na == 0 or nb == 0:
            return 0.0
        return float(dot / (na * nb))

    def rank_by_query(self, query_text: str, clips: Iterable[Path], cache_dir: Path, metadata_map: dict = None) -> List[Tuple[str, float]]:
        """
        Rank clips by query similarity.
        metadata_map: dict mapping clip filename to ClipScore metadata
        """
        # Always produce a query embedding (local or remote)
        query_vec = self._embed_text(query_text)
        
        ranked: List[Tuple[str, float]] = []
        for clip in clips:
            try:
                metadata = None
                if metadata_map and clip.name in metadata_map:
                    item = metadata_map[clip.name]
                    metadata = {
                        'face_count': item.face_count,
                        'blur_score': item.blur_score,
                        'motion_score': item.motion_score,
                    }
                vvec = self._get_or_create_video_embedding(clip, cache_dir, metadata)
                if not vvec:
                    print(f"Warning: No embedding for {clip.name}, using 0.0")
                    ranked.append((clip.name, 0.0))
                    continue
                score = self._cosine_similarity(query_vec, vvec)
                ranked.append((clip.name, score))
            except Exception as e:
                print(f"Error processing clip {clip.name}: {str(e)}")
                ranked.append((clip.name, 0.0))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


