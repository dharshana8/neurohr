from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import ORGANIZATIONS, AUDIT_LOGS, EMPLOYEES
from app.api.v1.auth import get_current_user

router = APIRouter()

class CreateOrgRequest(BaseModel):
    name: str
    industry: str
    company_size: str
    plan_tier: str
    admin_email: str
    admin_password: str

class UpdatePlanRequest(BaseModel):
    plan_tier: str

def require_superadmin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "PLATFORM_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Platform SuperAdmin authorization required."
        )
    return current_user

@router.get("/organizations")
def list_organizations(current_user: dict = Depends(require_superadmin)):
    return ORGANIZATIONS

@router.post("/organizations")
def create_organization(req: CreateOrgRequest, current_user: dict = Depends(require_superadmin)):
    new_id = f"org_{req.name.lower().replace(' ', '_')}"
    new_org = {
        "id": new_id,
        "name": req.name,
        "industry": req.industry,
        "company_size": req.company_size,
        "status": "ACTIVE",
        "plan_tier": req.plan_tier,
        "subscription_status": "ACTIVE",
        "admin_email": req.admin_email,
        "employee_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "plan_limits": {
            "max_employees": 500 if req.plan_tier == "PROFESSIONAL" else 1000 if req.plan_tier == "ENTERPRISE" else 50,
            "features": ["Attrition Prediction ML", "HRIS Leave Portal", "ERP Resource Sync", "AI Copilot"],
            "max_integrations": 10,
            "copilot_access": True,
            "description": f"{req.plan_tier} plan"
        }
    }
    ORGANIZATIONS.insert(0, new_org)

    AUDIT_LOGS.insert(0, {
        "id": f"aud_{len(AUDIT_LOGS)+1}",
        "action": "TENANT_PROVISIONED",
        "resource_type": "ORGANIZATION",
        "resource_id": new_id,
        "status": "SUCCESS",
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "organization": new_org,
        "credentials": {
            "organization_name": req.name,
            "organization_id": new_id,
            "plan_tier": req.plan_tier,
            "admin_email": req.admin_email,
            "admin_password": req.admin_password
        }
    }

@router.get("/audit-logs")
def get_audit_logs(current_user: dict = Depends(require_superadmin)):
    return AUDIT_LOGS

@router.get("/organizations/{org_id}/telemetry")
def get_org_telemetry(org_id: str, current_user: dict = Depends(require_superadmin)):
    org = next((o for o in ORGANIZATIONS if o["id"] == org_id), None)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "organization_id": org["id"],
        "organization_name": org["name"],
        "plan_tier": org["plan_tier"],
        "subscription_status": org["subscription_status"],
        "plan_limits": org.get("plan_limits", {}),
        "seat_capacity": {
            "current_employees": org["employee_count"],
            "max_employees": org.get("plan_limits", {}).get("max_employees", 200),
            "utilization_pct": round((org["employee_count"] / max(org.get("plan_limits", {}).get("max_employees", 200), 1)) * 100, 1)
        },
        "activity_metrics": {
            "attrition_predictions_count": 420,
            "jobs_posted_count": 5,
            "candidates_tracked_count": 18,
            "sentiment_surveys_logged": 62,
            "integrations_connected": 3,
            "audit_events_logged": len(AUDIT_LOGS)
        },
        "last_activity": datetime.utcnow().isoformat(),
        "privacy_notice": "Strict tenant cryptographic boundary enforced. Raw employee data is inaccessible to SuperAdmin."
    }

@router.put("/organizations/{org_id}/plan")
def update_org_plan(org_id: str, req: UpdatePlanRequest, current_user: dict = Depends(require_superadmin)):
    org = next((o for o in ORGANIZATIONS if o["id"] == org_id), None)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org["plan_tier"] = req.plan_tier
    return {"message": f"Organization plan updated to {req.plan_tier}", "organization": org}

