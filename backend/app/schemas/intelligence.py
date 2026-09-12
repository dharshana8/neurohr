from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Skill Taxonomy Schemas ---
class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1)
    aliases: List[str] = Field(default_factory=list)
    category: str = "General"
    description: Optional[str] = None

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None
    category: Optional[str] = None
    description: Optional[str] = None

class SkillResponse(BaseModel):
    id: str
    skill_id: str
    name: str
    aliases: List[str]
    category: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Role Requirement Schemas ---
class RoleRequirementCreate(BaseModel):
    role: str = Field(..., min_length=1)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    skill_levels: Dict[str, str] = Field(default_factory=dict)

class RoleRequirementUpdate(BaseModel):
    role: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    skill_levels: Optional[Dict[str, str]] = None

class RoleRequirementResponse(BaseModel):
    id: str
    requirement_id: str
    role: str
    required_skills: List[str]
    preferred_skills: List[str]
    skill_levels: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Skill Gap Analysis Schemas ---
class SkillGapAnalyzeRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)

class SkillItemDetail(BaseModel):
    skill: str
    required_level: Optional[str] = "UNKNOWN"
    employee_level: Optional[str] = "UNKNOWN"
    status: str  # MATCHED, MISSING, PARTIAL
    explanation: str

class DevelopmentArea(BaseModel):
    skill: str
    priority: str  # HIGH, MEDIUM, LOW
    recommendation_type: str  # TRAINING, PROJECT, MENTORING, CERTIFICATION
    recommendation: str
    reason: str

class SkillGapResponse(BaseModel):
    analysis_id: str
    employee_id: str
    employee_name: str
    current_role: str
    target_role: str
    skill_coverage_score: float
    matched_count: int
    missing_count: int
    partial_count: int
    total_required_skills: int
    matched_skills: List[Dict[str, Any]]
    missing_skills: List[Dict[str, Any]]
    partial_skills: List[Dict[str, Any]]
    recommended_development_areas: List[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SkillGapAnalyticsResponse(BaseModel):
    total_employees_analyzed: int
    average_skill_coverage: float
    top_skill_gaps: List[Dict[str, Any]]
    department_breakdown: List[Dict[str, Any]]
    role_breakdown: List[Dict[str, Any]]

# --- Career Path Schemas ---
class MilestoneItem(BaseModel):
    title: str
    description: str
    completed: bool = False
    target_date: Optional[str] = None

class CareerPathCreate(BaseModel):
    employee_id: str
    current_role: str
    target_role: str
    estimated_skill_coverage: float
    required_skills: List[str] = Field(default_factory=list)
    current_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "ACTIVE"
    performance_context: Optional[Dict[str, Any]] = None

class CareerPathUpdate(BaseModel):
    status: Optional[str] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    recommended_actions: Optional[List[str]] = None

class CareerPathGenerateRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)

class CareerPathResponse(BaseModel):
    career_path_id: str
    employee_id: str
    employee_name: str
    current_role: str
    target_role: str
    estimated_skill_coverage: float
    required_skills: List[str]
    current_skills: List[str]
    missing_skills: List[str]
    recommended_actions: List[str]
    milestones: List[Dict[str, Any]]
    status: str
    performance_context: Optional[Dict[str, Any]] = None
    is_ai_assisted: bool = True
    disclaimer: str = "AI-assisted recommendation for career planning. Does not constitute a guaranteed promotion."
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CareerPathAnalyticsResponse(BaseModel):
    active_career_paths: int
    target_roles: List[Dict[str, Any]]
    common_development_areas: List[Dict[str, Any]]
    status_distribution: Dict[str, int]
