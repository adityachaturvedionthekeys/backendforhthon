from fastapi import APIRouter, HTTPException, status
from app.schemas.generation import (
    GenerateRequest, 
    GenerateResponse, 
    JobStatusResponse,
    RegenerateSceneRequest
)
import fastapi.responses
from app.services.job_store import job_store

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_content(request: GenerateRequest):
    job_id = job_store.create_job()
    return GenerateResponse(job_id=job_id, status="queued")

@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**job)

@router.get("/result/{job_id}")
def get_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "completed":
        return fastapi.responses.JSONResponse(
            status_code=status.HTTP_202_ACCEPTED, 
            content={"detail": "Result is not ready yet"}
        )
        
    # Future contract, not implemented for this milestone
    return {
        "job_id": job_id,
        "status": "completed",
        "title": "Placeholder Title",
        "hook": "Placeholder Hook",
        "script": "Placeholder Script",
        "scenes": [],
        "video_url": "https://example.com/video.mp4",
        "duration": 45
    }

@router.post("/regenerate-scene")
def regenerate_scene(request: RegenerateSceneRequest):
    # Validation is handled by Pydantic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Scene regeneration is not implemented yet."
    )
