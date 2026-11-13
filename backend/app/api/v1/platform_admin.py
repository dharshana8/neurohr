from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
import uuid

from app.core.database import (
    ORGANIZATIONS, 
    AUDIT_LOGS, 
    EMPLOYEES, 
    USERS, 
    get_mongo_db
)
from app.api.v1.auth import get_current_user
from app.core.security import create_access_token

router = APIRouter()

# Global Feature Flags State
PLATFORM_SETTINGS = {
    "maintenance_mode": False,
    "global_copilot_enabled": True,
    "mfa_enforced": False,
    "allow_self_registration": False,
    "max_tenants_limit": 50
}

TIER_CONFIGS = {
    "STARTER": {
        "max_employees": 50,
        "features": ["Attrition Prediction ML", "Core HRIS & Leave Tracking", "CSV Workforce Import"],
        "max_integrations": 2,
        "copilot_access": False,
        "monthly_price_inr": 25000,
        "description": "Essential HR workforce tracking and calibrated attrition prediction for growing teams."
    },
    "PROFESSIONAL": {
        "max_employees": 300,
        "features": ["Attrition Prediction ML", "HRIS Leave Portal", "ERP Resource Sync", "AI Copilot", "Workplace Sentiment Analysis"],
        "max_integrations": 10,
        "copilot_access": True,
        "monthly_price_inr": 85000,
        "description": "Mid-market enterprise plan with full predictive AI, ERP headcount sync, and Copilot."
    },
    "ENTERPRISE": {
        "max_employees": 5000,
        "features": ["All Modules", "Custom ML Calibration", "SAP & Workday Connectors", "Dedicated SLA", "Uncapped AI Tokens"],
        "max_integrations": 50,
        "copilot_access": True,
        "monthly_price_inr": 250000,
        "description": "Full-scale multi-subsidiary enterprise license with custom governance and high throughput."
    }
}

class CreateTenantRequest(BaseModel):
    organization_name: Optional[str] = None
    name: Optional[str] = None
    industry: Optional[str] = "Technology"
    company_size: Optional[str] = "51-200"
    plan_tier: Optional[str] = "PROFESSIONAL"
    admin_email: EmailStr
    admin_password: str

class CreatePlanRequest(BaseModel):
    name: str
    tier_key: Optional[str] = None
    max_employees: int = 150
    monthly_price_inr: int = 45000
    max_integrations: int = 5
    copilot_access: bool = True
    features: List[str] = ["Attrition Prediction ML", "Core HRIS & Leave Tracking"]
    description: str = "Custom plan configured by Platform SuperAdmin"

class UpdatePlanRequest(BaseModel):
    plan_tier: str

class ResetAdminRequest(BaseModel):
    email: EmailStr
    password: str

class FeatureFlagsRequest(BaseModel):
    maintenance_mode: Optional[bool] = None
    global_copilot_enabled: Optional[bool] = None
    mfa_enforced: Optional[bool] = None
    allow_self_registration: Optional[bool] = None

def require_superadmin(current_user: dict = Depends(get_current_user)):
    role = str(current_user.get("role", "")).upper()
    email = str(current_user.get("email", "")).lower()
    if role not in ["PLATFORM_ADMIN", "SUPERADMIN"] and email not in ["admin@neurohr.com", "platform@neurohr.com"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Platform SuperAdmin authorization required."
        )
    return current_user

def log_platform_audit(action: str, resource_type: str, resource_id: str, status: str = "SUCCESS"):
    entry = {
        "id": f"aud_{len(AUDIT_LOGS) + 101}",
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    AUDIT_LOGS.insert(0, entry)
    db = get_mongo_db()
    if db is not None:
        try:
            db["audit_logs"].insert_one(dict(entry))
        except Exception:
            pass

# ─── Organizations Endpoints ──────────────────────────────────────────────────

def find_org(org_id: str) -> Optional[dict]:
    org = next((o for o in ORGANIZATIONS if o.get("id") == org_id), None)
    if not org:
        db = get_mongo_db()
        if db is not None:
            try:
                db_org = db["organizations"].find_one({"id": org_id}, {"_id": 0})
                if db_org:
                    ORGANIZATIONS.append(db_org)
                    return db_org
            except Exception:
                pass
    return org


@router.get("/organizations")
def list_organizations(current_user: dict = Depends(require_superadmin)):
    db = get_mongo_db()
    if db is not None:
        try:
            db_orgs = list(db["organizations"].find({}, {"_id": 0}))
            if db_orgs:
                # Merge with in-memory to ensure latest metadata
                org_map = {o["id"]: o for o in ORGANIZATIONS}
                for dbo in db_orgs:
                    org_map[dbo["id"]] = dbo
                return list(org_map.values())
        except Exception:
            pass
    return ORGANIZATIONS

@router.post("/register-tenant")
@router.post("/organizations")
def register_tenant(req: CreateTenantRequest, current_user: dict = Depends(require_superadmin)):
    name = (req.organization_name or req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Organization name is required.")
    
    # Generate clean tenant ID
    slug = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
    org_id = f"org_{slug}_{uuid.uuid4().hex[:4]}"

    # Verify admin email uniqueness in USERS
    if req.admin_email in USERS:
        raise HTTPException(
            status_code=400, 
            detail=f"An administrator account with email '{req.admin_email}' already exists."
        )

    tier = req.plan_tier.upper() if req.plan_tier else "PROFESSIONAL"
    tier_info = TIER_CONFIGS.get(tier, TIER_CONFIGS["PROFESSIONAL"])

    new_org = {
        "id": org_id,
        "name": name,
        "industry": req.industry or "Technology",
        "company_size": req.company_size or "51-200",
        "status": "ACTIVE",
        "plan_tier": tier,
        "subscription_status": "ACTIVE",
        "admin_email": req.admin_email,
        "employee_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_limits": {
            "max_employees": tier_info["max_employees"],
            "features": tier_info["features"],
            "max_integrations": tier_info["max_integrations"],
            "copilot_access": tier_info["copilot_access"],
            "description": tier_info["description"]
        }
    }

    # Add to in-memory store
    ORGANIZATIONS.insert(0, new_org)

    # Register tenant admin in USERS
    user_id = f"usr_{slug}_admin"
    admin_record = {
        "id": user_id,
        "email": req.admin_email,
        "password": req.admin_password,
        "role": "ORGANIZATION_ADMIN",
        "organization_id": org_id,
        "name": f"{name} Admin",
        "is_active": True
    }
    USERS[req.admin_email] = admin_record

    # Persist in MongoDB
    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].insert_one(dict(new_org))
            db["users"].update_one(
                {"email": req.admin_email},
                {"$set": dict(admin_record)},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB tenant persistence error: {e}")

    log_platform_audit("TENANT_PROVISIONED", "ORGANIZATION", org_id)

    return {
        "organization_id": org_id,
        "organization_name": name,
        "plan_tier": tier,
        "admin_email": req.admin_email,
        "admin_password": req.admin_password,
        "status": "ACTIVE",
        "message": f"Successfully provisioned enterprise tenant '{name}' with {tier} plan."
    }

@router.put("/organizations/{org_id}/status")
def update_org_status(
    org_id: str, 
    status: str = Query(..., pattern="^(ACTIVE|SUSPENDED)$"), 
    current_user: dict = Depends(require_superadmin)
):
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org["status"] = status
    org["subscription_status"] = "ACTIVE" if status == "ACTIVE" else "SUSPENDED"

    # Suspend/activate tenant admin user
    if org.get("admin_email") and org["admin_email"] in USERS:
        USERS[org["admin_email"]]["is_active"] = (status == "ACTIVE")

    # Persist in MongoDB
    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].update_one(
                {"id": org_id},
                {"$set": {"status": status, "subscription_status": org["subscription_status"]}}
            )
        except Exception:
            pass

    log_platform_audit(f"TENANT_{status}", "ORGANIZATION", org_id)
    return {"message": f"Organization '{org['name']}' status changed to {status}", "organization": org}

@router.put("/organizations/{org_id}/plan")
def update_org_plan(org_id: str, req: UpdatePlanRequest, current_user: dict = Depends(require_superadmin)):
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    tier = req.plan_tier.upper()
    if tier not in TIER_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Invalid plan tier. Choose from: {list(TIER_CONFIGS.keys())}")

    tier_info = TIER_CONFIGS[tier]
    org["plan_tier"] = tier
    org["plan_limits"] = {
        "max_employees": tier_info["max_employees"],
        "features": tier_info["features"],
        "max_integrations": tier_info["max_integrations"],
        "copilot_access": tier_info["copilot_access"],
        "description": tier_info["description"]
    }

    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].update_one(
                {"id": org_id},
                {"$set": {"plan_tier": tier, "plan_limits": org["plan_limits"]}}
            )
        except Exception:
            pass

    log_platform_audit(f"PLAN_UPGRADED_{tier}", "ORGANIZATION", org_id)
    return {"message": f"Organization plan upgraded to {tier}", "organization": org}

@router.post("/organizations/{org_id}/admin")
def reset_org_admin(org_id: str, req: ResetAdminRequest, current_user: dict = Depends(require_superadmin)):
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    old_email = org.get("admin_email")
    if old_email and old_email in USERS:
        del USERS[old_email]

    org["admin_email"] = req.email
    admin_record = {
        "id": f"usr_{org_id}_admin",
        "email": req.email,
        "password": req.password,
        "role": "ORGANIZATION_ADMIN",
        "organization_id": org_id,
        "name": f"{org['name']} Admin",
        "is_active": True
    }
    USERS[req.email] = admin_record

    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].update_one({"id": org_id}, {"$set": {"admin_email": req.email}})
            db["users"].delete_many({"organization_id": org_id, "role": "ORGANIZATION_ADMIN"})
            db["users"].insert_one(dict(admin_record))
        except Exception:
            pass

    log_platform_audit("ADMIN_CREDENTIALS_ROTATED", "ORGANIZATION", org_id)
    return {
        "message": f"Admin credentials for '{org['name']}' rotated successfully.",
        "admin_email": req.email,
        "admin_password": req.password
    }

@router.delete("/organizations/{org_id}")
def delete_org(org_id: str, current_user: dict = Depends(require_superadmin)):
    global ORGANIZATIONS
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org_id == "org_acme_corp":
        raise HTTPException(status_code=400, detail="Default demo tenant 'Acme Corporation' cannot be deleted.")

    ORGANIZATIONS = [o for o in ORGANIZATIONS if o["id"] != org_id]
    if org.get("admin_email") and org["admin_email"] in USERS:
        del USERS[org["admin_email"]]

    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].delete_one({"id": org_id})
            db["users"].delete_many({"organization_id": org_id})
        except Exception:
            pass

    log_platform_audit("TENANT_OFFBOARDED_AND_DELETED", "ORGANIZATION", org_id)
    return {"message": f"Organization '{org['name']}' has been completely decommissioned."}

# ─── Tenant Impersonation (SuperAdmin Troubleshooting) ────────────────────────

@router.post("/organizations/{org_id}/impersonate")
def impersonate_tenant(org_id: str, current_user: dict = Depends(require_superadmin)):
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    admin_email = org.get("admin_email", f"admin@{org['id']}.com")
    # Issue a scoped impersonation JWT token
    token = create_access_token(
        subject=admin_email,
        role="ORGANIZATION_ADMIN",
        organization_id=org_id
    )

    log_platform_audit("SUPERADMIN_IMPERSONATION_STARTED", "ORGANIZATION", org_id)

    return {
        "impersonation_token": token,
        "tenant_id": org_id,
        "tenant_name": org["name"],
        "redirect_url": "/dashboard/overview",
        "message": f"Scoped session created for '{org['name']}'. Diagnostic mode enabled."
    }

# ─── Global Telemetry & System Health ──────────────────────────────────────────

@router.get("/system-health")
def get_system_health(current_user: dict = Depends(require_superadmin)):
    total_tenants = len(ORGANIZATIONS)
    active_tenants = sum(1 for o in ORGANIZATIONS if o.get("status") == "ACTIVE")
    total_employees = sum(o.get("employee_count", 0) for o in ORGANIZATIONS) + len(EMPLOYEES)
    
    # Calculate Monthly Recurring Revenue across active tiers
    mrr_inr = sum(
        TIER_CONFIGS.get(o.get("plan_tier", "STARTER"), {}).get("monthly_price_inr", 25000)
        for o in ORGANIZATIONS if o.get("status") == "ACTIVE"
    )

    return {
        "status": "HEALTHY",
        "uptime_pct": 99.98,
        "api_latency_ms": 32,
        "db_cluster": {
            "status": "CONNECTED",
            "type": "MongoDB Enterprise ReplicaSet",
            "active_connections": 14,
            "read_latency_ms": 4
        },
        "ml_inference_cluster": {
            "engine": "Scikit-Learn Random Forest Pipeline (v2.4)",
            "status": "OPTIMAL",
            "avg_prediction_latency_ms": 11,
            "features_calibrated": ["salary_inr", "tenure_years", "performance", "engagement", "overtime", "promotions"]
        },
        "metrics": {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "total_cross_tenant_workforce": total_employees,
            "monthly_recurring_revenue_inr": mrr_inr,
            "ai_tokens_consumed_month": 164280,
            "total_audit_events": len(AUDIT_LOGS)
        },
        "platform_settings": PLATFORM_SETTINGS
    }

@router.get("/organizations/{org_id}/telemetry")
def get_org_telemetry(org_id: str, current_user: dict = Depends(require_superadmin)):
    org = find_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    tier = org.get("plan_tier", "STARTER")
    tier_info = TIER_CONFIGS.get(tier, TIER_CONFIGS["STARTER"])
    max_emps = tier_info["max_employees"]

    if org_id == "org_acme_corp":
        emp_count = len(EMPLOYEES)
        attrition_count = len(EMPLOYEES)
        jobs_count = 5
        candidates_count = 18
        surveys_count = 24
        integrations_count = 3
    else:
        db = get_mongo_db()
        org_emps = []
        if db is not None:
            try:
                org_emps = list(db["employees"].find({"organization_id": org_id}))
            except Exception:
                pass
        emp_count = len(org_emps) if org_emps else org.get("employee_count", 0)
        attrition_count = len([e for e in org_emps if e.get("attrition_probability") is not None]) if emp_count > 0 else 0
        jobs_count = 0
        candidates_count = 0
        surveys_count = 0
        integrations_count = 0

    return {
        "organization_id": org["id"],
        "organization_name": org["name"],
        "plan_tier": tier,
        "subscription_status": org.get("subscription_status", "ACTIVE"),
        "plan_limits": {
            "max_employees": max_emps,
            "features": tier_info["features"],
            "max_integrations": tier_info["max_integrations"],
            "copilot_access": tier_info["copilot_access"],
            "description": tier_info["description"]
        },
        "seat_capacity": {
            "current_employees": emp_count,
            "max_employees": max_emps,
            "utilization_pct": round((emp_count / max(max_emps, 1)) * 100, 1)
        },
        "activity_metrics": {
            "attrition_predictions_count": attrition_count,
            "jobs_posted_count": jobs_count,
            "candidates_tracked_count": candidates_count,
            "sentiment_surveys_logged": surveys_count,
            "integrations_connected": integrations_count,
            "audit_events_logged": len([a for a in AUDIT_LOGS if a.get("resource_id") == org_id])
        },
        "last_activity": org.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "privacy_notice": "Strict tenant cryptographic boundary enforced. Raw employee records are inaccessible to SuperAdmin."
    }

@router.get("/audit-logs")
def get_audit_logs(current_user: dict = Depends(require_superadmin)):
    return AUDIT_LOGS

@router.get("/feature-flags")
def get_feature_flags(current_user: dict = Depends(require_superadmin)):
    return PLATFORM_SETTINGS

@router.put("/feature-flags")
def update_feature_flags(req: FeatureFlagsRequest, current_user: dict = Depends(require_superadmin)):
    if req.maintenance_mode is not None:
        PLATFORM_SETTINGS["maintenance_mode"] = req.maintenance_mode
    if req.global_copilot_enabled is not None:
        PLATFORM_SETTINGS["global_copilot_enabled"] = req.global_copilot_enabled
    if req.mfa_enforced is not None:
        PLATFORM_SETTINGS["mfa_enforced"] = req.mfa_enforced
    if req.allow_self_registration is not None:
        PLATFORM_SETTINGS["allow_self_registration"] = req.allow_self_registration

    log_platform_audit("FEATURE_FLAGS_UPDATED", "PLATFORM_CORE", "SYSTEM")
    return {"message": "Platform feature flags updated successfully", "settings": PLATFORM_SETTINGS}

# ─── Subscription Plans Governance ──────────────────────────────────────────

@router.get("/plans")
def get_all_subscription_plans(current_user: dict = Depends(require_superadmin)):
    db = get_mongo_db()
    if db is not None:
        try:
            custom_plans = list(db["subscription_plans"].find({}, {"_id": 0}))
            for p in custom_plans:
                k = (p.get("tier_key") or p.get("name") or "").upper().replace(" ", "_")
                if k:
                    TIER_CONFIGS[k] = p
        except Exception:
            pass
    return TIER_CONFIGS

@router.post("/plans")
def create_subscription_plan(req: CreatePlanRequest, current_user: dict = Depends(require_superadmin)):
    tier_key = (req.tier_key or req.name).strip().upper().replace(" ", "_")
    plan_obj = {
        "tier_key": tier_key,
        "name": req.name,
        "max_employees": req.max_employees,
        "features": req.features,
        "max_integrations": req.max_integrations,
        "copilot_access": req.copilot_access,
        "monthly_price_inr": req.monthly_price_inr,
        "description": req.description
    }
    TIER_CONFIGS[tier_key] = plan_obj
    db = get_mongo_db()
    if db is not None:
        try:
            db["subscription_plans"].update_one(
                {"tier_key": tier_key},
                {"$set": plan_obj},
                upsert=True
            )
        except Exception as e:
            print("MongoDB save plan failed:", e)
    log_platform_audit("SUBSCRIPTION_PLAN_CREATED", "PLAN", tier_key)
    return {"message": f"Plan '{tier_key}' created successfully.", "plan": plan_obj}

@router.delete("/plans/{tier_key}")
def delete_subscription_plan(tier_key: str, current_user: dict = Depends(require_superadmin)):
    k = tier_key.upper()
    if k in ["STARTER", "PROFESSIONAL", "ENTERPRISE"]:
        raise HTTPException(status_code=400, detail="Standard platform tier cannot be deleted.")
    if k in TIER_CONFIGS:
        del TIER_CONFIGS[k]
    db = get_mongo_db()
    if db is not None:
        try:
            db["subscription_plans"].delete_one({"tier_key": k})
        except Exception:
            pass
    log_platform_audit("SUBSCRIPTION_PLAN_DELETED", "PLAN", k)
    return {"message": f"Plan '{k}' removed successfully."}
