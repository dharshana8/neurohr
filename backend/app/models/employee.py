from typing import Optional
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class Employee(Document):
    organization_id: Link[Organization]
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
    attrition: int  # 0 or 1
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "employees"
        indexes = [
            "organization_id",
            "employee_id",
            "department",
            "role"
        ]
