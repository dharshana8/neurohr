from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class Skill(Document):
    skill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    aliases: List[str] = Field(default_factory=list)
    category: str = "General"
    description: Optional[str] = None
    organization_id: Optional[Link[Organization]] = None  # None indicates system-wide taxonomy
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "skills"
        indexes = [
            "skill_id",
            "name",
            "category",
            "organization_id"
        ]

class RoleSkillRequirement(Document):
    requirement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    role: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    skill_levels: Dict[str, str] = Field(default_factory=dict)  # e.g., {"Python": "ADVANCED", "Docker": "INTERMEDIATE"}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "role_skill_requirements"
        indexes = [
            "requirement_id",
            "organization_id",
            "role"
        ]

class SkillGapAnalysis(Document):
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    employee_id: str
    current_role: str
    target_role: str
    skill_coverage_score: float  # Percentage (0 - 100)
    matched_skills: List[Dict[str, Any]] = Field(default_factory=list)
    missing_skills: List[Dict[str, Any]] = Field(default_factory=list)
    partial_skills: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_development_areas: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "skill_gap_analyses"
        indexes = [
            "analysis_id",
            "organization_id",
            "employee_id",
            "target_role"
        ]

class CareerPath(Document):
    career_path_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    employee_id: str
    current_role: str
    target_role: str
    estimated_skill_coverage: float
    required_skills: List[str] = Field(default_factory=list)
    current_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "ACTIVE"  # DRAFT, ACTIVE, COMPLETED, ARCHIVED
    performance_context: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "career_paths"
        indexes = [
            "career_path_id",
            "organization_id",
            "employee_id",
            "status"
        ]
