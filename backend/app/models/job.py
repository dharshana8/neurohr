from typing import List, Optional
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class Job(Document):
    organization_id: Link[Organization]
    job_id: str
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    minimum_experience: float = 0.0
    qualification: str = ""
    location: str = ""
    employment_type: str = "Full Time"  # Full Time, Part Time, Contract, etc.
    status: str = "Open"  # Open, Closed, Draft
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "jobs"
        indexes = [
            "organization_id",
            "job_id",
            "status",
            "title"
        ]
