from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from app.models.organization import Organization
from app.models.user import User
from app.api.deps import require_platform_admin
from app.core import security
from beanie import PydanticObjectId

router = APIRouter()

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "STARTER": {
        "max_employees": 50,
        "features": ["core_workforce", "csv_import", "attrition_prediction"],
        "max_integrations": 0,
        "copilot_access": False,
        "description": "Essential HR workforce tracking and basic attrition prediction for small teams.",
    },
    "PROFESSIONAL": {
        "max_employees": 250,
        "features": [
            "core_workforce",
            "csv_import",
            "attrition_prediction",
            "recruitment_ats",
            "skill_gap_analysis",
            "career_pathing",
            "sentiment_intelligence",
        ],
        "max_integrations": 1,
        "copilot_access": False,
        "description": "Full HR intelligence suite including ATS recruitment, skill matching, and workplace sentiment analysis.",
    },
    "ENTERPRISE": {
        "max_employees": 5000,
        "features": [
            "core_workforce",
            "csv_import",
            "attrition_prediction",
            "recruitment_ats",
            "skill_gap_analysis",
            "career_pathing",
            "sentiment_intelligence",
            "grok_copilot_rag",
            "executive_insights",
        ],
        "max_integrations": 99,
        "copilot_access": True,
        "description": "Unlimited enterprise scale with Grok AI Copilot, deep integrations, and dedicated intelligence analytics.",
    },
}

class OrganizationResponse(BaseModel):
    id: str
    name: str
    industry: str | None = None
    company_size: str | None = None
    status: str
    plan_tier: str = "STARTER"
    subscription_status: str = "ACTIVE"
    plan_limits: dict | None = None
    admin_email: str | None = None
    employee_count: int = 0
    created_at: datetime | None = None
    
    class Config:
        from_attributes = True

class CreateOrganizationRequest(BaseModel):
    name: str
    industry: str | None = None
    company_size: str | None = None
    plan_tier: str = "STARTER"

class UpdateOrganizationRequest(BaseModel):
    name: str | None = None
    industry: str | None = None
    company_size: str | None = None

class UpdatePlanRequest(BaseModel):
    plan_tier: str
    subscription_status: Optional[str] = "ACTIVE"

class OrganizationTelemetryResponse(BaseModel):
    organization_id: str
    organization_name: str
    plan_tier: str
    subscription_status: str
    plan_limits: dict
    seat_capacity: dict
    activity_metrics: dict
    last_activity: Optional[datetime] = None
    privacy_notice: str = "🔒 Strict Tenant Isolation Enforced: Only operational metrics and system telemetry are shared. Employee PII, compensation details, and survey text remain strictly confidential."

class CreateOrgAdminRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterTenantWithAdminRequest(BaseModel):
    organization_name: str
    industry: str | None = None
    company_size: str | None = None
    plan_tier: str = "STARTER"
    admin_email: EmailStr
    admin_password: str

class RegisterTenantWithAdminResponse(BaseModel):
    organization_id: str
    organization_name: str
    plan_tier: str
    admin_email: str
    admin_password: str
    status: str
    message: str

@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    current_admin: User = Depends(require_platform_admin)
):
    from app.models.employee import Employee
    orgs = await Organization.find_all().to_list()
    results = []
    for org in orgs:
        admin_user = await User.find_one({
            "$or": [
                {"organization_id": org.id},
                {"organization_id.$id": org.id}
            ],
            "role": "ORGANIZATION_ADMIN"
        })
        emp_count = await Employee.find({
            "$or": [
                {"organization_id": org.id},
                {"organization_id.$id": org.id}
            ]
        }).count()
        tier = getattr(org, "plan_tier", "STARTER")
        results.append(OrganizationResponse(
            id=str(org.id),
            name=org.name,
            industry=org.industry,
            company_size=org.company_size,
            status=org.status,
            plan_tier=tier,
            subscription_status=getattr(org, "subscription_status", "ACTIVE"),
            plan_limits=getattr(org, "plan_limits", None) or TIER_LIMITS.get(tier, TIER_LIMITS["STARTER"]),
            admin_email=admin_user.email if admin_user else None,
            employee_count=emp_count,
            created_at=getattr(org, "created_at", None)
        ))
    return results

@router.post("/register-tenant", response_model=RegisterTenantWithAdminResponse)
async def platform_register_tenant(
    req: RegisterTenantWithAdminRequest,
    current_admin: User = Depends(require_platform_admin)
):
    if await User.find_one(User.email == req.admin_email):
        raise HTTPException(status_code=400, detail="An account with this customer email already exists")

    tier = (req.plan_tier or "STARTER").upper()
    if tier not in TIER_LIMITS:
        tier = "STARTER"
    limits = TIER_LIMITS[tier]

    org = Organization(
        name=req.organization_name,
        industry=req.industry,
        company_size=req.company_size,
        status="ACTIVE",
        plan_tier=tier,
        plan_limits=limits,
        subscription_status="ACTIVE"
    )
    await org.insert()

    user = User(
        organization_id=org,
        email=req.admin_email,
        password_hash=security.get_password_hash(req.admin_password),
        role="ORGANIZATION_ADMIN",
        is_active=True
    )
    await user.insert()

    from app.models.audit import AuditLog
    audit_log = AuditLog(
        organization_id=org,
        user_id=current_admin,
        action="TENANT_PROVISIONED_BY_SUPERADMIN",
        resource_type="Organization",
        resource_id=str(org.id),
        status="SUCCESS",
        details=f"Superadmin {current_admin.email} created organization '{org.name}' [Plan: {tier}] with admin {user.email}"
    )
    await audit_log.insert()

    return RegisterTenantWithAdminResponse(
        organization_id=str(org.id),
        organization_name=org.name,
        plan_tier=org.plan_tier,
        admin_email=user.email,
        admin_password=req.admin_password,
        status=org.status,
        message="Organization and customer admin successfully created"
    )

@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    req: CreateOrganizationRequest,
    current_admin: User = Depends(require_platform_admin)
):
    tier = (req.plan_tier or "STARTER").upper()
    if tier not in TIER_LIMITS:
        tier = "STARTER"
    limits = TIER_LIMITS[tier]

    org = Organization(
        name=req.name,
        industry=req.industry,
        company_size=req.company_size,
        status="ACTIVE",
        plan_tier=tier,
        plan_limits=limits,
        subscription_status="ACTIVE"
    )
    await org.insert()
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        company_size=org.company_size,
        status=org.status,
        plan_tier=org.plan_tier,
        subscription_status=org.subscription_status,
        plan_limits=org.plan_limits
    )

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_admin: User = Depends(require_platform_admin)
):
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    from app.models.employee import Employee
    admin_user = await User.find_one({
        "$or": [
            {"organization_id": org.id},
            {"organization_id.$id": org.id}
        ],
        "role": "ORGANIZATION_ADMIN"
    })
    emp_count = await Employee.find({
        "$or": [
            {"organization_id": org.id},
            {"organization_id.$id": org.id}
        ]
    }).count()

    tier = getattr(org, "plan_tier", "STARTER")
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        company_size=org.company_size,
        status=org.status,
        plan_tier=tier,
        subscription_status=getattr(org, "subscription_status", "ACTIVE"),
        plan_limits=getattr(org, "plan_limits", None) or TIER_LIMITS.get(tier, TIER_LIMITS["STARTER"]),
        admin_email=admin_user.email if admin_user else None,
        employee_count=emp_count,
        created_at=getattr(org, "created_at", None)
    )

@router.put("/organizations/{org_id}/plan")
async def update_organization_plan(
    org_id: str,
    req: UpdatePlanRequest,
    current_admin: User = Depends(require_platform_admin)
):
    tier = req.plan_tier.upper()
    if tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail=f"Invalid plan tier '{req.plan_tier}'. Must be one of {list(TIER_LIMITS.keys())}")
    
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    old_tier = getattr(org, "plan_tier", "STARTER")
    org.plan_tier = tier
    org.plan_limits = TIER_LIMITS[tier]
    if req.subscription_status:
        org.subscription_status = req.subscription_status
    await org.save()

    from app.models.audit import AuditLog
    audit_log = AuditLog(
        organization_id=org,
        user_id=current_admin,
        action="PLAN_TIER_UPDATED",
        resource_type="Organization",
        resource_id=str(org.id),
        status="SUCCESS",
        details=f"Superadmin {current_admin.email} updated plan for '{org.name}' from {old_tier} to {tier}"
    )
    await audit_log.insert()

    return {
        "message": f"Organization plan updated to {tier}",
        "plan_tier": tier,
        "plan_limits": org.plan_limits,
        "subscription_status": org.subscription_status
    }

@router.get("/organizations/{org_id}/telemetry", response_model=OrganizationTelemetryResponse)
async def get_organization_telemetry(
    org_id: str,
    current_admin: User = Depends(require_platform_admin)
):
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    from app.models.employee import Employee
    from app.models.attrition import AttritionPrediction
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.sentiment import EmployeeFeedback
    from app.integrations.models.integration import Integration
    from app.models.audit import AuditLog

    tenant_filter = {
        "$or": [
            {"organization_id": org.id},
            {"organization_id.$id": org.id}
        ]
    }

    # Aggregate metric counters without exposing any raw customer PII, salaries or feedback content
    emp_count = await Employee.find(tenant_filter).count()
    attrition_count = await AttritionPrediction.find(tenant_filter).count()
    job_count = await Job.find(tenant_filter).count()
    candidate_count = await Candidate.find(tenant_filter).count()
    feedback_count = await EmployeeFeedback.find(tenant_filter).count()
    integration_count = await Integration.find(tenant_filter).count()
    audit_count = await AuditLog.find(tenant_filter).count()

    tier = getattr(org, "plan_tier", "STARTER")
    limits = getattr(org, "plan_limits", None) or TIER_LIMITS.get(tier, TIER_LIMITS["STARTER"])
    max_employees = limits.get("max_employees", 50)
    utilization = round((emp_count / max_employees * 100), 1) if max_employees > 0 else 0.0

    last_log = await AuditLog.find(tenant_filter).sort("-timestamp").first_or_none()
    last_activity = last_log.timestamp if last_log else getattr(org, "created_at", None)

    return OrganizationTelemetryResponse(
        organization_id=str(org.id),
        organization_name=org.name,
        plan_tier=tier,
        subscription_status=getattr(org, "subscription_status", "ACTIVE"),
        plan_limits=limits,
        seat_capacity={
            "current_employees": emp_count,
            "max_employees": max_employees,
            "utilization_pct": min(utilization, 100.0)
        },
        activity_metrics={
            "attrition_predictions_count": attrition_count,
            "jobs_posted_count": job_count,
            "candidates_tracked_count": candidate_count,
            "sentiment_surveys_logged": feedback_count,
            "integrations_connected": integration_count,
            "audit_events_logged": audit_count
        },
        last_activity=last_activity
    )

@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    req: UpdateOrganizationRequest,
    current_admin: User = Depends(require_platform_admin)
):
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if req.name is not None:
        org.name = req.name
    if req.industry is not None:
        org.industry = req.industry
    if req.company_size is not None:
        org.company_size = req.company_size
        
    await org.save()
    tier = getattr(org, "plan_tier", "STARTER")
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        industry=org.industry,
        company_size=org.company_size,
        status=org.status,
        plan_tier=tier,
        subscription_status=getattr(org, "subscription_status", "ACTIVE"),
        plan_limits=getattr(org, "plan_limits", None) or TIER_LIMITS.get(tier, TIER_LIMITS["STARTER"])
    )

@router.post("/organizations/{org_id}/admin")
async def create_organization_admin(
    org_id: str,
    req: CreateOrgAdminRequest,
    current_admin: User = Depends(require_platform_admin)
):
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    existing_user = await User.find_one(User.email == req.email)
    if existing_user:
        existing_user.password_hash = security.get_password_hash(req.password)
        existing_user.role = "ORGANIZATION_ADMIN"
        existing_user.organization_id = org
        existing_user.is_active = True
        await existing_user.save()
        return {"message": "Admin credentials updated successfully", "user_id": str(existing_user.id)}

    user = User(
        organization_id=org,
        email=req.email,
        password_hash=security.get_password_hash(req.password),
        role="ORGANIZATION_ADMIN",
        is_active=True
    )
    await user.insert()
    return {"message": "Admin created successfully", "user_id": str(user.id)}

@router.put("/organizations/{org_id}/status")
async def update_organization_status(
    org_id: str,
    status: str,
    current_admin: User = Depends(require_platform_admin)
):
    if status not in ["ACTIVE", "SUSPENDED", "INACTIVE"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    org = await Organization.get(PydanticObjectId(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    org.status = status
    await org.save()
    return {"message": "Status updated successfully"}

class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str | None
    status: str
    timestamp: datetime

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    current_admin: User = Depends(require_platform_admin)
):
    from app.models.audit import AuditLog
    logs = await AuditLog.find_all().sort("-timestamp").to_list()
    return [
        AuditLogResponse(
            id=str(log.id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            status=log.status,
            timestamp=log.timestamp
        ) for log in logs
    ]
