from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmployeeResponse(BaseModel):
    id: str
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
    skills: str
    promotion_history: int
    manager_feedback: str
    employment_status: str
    attrition: int

    class Config:
        from_attributes = True

class ImportSummaryResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    imported_rows: int
    errors: List[str]

class WorkforceStatsResponse(BaseModel):
    total_employees: int
    high_attrition_risk: int
    avg_performance: float
    avg_engagement: float

