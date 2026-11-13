"""CSV mapper to convert raw CSV rows to NormalizedEmployee schema"""
from typing import Dict, Any, List
from app.integrations.base.schemas import NormalizedEmployee
from datetime import datetime

def map_csv_row(row: Dict[str, Any]) -> NormalizedEmployee:
    # Convert skills string to list
    skills_raw = row.get("skills", "")
    skills_list = [s.strip() for s in str(skills_raw).split(",") if s.strip()]
    return NormalizedEmployee(
        employee_id=str(row.get("employee_id")),
        name=str(row.get("name")),
        department=str(row.get("department")),
        role=str(row.get("role")),
        joining_date=datetime.fromisoformat(str(row.get("joining_date"))),
        experience=float(row.get("experience")),
        salary=float(row.get("salary")),
        performance_score=float(row.get("performance_score")),
        engagement_score=float(row.get("engagement_score")),
        overtime=float(row.get("overtime")),
        skills=skills_list,
        promotion_history=int(row.get("promotion_history")),
        manager_feedback=str(row.get("manager_feedback", "")),
        employment_status=str(row.get("employment_status", "Active")),
        attrition=int(row.get("attrition")),
    )
