import os
import re
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.user import User
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.schemas.recruitment import CandidateResponse, CandidateCreate, CandidateUpdate, CandidateStatusUpdate
from app.api.deps import require_recruitment_read, require_recruitment_write
from app.recruitment.resume_parser.parser import extract_text_from_file, parse_resume_text

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads", "resumes")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream"
}

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return str(org_link)

def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename)
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', base)

@router.post("/upload", response_model=CandidateResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_recruitment_write)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Only PDF and DOCX files are supported."
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file MIME type '{file.content_type}'. Only PDF and DOCX files are supported."
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 10MB.")

    org_id = get_org_id(current_user.organization_id)
    cand_id = f"CAND-{uuid.uuid4().hex[:6].upper()}"
    
    safe_filename = sanitize_filename(file.filename)
    target_dir = os.path.join(UPLOAD_DIR, str(org_id), cand_id)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    raw_text = extract_text_from_file(file_path)
    parsed = parse_resume_text(raw_text)

    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    now = datetime.now(timezone.utc)

    candidate = Candidate(
        organization_id=org_ref,
        candidate_id=cand_id,
        name=parsed["name"],
        email=parsed["email"],
        phone=parsed["phone"],
        education=parsed["education"],
        degree=parsed["degree"],
        experience=parsed["experience"],
        skills=parsed["skills"],
        projects=parsed["projects"],
        certifications=parsed["certifications"],
        previous_companies=parsed["previous_companies"],
        job_titles=parsed["job_titles"],
        resume_file=os.path.relpath(file_path, UPLOAD_DIR),
        resume_text=parsed["resume_text"],
        source="Upload",
        status="NEW",
        parsing_status=parsed["parsing_status"],
        parsing_warning=parsed["parsing_warning"],
        created_at=now,
        updated_at=now
    )
    await candidate.insert()

    return CandidateResponse(
        id=str(candidate.id),
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        education=candidate.education,
        degree=candidate.degree,
        experience=candidate.experience,
        skills=candidate.skills,
        projects=candidate.projects,
        certifications=candidate.certifications,
        previous_companies=candidate.previous_companies,
        job_titles=candidate.job_titles,
        resume_file=candidate.resume_file,
        source=candidate.source,
        status=candidate.status,
        parsing_status=candidate.parsing_status,
        parsing_warning=candidate.parsing_warning,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )

@router.get("", response_model=List[CandidateResponse])
async def list_candidates(
    search: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    min_experience: Optional[float] = Query(None),
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    candidates = await Candidate.find({"organization_id.$id": org_id}).to_list()

    filtered = []
    for c in candidates:
        if search:
            s_lower = search.lower()
            if not (s_lower in c.name.lower() or (c.email and s_lower in c.email.lower()) or any(s_lower in sk.lower() for sk in c.skills) or (c.degree and s_lower in c.degree.lower())):
                continue
        if skill and skill.lower() != 'all':
            if not any(skill.lower() in sk.lower() for sk in c.skills):
                continue
        if min_experience is not None:
            if c.experience < min_experience:
                continue
        filtered.append(c)

    filtered = sorted(filtered, key=lambda x: x.created_at, reverse=True)

    return [
        CandidateResponse(
            id=str(c.id),
            candidate_id=c.candidate_id,
            name=c.name,
            email=c.email,
            phone=c.phone,
            education=c.education,
            degree=c.degree,
            experience=c.experience,
            skills=c.skills,
            projects=c.projects,
            certifications=c.certifications,
            previous_companies=c.previous_companies,
            job_titles=c.job_titles,
            resume_file=c.resume_file,
            source=c.source,
            status=c.status,
            parsing_status=c.parsing_status,
            parsing_warning=c.parsing_warning,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in filtered
    ]

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    candidate = await Candidate.find_one({"organization_id.$id": org_id}, Candidate.candidate_id == candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateResponse(
        id=str(candidate.id),
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        education=candidate.education,
        degree=candidate.degree,
        experience=candidate.experience,
        skills=candidate.skills,
        projects=candidate.projects,
        certifications=candidate.certifications,
        previous_companies=candidate.previous_companies,
        job_titles=candidate.job_titles,
        resume_file=candidate.resume_file,
        source=candidate.source,
        status=candidate.status,
        parsing_status=candidate.parsing_status,
        parsing_warning=candidate.parsing_warning,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )

@router.get("/{candidate_id}/resume")
async def download_resume(
    candidate_id: str,
    current_user: User = Depends(require_recruitment_read)
):
    org_id = get_org_id(current_user.organization_id)
    candidate = await Candidate.find_one({"organization_id.$id": org_id}, Candidate.candidate_id == candidate_id)
    if not candidate or not candidate.resume_file:
        raise HTTPException(status_code=404, detail="Candidate or resume file not found")

    full_path = os.path.abspath(os.path.join(UPLOAD_DIR, candidate.resume_file))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Resume file does not exist on disk")

    ext = os.path.splitext(full_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=full_path,
        filename=os.path.basename(full_path),
        media_type=media_type
    )

@router.post("", response_model=CandidateResponse)
async def create_candidate(
    candidate_in: CandidateCreate,
    current_user: User = Depends(require_recruitment_write)
):
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    cand_id = f"CAND-{uuid.uuid4().hex[:6].upper()}"
    
    now = datetime.now(timezone.utc)
    candidate = Candidate(
        organization_id=org_ref,
        candidate_id=cand_id,
        name=candidate_in.name,
        email=candidate_in.email,
        phone=candidate_in.phone,
        education=candidate_in.education,
        degree=candidate_in.degree,
        experience=candidate_in.experience,
        skills=[s.strip() for s in candidate_in.skills if s.strip()],
        projects=candidate_in.projects,
        certifications=candidate_in.certifications,
        previous_companies=candidate_in.previous_companies,
        job_titles=candidate_in.job_titles,
        resume_file="",
        resume_text="",
        source=candidate_in.source,
        status=candidate_in.status,
        parsing_status="Completed",
        created_at=now,
        updated_at=now
    )
    await candidate.insert()

    return CandidateResponse(
        id=str(candidate.id),
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        education=candidate.education,
        degree=candidate.degree,
        experience=candidate.experience,
        skills=candidate.skills,
        projects=candidate.projects,
        certifications=candidate.certifications,
        previous_companies=candidate.previous_companies,
        job_titles=candidate.job_titles,
        resume_file=candidate.resume_file,
        source=candidate.source,
        status=candidate.status,
        parsing_status=candidate.parsing_status,
        parsing_warning=candidate.parsing_warning,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    candidate_in: CandidateUpdate,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    candidate = await Candidate.find_one({"organization_id.$id": org_id}, Candidate.candidate_id == candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if candidate_in.name is not None: candidate.name = candidate_in.name
    if candidate_in.email is not None: candidate.email = candidate_in.email
    if candidate_in.phone is not None: candidate.phone = candidate_in.phone
    if candidate_in.education is not None: candidate.education = candidate_in.education
    if candidate_in.degree is not None: candidate.degree = candidate_in.degree
    if candidate_in.experience is not None: candidate.experience = candidate_in.experience
    if candidate_in.skills is not None: candidate.skills = [s.strip() for s in candidate_in.skills if s.strip()]
    if candidate_in.projects is not None: candidate.projects = candidate_in.projects
    if candidate_in.certifications is not None: candidate.certifications = candidate_in.certifications
    if candidate_in.previous_companies is not None: candidate.previous_companies = candidate_in.previous_companies
    if candidate_in.job_titles is not None: candidate.job_titles = candidate_in.job_titles

    candidate.updated_at = datetime.now(timezone.utc)
    await candidate.save()

    return CandidateResponse(
        id=str(candidate.id),
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        education=candidate.education,
        degree=candidate.degree,
        experience=candidate.experience,
        skills=candidate.skills,
        projects=candidate.projects,
        certifications=candidate.certifications,
        previous_companies=candidate.previous_companies,
        job_titles=candidate.job_titles,
        resume_file=candidate.resume_file,
        source=candidate.source,
        status=candidate.status,
        parsing_status=candidate.parsing_status,
        parsing_warning=candidate.parsing_warning,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )

@router.delete("/actions/clear-all")
async def clear_all_candidates(
    current_user: User = Depends(require_recruitment_write)
):
    """Delete all candidate profiles, match ratings, and resume files for the tenant."""
    org_id = get_org_id(current_user.organization_id)
    candidates = await Candidate.find({"organization_id.$id": org_id}).to_list()
    count = len(candidates)
    for candidate in candidates:
        if candidate.resume_file:
            file_path = os.path.join(UPLOAD_DIR, candidate.resume_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        await CandidateMatch.find({"candidate_id": candidate.candidate_id}).delete()
        await candidate.delete()
    return {"message": f"Successfully removed {count} candidate profiles and files", "count": count}

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    candidate = await Candidate.find_one({"organization_id.$id": org_id}, Candidate.candidate_id == candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Remove stored resume file from disk
    if candidate.resume_file:
        file_path = os.path.join(UPLOAD_DIR, candidate.resume_file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    # Clean up associated candidate matching ratings
    await CandidateMatch.find({"candidate_id": candidate_id}).delete()
    await candidate.delete()
    return {"message": "Candidate and resume file deleted successfully"}

@router.post("/{candidate_id}/status", response_model=CandidateResponse)
async def update_candidate_status(
    candidate_id: str,
    status_in: CandidateStatusUpdate,
    current_user: User = Depends(require_recruitment_write)
):
    org_id = get_org_id(current_user.organization_id)
    candidate = await Candidate.find_one({"organization_id.$id": org_id}, Candidate.candidate_id == candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = status_in.status
    candidate.updated_at = datetime.now(timezone.utc)
    await candidate.save()

    return CandidateResponse(
        id=str(candidate.id),
        candidate_id=candidate.candidate_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        education=candidate.education,
        degree=candidate.degree,
        experience=candidate.experience,
        skills=candidate.skills,
        projects=candidate.projects,
        certifications=candidate.certifications,
        previous_companies=candidate.previous_companies,
        job_titles=candidate.job_titles,
        resume_file=candidate.resume_file,
        source=candidate.source,
        status=candidate.status,
        parsing_status=candidate.parsing_status,
        parsing_warning=candidate.parsing_warning,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )
