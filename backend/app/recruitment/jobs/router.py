from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
import uuid

from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.schemas.recruitment import (
    JobCreate, JobUpdate, JobResponse, CandidateRankingItem, JobRankingResponse, CandidateMatchResponse
)
from app.api.deps import require_recruitment_read, require_recruitment_write
from app.recruitment.ranking.matcher import compute_candidate_job_match

router = APIRouter()

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

@router.post("", response_model=JobResponse)
async def create_job(
    job_in: JobCreate,
    current_user: User = Depends(require_recruitment_write)
):
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    job_id = f"JOB-{uuid.uuid4().hex[:6].upper()}"
    
    now = datetime.now(timezone.utc)
    job = Job(
        organization_id=org_ref,
        job_id=job_id,
        title=job_in.title,
        description=job_in.description,
        required_skills=[s.strip() for s in job_in.required_skills if s.strip()],
        minimum_experience=job_in.minimum_experience,
        qualification=job_in.qualification,
        location=job_in.location,
        employment_type=job_in.employment_type,
        status=job_in.status,
        created_by=current_user.email,
        created_at=now,
        updated_at=now
    )
    await job.insert()

    return JobResponse(
        id=str(job.id),
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        minimum_experience=job.minimum_experience,
        qualification=job.qualification,
        location=job.location,
        employment_type=job.employment_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    jobs = await Job.find({"organization_id.$id": org_id}).to_list()
    
    if status and status.lower() != 'all':
        jobs = [j for j in jobs if j.status.lower() == status.lower()]

    jobs = sorted(jobs, key=lambda x: x.created_at, reverse=True)

    return [
        JobResponse(
            id=str(j.id),
            job_id=j.job_id,
            title=j.title,
            description=j.description,
            required_skills=j.required_skills,
            minimum_experience=j.minimum_experience,
            qualification=j.qualification,
            location=j.location,
            employment_type=j.employment_type,
            status=j.status,
            created_by=j.created_by,
            created_at=j.created_at,
            updated_at=j.updated_at
        ) for j in jobs
    ]

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=str(job.id),
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        minimum_experience=job.minimum_experience,
        qualification=job.qualification,
        location=job.location,
        employment_type=job.employment_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_in: JobUpdate,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_in.title is not None: job.title = job_in.title
    if job_in.description is not None: job.description = job_in.description
    if job_in.required_skills is not None: job.required_skills = [s.strip() for s in job_in.required_skills if s.strip()]
    if job_in.minimum_experience is not None: job.minimum_experience = job_in.minimum_experience
    if job_in.qualification is not None: job.qualification = job_in.qualification
    if job_in.location is not None: job.location = job_in.location
    if job_in.employment_type is not None: job.employment_type = job_in.employment_type
    if job_in.status is not None: job.status = job_in.status

    job.updated_at = datetime.now(timezone.utc)
    await job.save()

    return JobResponse(
        id=str(job.id),
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        minimum_experience=job.minimum_experience,
        qualification=job.qualification,
        location=job.location,
        employment_type=job.employment_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    await job.delete()
    return {"message": "Job deleted successfully"}

@router.post("/{job_id}/open", response_model=JobResponse)
async def open_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = "Open"
    job.updated_at = datetime.now(timezone.utc)
    await job.save()
    
    return JobResponse(
        id=str(job.id),
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        minimum_experience=job.minimum_experience,
        qualification=job.qualification,
        location=job.location,
        employment_type=job.employment_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.post("/{job_id}/close", response_model=JobResponse)
async def close_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = "Closed"
    job.updated_at = datetime.now(timezone.utc)
    await job.save()
    
    return JobResponse(
        id=str(job.id),
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        minimum_experience=job.minimum_experience,
        qualification=job.qualification,
        location=job.location,
        employment_type=job.employment_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

# --- RANKING ENDPOINTS ---

@router.post("/{job_id}/rank", response_model=JobRankingResponse)
async def rank_candidates_for_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id

    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = await Candidate.find({"organization_id.$id": org_id}).to_list()
    
    matches_list = []
    now = datetime.now(timezone.utc)

    for cand in candidates:
        match_data = compute_candidate_job_match(job, cand)
        
        existing = await CandidateMatch.find_one(
            {"organization_id.$id": org_id},
            CandidateMatch.job_id == job_id,
            CandidateMatch.candidate_id == cand.candidate_id
        )
        
        if existing:
            existing.match_score = match_data["match_score"]
            existing.matched_skills = match_data["matched_skills"]
            existing.missing_skills = match_data["missing_skills"]
            existing.experience_match = match_data["experience_match"]
            existing.education_match = match_data["education_match"]
            existing.semantic_similarity = match_data["semantic_similarity"]
            existing.explanation = match_data["explanation"]
            existing.updated_at = now
            await existing.save()
            match_doc = existing
        else:
            match_doc = CandidateMatch(
                organization_id=org_ref,
                job_id=job_id,
                candidate_id=cand.candidate_id,
                match_score=match_data["match_score"],
                matched_skills=match_data["matched_skills"],
                missing_skills=match_data["missing_skills"],
                experience_match=match_data["experience_match"],
                education_match=match_data["education_match"],
                semantic_similarity=match_data["semantic_similarity"],
                explanation=match_data["explanation"],
                created_at=now,
                updated_at=now
            )
            await match_doc.insert()

        matches_list.append((cand, match_doc))

    matches_list.sort(key=lambda x: x[1].match_score, reverse=True)

    rankings = [
        CandidateRankingItem(
            rank=idx + 1,
            candidate_id=cand.candidate_id,
            name=cand.name,
            email=cand.email,
            experience=cand.experience,
            skills=cand.skills,
            degree=cand.degree,
            match_score=m.match_score,
            matched_skills=m.matched_skills,
            missing_skills=m.missing_skills,
            experience_match=m.experience_match,
            education_match=m.education_match,
            semantic_similarity=m.semantic_similarity,
            explanation=m.explanation
        ) for idx, (cand, m) in enumerate(matches_list)
    ]

    return JobRankingResponse(
        job_id=job.job_id,
        job_title=job.title,
        total_candidates=len(rankings),
        rankings=rankings
    )

@router.get("/{job_id}/ranking", response_model=JobRankingResponse)
async def get_candidate_ranking_for_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    job = await Job.find_one({"organization_id.$id": org_id}, Job.job_id == job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    matches = await CandidateMatch.find(
        {"organization_id.$id": org_id},
        CandidateMatch.job_id == job_id
    ).to_list()

    if not matches:
        return await rank_candidates_for_job(job_id=job_id, current_user=current_user)

    matches.sort(key=lambda x: x.match_score, reverse=True)

    cands_map = {
        c.candidate_id: c for c in await Candidate.find({"organization_id.$id": org_id}).to_list()
    }

    rankings = []
    for idx, m in enumerate(matches):
        cand = cands_map.get(m.candidate_id)
        if not cand:
            continue
        rankings.append(
            CandidateRankingItem(
                rank=idx + 1,
                candidate_id=cand.candidate_id,
                name=cand.name,
                email=cand.email,
                experience=cand.experience,
                skills=cand.skills,
                degree=cand.degree,
                match_score=m.match_score,
                matched_skills=m.matched_skills,
                missing_skills=m.missing_skills,
                experience_match=m.experience_match,
                education_match=m.education_match,
                semantic_similarity=m.semantic_similarity,
                explanation=m.explanation
            )
        )

    return JobRankingResponse(
        job_id=job.job_id,
        job_title=job.title,
        total_candidates=len(rankings),
        rankings=rankings
    )

@router.post("/{job_id}/rankings/refresh", response_model=JobRankingResponse)
async def refresh_candidate_ranking_for_job(
    job_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    # Re-run the ranking logic
    return await rank_candidates_for_job(job_id=job_id, current_user=current_user)

@router.get("/{job_id}/rankings/{candidate_id}", response_model=CandidateMatchResponse)
async def get_candidate_job_match(
    job_id: str,
    candidate_id: str,
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    match_doc = await CandidateMatch.find_one(
        {"organization_id.$id": org_id},
        CandidateMatch.job_id == job_id,
        CandidateMatch.candidate_id == candidate_id
    )
    if not match_doc:
        raise HTTPException(status_code=404, detail="Match not found")
        
    return CandidateMatchResponse(
        candidate_id=match_doc.candidate_id,
        job_id=match_doc.job_id,
        match_score=match_doc.match_score,
        matched_skills=match_doc.matched_skills,
        missing_skills=match_doc.missing_skills,
        experience_match=match_doc.experience_match,
        education_match=match_doc.education_match,
        semantic_similarity=match_doc.semantic_similarity,
        explanation=match_doc.explanation
    )

@router.delete("/{job_id}/rankings/{candidate_id}")
async def remove_candidate_from_ranking(
    job_id: str,
    candidate_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    match_doc = await CandidateMatch.find_one(
        {"organization_id.$id": org_id},
        CandidateMatch.job_id == job_id,
        CandidateMatch.candidate_id == candidate_id
    )
    if not match_doc:
        raise HTTPException(status_code=404, detail="Match not found")
        
    await match_doc.delete()
    return {"message": "Candidate match removed successfully"}
