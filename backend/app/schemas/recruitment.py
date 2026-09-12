from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    minimum_experience: float = 0.0
    qualification: str = ""
    location: str = ""
    employment_type: str = "Full Time"
    status: str = "Open"

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    minimum_experience: Optional[float] = None
    qualification: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    job_id: str
    title: str
    description: str
    required_skills: List[str]
    minimum_experience: float
    qualification: str
    location: str
    employment_type: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime

class CandidateResponse(BaseModel):
    id: str
    candidate_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    experience: float
    skills: List[str]
    projects: List[str]
    certifications: List[str]
    previous_companies: List[str]
    job_titles: List[str]
    resume_file: str
    source: str
    status: str
    parsing_status: str
    parsing_warning: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CandidateCreate(BaseModel):
    name: str
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
    source: str = "Manual"
    status: str = "NEW"

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    experience: Optional[float] = None
    skills: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    previous_companies: Optional[List[str]] = None
    job_titles: Optional[List[str]] = None

class CandidateStatusUpdate(BaseModel):
    status: str

class CandidateMatchResponse(BaseModel):
    candidate_id: str
    job_id: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_match: str
    education_match: str
    semantic_similarity: float
    explanation: str

class CandidateRankingItem(BaseModel):
    rank: int
    candidate_id: str
    name: str
    email: Optional[str] = None
    experience: float
    skills: List[str]
    degree: Optional[str] = None
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_match: str
    education_match: str
    semantic_similarity: float
    explanation: str

class JobRankingResponse(BaseModel):
    job_id: str
    job_title: str
    total_candidates: int
    rankings: List[CandidateRankingItem]
