from typing import Dict, Any, List, Optional
from datetime import datetime
from app.integrations.base.schemas import NormalizedEmployee

DEFAULT_HRIS_MAPPING = {
    "emp_id": "employee_id",
    "employee_name": "name",
    "dept_name": "department",
    "designation": "role",
    "date_joined": "joining_date",
    "experience_years": "experience",
    "salary": "salary",
    "performance_score": "performance_score",
    "engagement_score": "engagement_score",
    "overtime": "overtime",
    "skills": "skills",
    "promotion_history": "promotion_history",
    "manager_feedback": "manager_feedback",
    "employment_status": "employment_status",
    "attrition": "attrition"
}

def parse_date(date_val: Any) -> datetime:
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, str):
        try:
            return datetime.fromisoformat(date_val)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_val, fmt)
            except ValueError:
                continue
    return datetime.utcnow()

def map_hris_row(row: Dict[str, Any], custom_mappings: Optional[Dict[str, str]] = None) -> NormalizedEmployee:
    """
    Maps a raw HRIS row into a NormalizedEmployee using either default or dynamic database mappings.
    """
    mapping = dict(DEFAULT_HRIS_MAPPING)
    if custom_mappings:
        mapping.update(custom_mappings)

    # Invert mapping to find source field for target field
    target_to_source = {target: src for src, target in mapping.items()}

    def get_val(target: str, default: Any = None):
        src = target_to_source.get(target, target)
        # Also handle potential alternative source field names
        if src in row:
            return row[src]
        if target in row:
            return row[target]
        # Legacy key fallbacks
        if target == "experience" and "experience" in row:
            return row["experience"]
        if target == "performance_score" and "performance" in row:
            return row["performance"]
        return default

    skills_raw = get_val("skills", "")
    if isinstance(skills_raw, list):
        skills_list = [str(s).strip() for s in skills_raw if str(s).strip()]
    else:
        skills_list = [s.strip() for s in str(skills_raw or "").split(",") if s.strip()]

    raw_date = get_val("joining_date", "2022-01-01")

    return NormalizedEmployee(
        employee_id=str(get_val("employee_id", "") or "").strip(),
        name=str(get_val("name", "") or "").strip(),
        department=str(get_val("department", "General") or "General").strip(),
        role=str(get_val("role", "Staff") or "Staff").strip(),
        joining_date=parse_date(raw_date),
        experience=float(get_val("experience", 0.0) or 0.0),
        salary=float(get_val("salary", 0.0) or 0.0),
        performance_score=float(get_val("performance_score", 3.0) or 3.0),
        engagement_score=float(get_val("engagement_score", 3.0) or 3.0),
        overtime=float(get_val("overtime", 0.0) or 0.0),
        skills=skills_list,
        promotion_history=int(get_val("promotion_history", 0) or 0),
        manager_feedback=str(get_val("manager_feedback", "") or ""),
        employment_status=str(get_val("employment_status", "Active") or "Active"),
        attrition=int(get_val("attrition", 0) or 0)
    )
