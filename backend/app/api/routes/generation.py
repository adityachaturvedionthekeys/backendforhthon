from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import fastapi.responses
from app.schemas.generation import (
    GenerateRequest, 
    GenerateResponse, 
    JobStatusResponse,
    RegenerateSceneRequest
)
from app.services.job_store import job_store
from app.services.orchestrator import run_generation_pipeline, regenerate_scene_pipeline

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_content(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = job_store.create_job()
    background_tasks.add_task(
        run_generation_pipeline,
        job_id,
        request.topic,
        request.duration,
        request.style
    )
    return GenerateResponse(job_id=job_id, status="queued")

@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.get("job_id"),
        status=job.get("status"),
        stage=job.get("stage"),
        progress=job.get("progress"),
        error=job.get("error")
    )

@router.get("/result/{job_id}")
def get_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "completed":
        return fastapi.responses.JSONResponse(
            status_code=425, # Too Early 
            content={"detail": "Result is not ready yet"}
        )
        
    return {
        "job_id": job_id,
        "status": "completed",
        "title": job.get("title"),
        "hook": job.get("hook"),
        "script": job.get("script"),
        "scenes": job.get("scenes"),
        "video_url": job.get("video_url"),
        "duration": sum(s.get("duration", 0) for s in job.get("scenes", []))
    }

@router.post("/regenerate-scene", status_code=status.HTTP_202_ACCEPTED)
def regenerate_scene(request: RegenerateSceneRequest, background_tasks: BackgroundTasks):
    job = job_store.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Can only regenerate scenes for completed jobs.")
        
    background_tasks.add_task(regenerate_scene_pipeline, request.job_id, request.scene_id)
    
    return {
        "job_id": request.job_id,
        "status": "queued",
        "message": f"Regenerating scene {request.scene_id}"
    }
