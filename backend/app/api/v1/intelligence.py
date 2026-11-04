from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from app.core.database import EMPLOYEES
from app.api.v1.auth import get_current_user
from app.ml.attrition.service import attrition_service

router = APIRouter()

@router.get("/attrition")
def get_attrition_overview(current_user: dict = Depends(get_current_user)):
    results = []
    for emp in EMPLOYEES:
        salary = emp.get("salary", 95000)
        tenure = 2.5
        perf = emp.get("performance_score", 4.0)
        eng = emp.get("engagement_score", 3.8)
        overtime = 25 if emp.get("id") == "EMP-102" else 10

        pred = attrition_service.predict_risk(
            salary=salary,
            tenure_years=tenure,
            performance=perf,
            engagement=eng,
            overtime_hours=overtime
        )
        results.append({
            "employee_id": emp["id"],
            "name": emp["name"],
            "department": emp["department"],
            "role": emp["role"],
            "risk_score": pred["attrition_probability"],
            "risk_level": pred["risk_level"],
            "drivers": pred["top_drivers"],
            "recommended_action": "Schedule 1:1 retention talk & review comp-off balance" if pred["risk_level"] == "HIGH" else "Monitor standard KPIs"
        })
    
    high_count = sum(1 for r in results if r["risk_level"] == "HIGH")
    medium_count = sum(1 for r in results if r["risk_level"] == "MEDIUM")
    low_count = sum(1 for r in results if r["risk_level"] == "LOW")

    return {
        "summary": {
            "total_analyzed": len(results),
            "high_risk": high_count,
            "medium_risk": medium_count,
            "low_risk": low_count,
            "workforce_attrition_rate_pct": round((high_count / max(len(results), 1)) * 100, 1)
        },
        "predictions": results
    }

@router.get("/sentiment")
def get_sentiment(current_user: dict = Depends(get_current_user)):
    return {
        "overall_sentiment_score": 0.76,
        "mood": "POSITIVE",
        "themes": [
            {"topic": "Remote Flexibility", "sentiment": 0.92, "volume": 45},
            {"topic": "Weekend Deployment Overtime", "sentiment": -0.68, "volume": 18},
            {"topic": "Health & Learning Allowance", "sentiment": 0.85, "volume": 32}
        ]
    }

