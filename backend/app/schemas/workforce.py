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

class EmployeeCreate(BaseModel):
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
    attrition: int = 0

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    joining_date: Optional[datetime] = None
    experience: Optional[float] = None
    salary: Optional[float] = None
    performance_score: Optional[float] = None
    engagement_score: Optional[float] = None
    overtime: Optional[float] = None
    skills: Optional[str] = None
    promotion_history: Optional[int] = None
    manager_feedback: Optional[str] = None
    employment_status: Optional[str] = None
    attrition: Optional[int] = None
