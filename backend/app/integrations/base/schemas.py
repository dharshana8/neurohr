"""Pydantic schemas for integration normalization"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class NormalizedEmployee(BaseModel):
    employee_id: str
    name: str
    department: str
    role: str
    joining_date: datetime
    experience: float
    salary: float
    performance_score: float
    engagement_score: float
    overtime: float
    skills: List[str] = Field(default_factory=list)
    promotion_history: int
    manager_feedback: Optional[str] = None
    employment_status: str = "Active"
    attrition: int  # 0 or 1
