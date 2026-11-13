import pandas as pd

FEATURE_COLUMNS = [
    "department",
    "role",
    "experience",
    "salary",
    "performance_score",
    "engagement_score",
    "overtime",
    "promotion_history",
    "employment_status"
]

def preprocess_employee(employee) -> pd.DataFrame:
    """
    Extract structured features for attrition model input.
    Excludes PII (employee_id, name).
    """
    data = {
        "department": [str(getattr(employee, "department", "Engineering"))],
        "role": [str(getattr(employee, "role", "Software Engineer"))],
        "experience": [float(getattr(employee, "experience", 0.0))],
        "salary": [float(getattr(employee, "salary", 0.0))],
        "performance_score": [float(getattr(employee, "performance_score", 0.0))],
        "engagement_score": [float(getattr(employee, "engagement_score", 0.0))],
        "overtime": [float(getattr(employee, "overtime", 0.0))],
        "promotion_history": [int(getattr(employee, "promotion_history", 0))],
        "employment_status": [str(getattr(employee, "employment_status", "Active"))]
    }
    return pd.DataFrame(data)
