from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import JOBS, CANDIDATES
from app.api.v1.auth import get_current_user

router = APIRouter()

class JobCreate(BaseModel):
    title: str
    department: str
    location: str
    openings: int
    salary_range: str

@router.get("/jobs")
def get_jobs(current_user: dict = Depends(get_current_user)):
    return JOBS

@router.post("/jobs")
def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
    new_job = {
        "id": f"JOB-{len(JOBS) + 101}",
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "openings": job.openings,
        "status": "OPEN",
        "salary_range": job.salary_range,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d")
    }
    JOBS.insert(0, new_job)
    return new_job

@router.get("/candidates")
def get_candidates(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if job_id:
        return [c for c in CANDIDATES if c.get("job_id") == job_id]
    return CANDIDATES

@router.get("/jobs/{job_id}/ranking")
def get_job_ranking(job_id: str, current_user: dict = Depends(get_current_user)):
    job = next((j for j in JOBS if j["id"] == job_id), None)
    cands = [c for c in CANDIDATES if c.get("job_id") == job_id]
    sorted_cands = sorted(cands, key=lambda x: x.get("match_score", 0), reverse=True)
    return {
        "job": job,
        "ranked_candidates": sorted_cands
    }

