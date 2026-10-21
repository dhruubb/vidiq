from __future__ import annotations

from typing import Dict, Optional
from threading import Lock

from ..schemas import RankedClipsResponse


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, RankedClipsResponse] = {}
        self._locks: Dict[str, Lock] = {}

    def init_job(self, job_id: str) -> None:
        self._locks[job_id] = Lock()
        self._jobs[job_id] = RankedClipsResponse(job_id=job_id, results=[])

    def complete_job(self, job_id: str, results) -> None:
        if job_id not in self._jobs:
            return
        with self._locks[job_id]:
            self._jobs[job_id] = RankedClipsResponse(job_id=job_id, results=results)

    def get_status(self, job_id: str) -> Optional[RankedClipsResponse]:
        return self._jobs.get(job_id)

    def remove_job(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._locks.pop(job_id, None)


