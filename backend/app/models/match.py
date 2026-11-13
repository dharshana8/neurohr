from typing import List, Optional
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class CandidateMatch(Document):
    organization_id: Link[Organization]
    job_id: str
    candidate_id: str
    match_score: float = 0.0
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    experience_match: str = "Match"  # Match, Below Minimum, Exceeds
    education_match: str = "Match"   # Match, Partial Match, Missing
    semantic_similarity: float = 0.0
    explanation: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "candidate_matches"
        indexes = [
            "organization_id",
            "job_id",
            "candidate_id",
            "match_score"
        ]
