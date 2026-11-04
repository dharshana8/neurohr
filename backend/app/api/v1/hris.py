from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import LEAVE_REQUESTS, GRIEVANCES, EMPLOYEES
from app.api.v1.auth import get_current_user

router = APIRouter()

class LeaveApplyRequest(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    days: int
    reason: str

class GrievanceSubmitRequest(BaseModel):
    employee_id: str
    category: str
    subject: str
    details: str

@router.get("/leaves")
def get_leave_requests(current_user: dict = Depends(get_current_user)):
    return LEAVE_REQUESTS

@router.post("/leaves")
def apply_leave(req: LeaveApplyRequest, current_user: dict = Depends(get_current_user)):
    emp = next((e for e in EMPLOYEES if e["id"] == req.employee_id), None)
    emp_name = emp["name"] if emp else "Staff Member"
    emp_dept = emp["department"] if emp else "General"

    # AI HR Evaluation for the new leave
    ai_verdict = "AUTO_APPROVE" if req.days <= 2 else "APPROVE_WITH_DELEGATION"
    impact = f"Workforce workload in {emp_dept} evaluated. No critical delivery blockers detected."

    new_leave = {
        "id": f"LV-{len(LEAVE_REQUESTS) + 301}",
        "employee_id": req.employee_id,
        "employee_name": emp_name,
        "department": emp_dept,
        "leave_type": req.leave_type,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "days": req.days,
        "reason": req.reason,
        "status": "APPROVED" if ai_verdict == "AUTO_APPROVE" else "PENDING_APPROVAL",
        "applied_on": datetime.utcnow().strftime("%Y-%m-%d"),
        "ai_recommendation": {
            "verdict": ai_verdict,
            "confidence": 0.94,
            "project_impact": impact,
            "policy_compliant": True
        }
    }
    LEAVE_REQUESTS.insert(0, new_leave)
    return new_leave

@router.put("/leaves/{leave_id}/status")
def update_leave_status(leave_id: str, new_status: str, current_user: dict = Depends(get_current_user)):
    for lv in LEAVE_REQUESTS:
        if lv["id"] == leave_id:
            lv["status"] = new_status.upper()
            return {"message": f"Leave status updated to {new_status}", "leave": lv}
    raise HTTPException(status_code=404, detail="Leave request not found")

@router.get("/attendance/summary")
def get_attendance_summary(current_user: dict = Depends(get_current_user)):
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_workforce": len(EMPLOYEES),
        "present_count": len(EMPLOYEES) - 2,
        "on_leave_count": 2,
        "remote_count": 4,
        "on_site_count": len(EMPLOYEES) - 6,
        "avg_punctuality_score": 96.4
    }

@router.get("/grievances")
def get_grievances(current_user: dict = Depends(get_current_user)):
    return GRIEVANCES

@router.post("/grievances")
def submit_grievance(req: GrievanceSubmitRequest, current_user: dict = Depends(get_current_user)):
    emp = next((e for e in EMPLOYEES if e["id"] == req.employee_id), None)
    emp_name = emp["name"] if emp else "Anonymous"

    # AI Triage & Grievance analysis
    urgency = "HIGH" if any(w in req.details.lower() for w in ["harass", "burnout", "resign", "toxic"]) else "MEDIUM"
    
    new_grv = {
        "id": f"GRV-{len(GRIEVANCES) + 501}",
        "employee_id": req.employee_id,
        "employee_name": emp_name,
        "category": req.category,
        "subject": req.subject,
        "details": req.details,
        "status": "UNDER_REVIEW",
        "submitted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "ai_analysis": {
            "urgency": urgency,
            "sentiment_score": -0.65,
            "flight_risk_impact": "Monitored",
            "recommended_action": "Auto-scheduled check-in with HR Business Partner within 24 hours."
        }
    }
    GRIEVANCES.insert(0, new_grv)
    return new_grv

@router.get("/payroll/overview")
def get_payroll_overview(current_user: dict = Depends(get_current_user)):
    total_monthly_payroll = sum(e.get("salary", 100000) for e in EMPLOYEES) / 12
    return {
        "cycle_month": "October 2026",
        "status": "PROCESSED",
        "total_disbursed": round(total_monthly_payroll, 2),
        "employees_paid": len(EMPLOYEES),
        "tax_withheld": round(total_monthly_payroll * 0.22, 2),
        "benefits_paid": round(total_monthly_payroll * 0.08, 2)
    }

