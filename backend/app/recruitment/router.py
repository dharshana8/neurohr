from fastapi import APIRouter
from app.recruitment.jobs.router import router as jobs_router
from app.recruitment.candidates.router import router as candidates_router

router = APIRouter()

router.include_router(jobs_router, prefix="/jobs", tags=["recruitment-jobs"])
router.include_router(candidates_router, prefix="/candidates", tags=["recruitment-candidates"])

