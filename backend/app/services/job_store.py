import uuid
from typing import Dict, Optional, Any

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "stage": "queued",
            "progress": 0,
            "error": None,
            "title": None,
            "hook": None,
            "script": None,
            "scenes": [],
            "video_url": None,
        }
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

job_store = JobStore()
