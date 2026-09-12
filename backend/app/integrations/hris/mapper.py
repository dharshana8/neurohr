from typing import Dict, Any, List
from app.integrations.base.schemas import NormalizedEmployee
from datetime import datetime

def map_hris_row(row: Dict[str, Any]) -> NormalizedEmployee:
    skills_raw = row.get("skills", "")
    skills_list = [s.strip() for s in str(skills_raw).split(",") if s.strip()]
    return NormalizedEmployee(
        employee_id=str(row.get("emp_id")),
        name=str(row.get("employee_name")),
        department=str(row.get("dept_name")),
        role=str(row.get("designation")),
        joining_date=datetime.fromisoformat(str(row.get("date_joined"))),
        experience=float(row.get("experience")),
        salary=float(row.get("salary")),
        performance_score=float(row.get("performance")),
        engagement_score=float(row.get("engagement_score")),
        overtime=float(row.get("overtime")),
        skills=skills_list,
        promotion_history=int(row.get("promotion_history")),
        manager_feedback=str(row.get("manager_feedback", "")),
        employment_status=str(row.get("employment_status", "Active")),
        attrition=int(row.get("attrition")),
    )
