from typing import List, Optional
from pydantic import BaseModel


class AnalysisRequestWeights(BaseModel):
    blur_weight: float = 0.34
    motion_weight: float = 0.33
    face_weight: float = 0.33


class ClipScore(BaseModel):
    filename: str
    blur_score: float
    motion_score: float
    face_score: float
    face_count: int
    unique_face_count: int = 0
    final_score: float
    thumbnail_name: str


class RankedClipsResponse(BaseModel):
    job_id: str
    results: List[ClipScore]


class QueryClipsRequest(BaseModel):
    job_id: str
    query: str


class DownloadQueryRequest(BaseModel):
    filenames: List[str]
    k: int = 5


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

