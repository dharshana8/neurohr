from typing import List, Optional
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class Candidate(Document):
    organization_id: Link[Organization]
    candidate_id: str
    name: str = "Unknown Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    experience: float = 0.0
    skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    previous_companies: List[str] = Field(default_factory=list)
    job_titles: List[str] = Field(default_factory=list)
    resume_file: str = ""  # relative path to uploaded file
    resume_text: str = ""
    source: str = "Upload"
    status: str = "NEW"  # NEW, SCREENING, SHORTLISTED, INTERVIEW, SELECTED, REJECTED, ARCHIVED
    parsing_status: str = "Completed"  # Completed, Partial, Failed
    parsing_warning: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "candidates"
        indexes = [
            "organization_id",
            "candidate_id",
            "email",
            "name"
        ]
