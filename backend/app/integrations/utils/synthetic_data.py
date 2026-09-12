import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Product"]
ROLES = ["Manager", "Developer", "Designer", "Analyst", "Director", "Specialist"]
SKILLS = ["Python", "Java", "React", "SQL", "Excel", "Marketing", "Design"]

def _random_date(start_year=2015):
    start = datetime(start_year, 1, 1)
    end = datetime.now()
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_mock_hris_data(count: int = 100) -> List[Dict[str, Any]]:
    """Generate mock data matching HRIS schema."""
    random.seed(42)  # For consistent mock data
    data = []
    for i in range(1, count + 1):
        data.append({
            "emp_id": f"HRIS-{i:03d}",
            "employee_name": f"HRIS Employee {i}",
            "dept_name": random.choice(DEPARTMENTS),
            "designation": random.choice(ROLES),
            "date_joined": _random_date().strftime("%Y-%m-%d"),
            "experience": round(random.uniform(1.0, 15.0), 1),
            "salary": random.randint(50000, 150000),
            "performance": round(random.uniform(2.0, 5.0), 1),
            "engagement_score": random.randint(50, 100),
            "overtime": random.randint(0, 20),
            "skills": ",".join(random.sample(SKILLS, k=random.randint(1, 3))),
            "promotion_history": random.randint(0, 3),
            "manager_feedback": "Good performance",
            "employment_status": "Active" if random.random() > 0.1 else "Terminated",
            "attrition": 1 if random.random() > 0.8 else 0,
        })
    return data

def generate_mock_erp_data(count: int = 100) -> List[Dict[str, Any]]:
    """Generate mock data matching ERP schema."""
    random.seed(43)
    data = []
    for i in range(1, count + 1):
        data.append({
            "employee_code": f"ERP-{i:03d}",
            "full_name": f"ERP Employee {i}",
            "department_name": random.choice(DEPARTMENTS),
            "job_title": random.choice(ROLES),
            "date_joined": _random_date().strftime("%Y-%m-%d"),
            "years_exp": round(random.uniform(1.0, 15.0), 1),
            "annual_salary": random.randint(50000, 150000),
            "perf_rating": round(random.uniform(2.0, 5.0), 1),
            "engagement": random.randint(50, 100),
            "overtime_hours": random.randint(0, 20),
            "skill_set": ",".join(random.sample(SKILLS, k=random.randint(1, 3))),
            "promotions": random.randint(0, 3),
            "feedback": "Consistent contributor",
            "status": "Active" if random.random() > 0.1 else "Terminated",
            "has_left": 1 if random.random() > 0.8 else 0,
        })
    return data
