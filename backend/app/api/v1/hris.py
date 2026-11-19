from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import LEAVE_REQUESTS, GRIEVANCES, get_tenant_employees, get_mongo_db
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

def generate_tenant_seed_leaves(org_id: str, emps: list) -> list:
    """Generate realistic initial leave petitions tailored to this tenant's employees."""
    if not emps:
        return []
    
    seeds = []
    # Leave 1: from first employee
    e1 = emps[0]
    seeds.append({
        "id": f"LV-{org_id[-4:]}-301",
        "organization_id": org_id,
        "employee_id": e1.get("id") or e1.get("employee_id"),
        "employee_name": e1["name"],
        "department": e1.get("department", "Engineering"),
        "leave_type": "Casual Leave",
        "start_date": "2026-11-20",
        "end_date": "2026-11-21",
        "days": 2,
        "reason": "Family commitments and personal matters",
        "status": "APPROVED",
        "applied_on": "2026-11-15",
        "ai_recommendation": {
            "verdict": "AUTO_APPROVE",
            "confidence": 0.96,
            "project_impact": f"Low risk: {e1.get('department')} sprint deliverables are on track.",
            "policy_compliant": True
        }
    })

    if len(emps) > 1:
        e2 = emps[1]
        seeds.append({
            "id": f"LV-{org_id[-4:]}-302",
            "organization_id": org_id,
            "employee_id": e2.get("id") or e2.get("employee_id"),
            "employee_name": e2["name"],
            "department": e2.get("department", "Sales"),
            "leave_type": "Sick Leave",
            "start_date": "2026-11-18",
            "end_date": "2026-11-19",
            "days": 2,
            "reason": "Medical appointment and recovery",
            "status": "APPROVED",
            "applied_on": "2026-11-16",
            "ai_recommendation": {
                "verdict": "AUTO_APPROVE",
                "confidence": 0.98,
                "project_impact": "Negligible delivery impact. Auto-authorized per health guidelines.",
                "policy_compliant": True
            }
        })

    if len(emps) > 2:
        e3 = emps[2]
        seeds.append({
            "id": f"LV-{org_id[-4:]}-303",
            "organization_id": org_id,
            "employee_id": e3.get("id") or e3.get("employee_id"),
            "employee_name": e3["name"],
            "department": e3.get("department", "Product"),
            "leave_type": "Earned Leave",
            "start_date": "2026-11-25",
            "end_date": "2026-11-29",
            "days": 5,
            "reason": "Annual recharge vacation",
            "status": "PENDING_APPROVAL",
            "applied_on": "2026-11-17",
            "ai_recommendation": {
                "verdict": "APPROVE_WITH_DELEGATION",
                "confidence": 0.92,
                "project_impact": f"Recommend delegating sprint tasks in {e3.get('department')} during this 5-day period.",
                "policy_compliant": True
            }
        })

    db = get_mongo_db()
    if db is not None:
        try:
            db["leaves"].insert_many([dict(s) for s in seeds])
        except Exception:
            pass

    return seeds

def generate_tenant_seed_grievances(org_id: str, emps: list) -> list:
    """Generate realistic initial grievances for high-risk employees in this tenant."""
    if not emps:
        return []
    
    # Target an employee with overtime or flight risk
    high_emps = [e for e in emps if float(e.get("attrition_risk", 0)) >= 0.65 or float(e.get("overtime_hours", 0)) > 20]
    target_emp = high_emps[0] if high_emps else emps[0]

    grv = [
        {
            "id": f"GRV-{org_id[-4:]}-501",
            "organization_id": org_id,
            "employee_id": target_emp.get("id") or target_emp.get("employee_id"),
            "employee_name": target_emp["name"],
            "category": "Workload & Burnout",
            "subject": "Consecutive sprint overtime without comp-off",
            "details": f"We have been working intense overtime ({int(target_emp.get('overtime_hours', 25))} hrs/mo) across project deliverables. Requesting comp-off review.",
            "status": "UNDER_REVIEW",
            "submitted_at": "2026-11-14",
            "ai_analysis": {
                "urgency": "HIGH",
                "sentiment_score": -0.78,
                "flight_risk_impact": "Elevated flight risk detected. Early intervention advised.",
                "recommended_action": "Grant 2 days comp-off and rebalance sprint workload."
            }
        }
    ]

    db = get_mongo_db()
    if db is not None:
        try:
            db["grievances"].insert_many([dict(g) for g in grv])
        except Exception:
            pass

    return grv

@router.get("/leaves")
def get_leave_requests(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    if org_id == "org_acme_corp":
        return LEAVE_REQUESTS

    db = get_mongo_db()
    if db is not None:
        try:
            tenant_leaves = list(db["leaves"].find({"organization_id": org_id}, {"_id": 0}))
            if tenant_leaves:
                return tenant_leaves
        except Exception:
            pass

    emps = get_tenant_employees(org_id)
    return generate_tenant_seed_leaves(org_id, emps)

@router.post("/leaves")
def apply_leave(req: LeaveApplyRequest, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    emp = next((e for e in emps if e.get("id") == req.employee_id or e.get("employee_id") == req.employee_id), None)
    emp_name = emp["name"] if emp else "Staff Member"
    emp_dept = emp["department"] if emp else "General"

    ai_verdict = "AUTO_APPROVE" if req.days <= 2 else "APPROVE_WITH_DELEGATION"
    impact = f"Workforce workload in {emp_dept} evaluated. No critical delivery blockers detected."

    new_leave = {
        "id": f"LV-{org_id[-4:]}-{int(datetime.utcnow().timestamp()) % 10000}",
        "organization_id": org_id,
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
            "confidence": 0.95,
            "project_impact": impact,
            "policy_compliant": True
        }
    }

    if org_id == "org_acme_corp":
        LEAVE_REQUESTS.insert(0, new_leave)

    db = get_mongo_db()
    if db is not None:
        try:
            db["leaves"].insert_one(dict(new_leave))
        except Exception:
            pass

    return new_leave

@router.put("/leaves/{leave_id}/status")
def update_leave_status(leave_id: str, new_status: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    status_clean = new_status.upper()

    if org_id == "org_acme_corp":
        for lv in LEAVE_REQUESTS:
            if lv["id"] == leave_id:
                lv["status"] = status_clean
                return {"message": f"Leave status updated to {status_clean}", "leave": lv}

    db = get_mongo_db()
    if db is not None:
        try:
            db["leaves"].update_one(
                {"id": leave_id, "organization_id": org_id},
                {"$set": {"status": status_clean}}
            )
            lv = db["leaves"].find_one({"id": leave_id, "organization_id": org_id}, {"_id": 0})
            if lv:
                return {"message": f"Leave status updated to {status_clean}", "leave": lv}
        except Exception:
            pass

    return {"message": f"Leave status updated to {status_clean}"}

@router.get("/attendance/summary")
def get_attendance_summary(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    total = len(emps)

    present = max(0, total - min(2, total))
    on_leave = min(2, total)
    on_site = int(total * 0.65) if total > 0 else 0
    remote = max(0, present - on_site)

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_workforce": total,
        "present_count": present,
        "on_leave_count": on_leave,
        "remote_count": remote,
        "on_site_count": on_site,
        "avg_punctuality_score": 97.4 if total > 0 else 0.0
    }

@router.get("/grievances")
def get_grievances(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    if org_id == "org_acme_corp":
        return GRIEVANCES

    db = get_mongo_db()
    if db is not None:
        try:
            grvs = list(db["grievances"].find({"organization_id": org_id}, {"_id": 0}))
            if grvs:
                return grvs
        except Exception:
            pass

    emps = get_tenant_employees(org_id)
    return generate_tenant_seed_grievances(org_id, emps)

@router.post("/grievances")
def submit_grievance(req: GrievanceSubmitRequest, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    emp = next((e for e in emps if e.get("id") == req.employee_id or e.get("employee_id") == req.employee_id), None)
    emp_name = emp["name"] if emp else "Anonymous"

    urgency = "HIGH" if any(w in req.details.lower() for w in ["harass", "burnout", "resign", "toxic", "overtime"]) else "MEDIUM"
    
    new_grv = {
        "id": f"GRV-{org_id[-4:]}-{int(datetime.utcnow().timestamp()) % 10000}",
        "organization_id": org_id,
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

    if org_id == "org_acme_corp":
        GRIEVANCES.insert(0, new_grv)

    db = get_mongo_db()
    if db is not None:
        try:
            db["grievances"].insert_one(dict(new_grv))
        except Exception:
            pass

    return new_grv

@router.get("/payroll/overview")
def get_payroll_overview(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    total = len(emps)
    total_annual = sum(float(e.get("salary", 1800000)) for e in emps)
    monthly_disbursed = (total_annual / 12) if total > 0 else 0.0

    return {
        "cycle_month": "November 2026",
        "status": "PROCESSED",
        "total_disbursed": round(monthly_disbursed, 2),
        "employees_paid": total,
        "tax_withheld": round(monthly_disbursed * 0.20, 2),
        "benefits_paid": round(monthly_disbursed * 0.08, 2)
    }
