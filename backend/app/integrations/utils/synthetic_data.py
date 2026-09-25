import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Product", "Operations"]
ROLES = ["Software Engineer", "DevOps Engineer", "Account Executive", "Marketing Analyst", "HR Manager", "Financial Analyst", "Product Manager"]
SKILLS = ["Python", "TypeScript", "React", "Docker", "AWS", "SQL", "Logistics", "Cybersecurity", "Excel", "Data Analysis"]

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Robin", "Casey", "Drew",
               "Jamie", "Cameron", "Avery", "Riley", "Logan", "Kendall", "Hayden", "Peyton", "Quinn", "Dakota"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
              "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White"]

def _random_date(start_year=2018, seed=None):
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    start = datetime(start_year, 1, 1)
    end = datetime(2025, 12, 31)
    return start + timedelta(days=rng.randint(0, (end - start).days))

def generate_core_identities(count: int = 100) -> List[Dict[str, Any]]:
    """
    Deterministic identity generator creating consistent workforce identities
    shared across external ERP and HRIS systems to verify normalization and deduplication.
    """
    identities = []
    rng = random.Random(1001)  # Seed for deterministic cross-system consistency

    for i in range(1, count + 1):
        fname = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        lname = LAST_NAMES[((i - 1) * 3) % len(LAST_NAMES)]
        full_name = f"{fname} {lname}"
        
        dept_idx = (i - 1) % len(DEPARTMENTS)
        dept = DEPARTMENTS[dept_idx]
        role = ROLES[dept_idx]
        
        join_date = _random_date(start_year=2018, seed=i + 500).strftime("%Y-%m-%d")
        exp = round(1.0 + (i % 14) * 0.9, 1)
        base_salary = 60000 + ((i * 1250) % 90000)
        perf = round(2.5 + ((i * 7) % 25) * 0.1, 1)
        if perf > 5.0:
            perf = 5.0
        eng = round(2.0 + ((i * 9) % 30) * 0.1, 1)
        if eng > 5.0:
            eng = 5.0
            
        ot = float((i * 4) % 20)
        skill_sample = [SKILLS[i % len(SKILLS)], SKILLS[(i + 2) % len(SKILLS)], SKILLS[(i + 5) % len(SKILLS)]]
        promotions = (i % 3)
        status = "Active" if (i % 12 != 0) else "Terminated"
        attrition_flag = 1 if (eng < 3.0 and perf >= 4.0) or (ot > 15) or (status == "Terminated") else 0

        identities.append({
            "emp_code": f"ERP{i:03d}",
            "full_name": full_name,
            "department": dept,
            "role": role,
            "date_joined": join_date,
            "experience": exp,
            "salary": float(base_salary),
            "performance": perf,
            "engagement": eng,
            "overtime": ot,
            "skills": skill_sample,
            "promotions": promotions,
            "status": status,
            "attrition": attrition_flag
        })
    return identities

def generate_mock_erp_data(count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate mock ERP dataset exposing ERP-specific enterprise field naming conventions.
    """
    identities = generate_core_identities(count)
    erp_records = []
    for item in identities:
        erp_records.append({
            "employee_code": item["emp_code"],
            "full_name": item["full_name"],
            "department_name": item["department"],
            "job_title": item["role"],
            "date_joined": item["date_joined"],
            "years_exp": item["experience"],
            "annual_salary": item["salary"],
            "perf_rating": item["performance"],
            "engagement": item["engagement"],
            "overtime_hours": item["overtime"],
            "skill_set": ", ".join(item["skills"]),
            "promotions": item["promotions"],
            "feedback": f"ERP Master Record: {item['full_name']} operational profile active in {item['department']}.",
            "status": item["status"],
            "has_left": item["attrition"]
        })
    return erp_records

def generate_mock_hris_data(count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate mock HRIS dataset exposing HRIS-specific human capital field naming conventions.
    Shares identical employee identities with Demo ERP to prove deduplication & enrichment.
    """
    identities = generate_core_identities(count)
    hris_records = []
    for item in identities:
        hris_records.append({
            "emp_id": item["emp_code"],
            "employee_name": item["full_name"],
            "dept_name": item["department"],
            "designation": item["role"],
            "date_joined": item["date_joined"],
            "experience_years": item["experience"],
            "salary": item["salary"],
            "performance_score": item["performance"],
            "engagement_score": item["engagement"],
            "overtime": item["overtime"],
            "skills": ", ".join(item["skills"]),
            "promotion_history": item["promotions"],
            "manager_feedback": f"HRIS Talent Review: {item['full_name']} performance score {item['performance']}/5.0 with {item['department']} team.",
            "employment_status": item["status"],
            "attrition": item["attrition"]
        })
    return hris_records
