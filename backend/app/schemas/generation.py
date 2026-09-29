from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0)
    style: str = Field(..., min_length=1)

class GenerateResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: int

class RegenerateSceneRequest(BaseModel):
    job_id: str = Field(..., min_length=1)
    scene_id: int = Field(..., gt=0)
