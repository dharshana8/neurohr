from typing import Dict, Any, List
from app.integrations.base.schemas import NormalizedEmployee
from datetime import datetime

def map_erp_row(row: Dict[str, Any]) -> NormalizedEmployee:
    skills_raw = row.get("skill_set", "")
    skills_list = [s.strip() for s in str(skills_raw).split(",") if s.strip()]
    return NormalizedEmployee(
        employee_id=str(row.get("employee_code")),
        name=str(row.get("full_name")),
        department=str(row.get("department_name")),
        role=str(row.get("job_title")),
        joining_date=datetime.fromisoformat(str(row.get("date_joined"))),
        experience=float(row.get("years_exp")),
        salary=float(row.get("annual_salary")),
        performance_score=float(row.get("perf_rating")),
        engagement_score=float(row.get("engagement")),
        overtime=float(row.get("overtime_hours")),
        skills=skills_list,
        promotion_history=int(row.get("promotions")),
        manager_feedback=str(row.get("feedback", "")),
        employment_status=str(row.get("status", "Active")),
        attrition=int(row.get("has_left")),
    )
