from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timezone

from app.models.user import User
from app.models.employee import Employee
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath
from app.models.audit import AuditLog
from app.schemas.intelligence import (
    SkillCreate, SkillUpdate, SkillResponse,
    RoleRequirementCreate, RoleRequirementUpdate, RoleRequirementResponse,
    SkillGapAnalyzeRequest, SkillGapResponse, SkillGapAnalyticsResponse,
    CareerPathCreate, CareerPathUpdate, CareerPathGenerateRequest, CareerPathResponse, CareerPathAnalyticsResponse
)
from app.api.deps import (
    get_current_active_user,
    require_organization_admin,
    require_hr_manager,
    require_hr_analyst,
)
from app.intelligence.services.skill_gap_service import SkillGapService, get_org_id
from app.intelligence.services.career_path_service import CareerPathService

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# 1. SKILL TAXONOMY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/skills", response_model=List[SkillResponse])
async def get_skills(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_hr_analyst)
):
    """Retrieve skill taxonomy. Includes global skills and organization-specific skills."""
    org_id = get_org_id(current_user.organization_id)
    await SkillGapService.ensure_default_taxonomy()

    query: Dict[str, Any] = {
        "$or": [
            {"organization_id": None},
            {"organization_id.$id": org_id}
        ]
    }
    if category and category.lower() != "all":
        query["category"] = category

    skills = await Skill.find(query).to_list()
    if search:
        s_lower = search.lower()
        skills = [s for s in skills if s_lower in s.name.lower() or any(s_lower in a.lower() for a in s.aliases)]

    return [
        SkillResponse(
            id=str(s.id),
            skill_id=s.skill_id,
            name=s.name,
            aliases=s.aliases,
            category=s.category,
            description=s.description,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in skills
    ]

@router.post("/skills", response_model=SkillResponse)
async def create_skill(
    req: SkillCreate,
    current_user: User = Depends(require_hr_manager)
):
    """Create a new skill in taxonomy for this organization."""
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    await SkillGapService.ensure_default_taxonomy()

    # Check if duplicate name exists
    existing = await Skill.find_one({
        "$or": [{"organization_id": None}, {"organization_id.$id": org_id}],
        "name": {"$regex": f"^{req.name.strip()}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail=f"Skill '{req.name}' already exists in taxonomy")

    skill = Skill(
        name=req.name.strip(),
        aliases=[a.strip() for a in req.aliases if a.strip()],
        category=req.category.strip(),
        description=req.description,
        organization_id=org_ref,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await skill.insert()

    # Audit Log
    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SKILL_CREATED",
        resource_type="Skill",
        resource_id=skill.skill_id,
        status="SUCCESS"
    ).insert()

    return SkillResponse(
        id=str(skill.id),
        skill_id=skill.skill_id,
        name=skill.name,
        aliases=skill.aliases,
        category=skill.category,
        description=skill.description,
        created_at=skill.created_at,
        updated_at=skill.updated_at
    )

@router.get("/skills/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    skill = await Skill.find_one({
        "skill_id": skill_id,
        "$or": [{"organization_id": None}, {"organization_id.$id": org_id}]
    })
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillResponse(
        id=str(skill.id),
        skill_id=skill.skill_id,
        name=skill.name,
        aliases=skill.aliases,
        category=skill.category,
        description=skill.description,
        created_at=skill.created_at,
        updated_at=skill.updated_at
    )

@router.put("/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    req: SkillUpdate,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    skill = await Skill.find_one({
        "skill_id": skill_id,
        "$or": [{"organization_id": None}, {"organization_id.$id": org_id}]
    })
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if req.name is not None:
        skill.name = req.name.strip()
    if req.aliases is not None:
        skill.aliases = [a.strip() for a in req.aliases if a.strip()]
    if req.category is not None:
        skill.category = req.category.strip()
    if req.description is not None:
        skill.description = req.description
    skill.updated_at = datetime.now(timezone.utc)
    await skill.save()

    # Audit Log
    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SKILL_UPDATED",
        resource_type="Skill",
        resource_id=skill.skill_id,
        status="SUCCESS"
    ).insert()

    return SkillResponse(
        id=str(skill.id),
        skill_id=skill.skill_id,
        name=skill.name,
        aliases=skill.aliases,
        category=skill.category,
        description=skill.description,
        created_at=skill.created_at,
        updated_at=skill.updated_at
    )

@router.delete("/skills/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    skill = await Skill.find_one({"skill_id": skill_id, "organization_id.$id": org_id})
    if not skill:
        # Check if it was global
        global_skill = await Skill.find_one({"skill_id": skill_id, "organization_id": None})
        if global_skill:
            raise HTTPException(status_code=403, detail="Standard platform taxonomy skills cannot be deleted")
        raise HTTPException(status_code=404, detail="Skill not found")

    await skill.delete()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SKILL_DELETED",
        resource_type="Skill",
        resource_id=skill_id,
        status="SUCCESS"
    ).insert()

    return {"message": "Skill deleted successfully"}

# ─────────────────────────────────────────────────────────────────────────────
# 2. ROLE SKILL REQUIREMENTS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/role-requirements", response_model=List[RoleRequirementResponse])
async def get_role_requirements(
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    reqs = await RoleSkillRequirement.find({"organization_id.$id": org_id}).to_list()
    return [
        RoleRequirementResponse(
            id=str(r.id),
            requirement_id=r.requirement_id,
            role=r.role,
            required_skills=r.required_skills,
            preferred_skills=r.preferred_skills,
            skill_levels=r.skill_levels,
            created_at=r.created_at,
            updated_at=r.updated_at
        ) for r in reqs
    ]

@router.post("/role-requirements", response_model=RoleRequirementResponse)
async def create_role_requirement(
    req: RoleRequirementCreate,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    existing = await RoleSkillRequirement.find_one({
        "organization_id.$id": org_id,
        "role": {"$regex": f"^{req.role.strip()}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail=f"Role requirement for '{req.role}' already exists. Use update instead.")

    record = RoleSkillRequirement(
        organization_id=org_ref,
        role=req.role.strip(),
        required_skills=[s.strip() for s in req.required_skills if s.strip()],
        preferred_skills=[s.strip() for s in req.preferred_skills if s.strip()],
        skill_levels=req.skill_levels,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await record.insert()

    # Audit Log
    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="ROLE_REQUIREMENTS_CREATED",
        resource_type="RoleSkillRequirement",
        resource_id=record.requirement_id,
        status="SUCCESS"
    ).insert()

    return RoleRequirementResponse(
        id=str(record.id),
        requirement_id=record.requirement_id,
        role=record.role,
        required_skills=record.required_skills,
        preferred_skills=record.preferred_skills,
        skill_levels=record.skill_levels,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

@router.get("/role-requirements/{requirement_id}", response_model=RoleRequirementResponse)
async def get_role_requirement(
    requirement_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    rec = await RoleSkillRequirement.find_one({
        "requirement_id": requirement_id,
        "organization_id.$id": org_id
    })
    if not rec:
        raise HTTPException(status_code=404, detail="Role requirement not found")
    return RoleRequirementResponse(
        id=str(rec.id),
        requirement_id=rec.requirement_id,
        role=rec.role,
        required_skills=rec.required_skills,
        preferred_skills=rec.preferred_skills,
        skill_levels=rec.skill_levels,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )

@router.put("/role-requirements/{requirement_id}", response_model=RoleRequirementResponse)
async def update_role_requirement(
    requirement_id: str,
    req: RoleRequirementUpdate,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    rec = await RoleSkillRequirement.find_one({
        "requirement_id": requirement_id,
        "organization_id.$id": org_id
    })
    if not rec:
        raise HTTPException(status_code=404, detail="Role requirement not found")

    if req.role is not None:
        rec.role = req.role.strip()
    if req.required_skills is not None:
        rec.required_skills = [s.strip() for s in req.required_skills if s.strip()]
    if req.preferred_skills is not None:
        rec.preferred_skills = [s.strip() for s in req.preferred_skills if s.strip()]
    if req.skill_levels is not None:
        rec.skill_levels = req.skill_levels
    rec.updated_at = datetime.now(timezone.utc)
    await rec.save()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="ROLE_REQUIREMENTS_UPDATED",
        resource_type="RoleSkillRequirement",
        resource_id=rec.requirement_id,
        status="SUCCESS"
    ).insert()

    return RoleRequirementResponse(
        id=str(rec.id),
        requirement_id=rec.requirement_id,
        role=rec.role,
        required_skills=rec.required_skills,
        preferred_skills=rec.preferred_skills,
        skill_levels=rec.skill_levels,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )

@router.delete("/role-requirements/{requirement_id}")
async def delete_role_requirement(
    requirement_id: str,
    current_user: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    rec = await RoleSkillRequirement.find_one({
        "requirement_id": requirement_id,
        "organization_id.$id": org_id
    })
    if not rec:
        raise HTTPException(status_code=404, detail="Role requirement not found")

    await rec.delete()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="ROLE_REQUIREMENTS_DELETED",
        resource_type="RoleSkillRequirement",
        resource_id=requirement_id,
        status="SUCCESS"
    ).insert()

    return {"message": "Role requirement deleted successfully"}

# ─────────────────────────────────────────────────────────────────────────────
# 3. SKILL GAP ANALYSIS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/skill-gaps/analyze", response_model=SkillGapResponse)
async def analyze_skill_gap(
    req: SkillGapAnalyzeRequest,
    current_user: User = Depends(require_hr_manager)
):
    """Run dynamic skill gap analysis for an employee against a target role."""
    org_id = get_org_id(current_user.organization_id)
    try:
        analysis = await SkillGapService.analyze_gap(
            employee_id=req.employee_id,
            target_role=req.target_role,
            org_id=org_id,
            user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Fetch employee name for response
    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == req.employee_id)
    emp_name = emp.name if emp else req.employee_id

    return SkillGapResponse(
        analysis_id=analysis.analysis_id,
        employee_id=analysis.employee_id,
        employee_name=emp_name,
        current_role=analysis.current_role,
        target_role=analysis.target_role,
        skill_coverage_score=analysis.skill_coverage_score,
        matched_count=len(analysis.matched_skills),
        missing_count=len(analysis.missing_skills),
        partial_count=len(analysis.partial_skills),
        total_required_skills=len(analysis.matched_skills) + len(analysis.missing_skills) + len(analysis.partial_skills),
        matched_skills=analysis.matched_skills,
        missing_skills=analysis.missing_skills,
        partial_skills=analysis.partial_skills,
        recommended_development_areas=analysis.recommended_development_areas,
        created_at=analysis.created_at
    )

@router.get("/skill-gaps/employees/{employee_id}", response_model=List[SkillGapResponse])
async def get_employee_skill_gaps(
    employee_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    """Retrieve all historical skill gap analyses performed for an employee."""
    org_id = get_org_id(current_user.organization_id)
    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    analyses = await SkillGapAnalysis.find(
        {"organization_id.$id": org_id},
        SkillGapAnalysis.employee_id == employee_id
    ).sort("-created_at").to_list()

    return [
        SkillGapResponse(
            analysis_id=a.analysis_id,
            employee_id=a.employee_id,
            employee_name=emp.name,
            current_role=a.current_role,
            target_role=a.target_role,
            skill_coverage_score=a.skill_coverage_score,
            matched_count=len(a.matched_skills),
            missing_count=len(a.missing_skills),
            partial_count=len(a.partial_skills),
            total_required_skills=len(a.matched_skills) + len(a.missing_skills) + len(a.partial_skills),
            matched_skills=a.matched_skills,
            missing_skills=a.missing_skills,
            partial_skills=a.partial_skills,
            recommended_development_areas=a.recommended_development_areas,
            created_at=a.created_at
        ) for a in analyses
    ]

@router.get("/skill-gaps/analytics", response_model=SkillGapAnalyticsResponse)
async def get_skill_gap_analytics(
    current_user: User = Depends(require_hr_analyst)
):
    """Get organization-wide aggregated skill gap metrics from real database data."""
    org_id = get_org_id(current_user.organization_id)
    analyses = await SkillGapAnalysis.find({"organization_id.$id": org_id}).to_list()
    
    total = len(analyses)
    if total == 0:
        return SkillGapAnalyticsResponse(
            total_employees_analyzed=0,
            average_skill_coverage=0.0,
            top_skill_gaps=[],
            department_breakdown=[],
            role_breakdown=[]
        )

    # Average coverage
    avg_cov = round(sum(a.skill_coverage_score for a in analyses) / total, 2)

    # Top skill gaps
    gap_freq: Dict[str, int] = {}
    for a in analyses:
        for m in a.missing_skills:
            skill = m.get("skill")
            if skill:
                gap_freq[skill] = gap_freq.get(skill, 0) + 1
        for p in a.partial_skills:
            skill = p.get("skill")
            if skill:
                gap_freq[skill] = gap_freq.get(skill, 0) + 1

    sorted_gaps = sorted(gap_freq.items(), key=lambda x: x[1], reverse=True)[:8]
    top_gaps = [{"skill": s, "count": c} for s, c in sorted_gaps]

    # Department and Role Breakdown
    # Retrieve employees mapping
    unique_emp_ids = list(set(a.employee_id for a in analyses))
    employees = await Employee.find({
        "organization_id.$id": org_id,
        "employee_id": {"$in": unique_emp_ids}
    }).to_list()
    emp_dept_map = {e.employee_id: e.department for e in employees}
    emp_role_map = {e.employee_id: e.role for e in employees}

    dept_scores: Dict[str, List[float]] = {}
    role_scores: Dict[str, List[float]] = {}

    for a in analyses:
        dept = emp_dept_map.get(a.employee_id, "General")
        dept_scores.setdefault(dept, []).append(a.skill_coverage_score)
        role = emp_role_map.get(a.employee_id, a.current_role)
        role_scores.setdefault(role, []).append(a.skill_coverage_score)

    dept_breakdown = [
        {"department": dept, "avg_coverage": round(sum(scs) / len(scs), 1), "analyzed_count": len(scs)}
        for dept, scs in dept_scores.items()
    ]
    role_breakdown = [
        {"role": role, "avg_coverage": round(sum(scs) / len(scs), 1), "analyzed_count": len(scs)}
        for role, scs in role_scores.items()
    ]

    return SkillGapAnalyticsResponse(
        total_employees_analyzed=len(unique_emp_ids),
        average_skill_coverage=avg_cov,
        top_skill_gaps=top_gaps,
        department_breakdown=dept_breakdown,
        role_breakdown=role_breakdown
    )

@router.get("/skill-gaps/{analysis_id}", response_model=SkillGapResponse)
async def get_skill_gap_by_id(
    analysis_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    a = await SkillGapAnalysis.find_one({
        "analysis_id": analysis_id,
        "organization_id.$id": org_id
    })
    if not a:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")

    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == a.employee_id)
    emp_name = emp.name if emp else a.employee_id

    return SkillGapResponse(
        analysis_id=a.analysis_id,
        employee_id=a.employee_id,
        employee_name=emp_name,
        current_role=a.current_role,
        target_role=a.target_role,
        skill_coverage_score=a.skill_coverage_score,
        matched_count=len(a.matched_skills),
        missing_count=len(a.missing_skills),
        partial_count=len(a.partial_skills),
        total_required_skills=len(a.matched_skills) + len(a.missing_skills) + len(a.partial_skills),
        matched_skills=a.matched_skills,
        missing_skills=a.missing_skills,
        partial_skills=a.partial_skills,
        recommended_development_areas=a.recommended_development_areas,
        created_at=a.created_at
    )

@router.delete("/skill-gaps/{analysis_id}")
async def delete_skill_gap(
    analysis_id: str,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    a = await SkillGapAnalysis.find_one({
        "analysis_id": analysis_id,
        "organization_id.$id": org_id
    })
    if not a:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")
    await a.delete()
    return {"message": "Skill gap analysis deleted successfully"}

# ─────────────────────────────────────────────────────────────────────────────
# 4. CAREER PATHING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/career-paths/generate", response_model=CareerPathResponse)
async def generate_career_path(
    req: CareerPathGenerateRequest,
    current_user: User = Depends(require_hr_manager)
):
    """Generate an AI-assisted personalized career path for an employee."""
    org_id = get_org_id(current_user.organization_id)
    try:
        career_path = await CareerPathService.generate_career_path(
            employee_id=req.employee_id,
            target_role=req.target_role,
            org_id=org_id,
            user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == req.employee_id)
    emp_name = emp.name if emp else req.employee_id

    return CareerPathResponse(
        career_path_id=career_path.career_path_id,
        employee_id=career_path.employee_id,
        employee_name=emp_name,
        current_role=career_path.current_role,
        target_role=career_path.target_role,
        estimated_skill_coverage=career_path.estimated_skill_coverage,
        required_skills=career_path.required_skills,
        current_skills=career_path.current_skills,
        missing_skills=career_path.missing_skills,
        recommended_actions=career_path.recommended_actions,
        milestones=career_path.milestones,
        status=career_path.status,
        performance_context=career_path.performance_context,
        is_ai_assisted=True,
        disclaimer="AI-assisted recommendation for career planning. Does not constitute a guaranteed promotion.",
        created_at=career_path.created_at,
        updated_at=career_path.updated_at
    )

@router.get("/career-paths", response_model=List[CareerPathResponse])
async def get_career_paths(
    status_filter: Optional[str] = Query(None, alias="status"),
    employee_id: Optional[str] = Query(None),
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    query: Dict[str, Any] = {"organization_id.$id": org_id}
    if status_filter and status_filter.upper() != "ALL":
        query["status"] = status_filter.upper()
    if employee_id:
        query["employee_id"] = employee_id

    paths = await CareerPath.find(query).sort("-updated_at").to_list()

    # Pre-fetch employees for names
    emp_ids = list(set(p.employee_id for p in paths))
    employees = await Employee.find({"organization_id.$id": org_id, "employee_id": {"$in": emp_ids}}).to_list()
    emp_map = {e.employee_id: e.name for e in employees}

    return [
        CareerPathResponse(
            career_path_id=p.career_path_id,
            employee_id=p.employee_id,
            employee_name=emp_map.get(p.employee_id, p.employee_id),
            current_role=p.current_role,
            target_role=p.target_role,
            estimated_skill_coverage=p.estimated_skill_coverage,
            required_skills=p.required_skills,
            current_skills=p.current_skills,
            missing_skills=p.missing_skills,
            recommended_actions=p.recommended_actions,
            milestones=p.milestones,
            status=p.status,
            performance_context=p.performance_context,
            is_ai_assisted=True,
            disclaimer="AI-assisted recommendation for career planning. Does not constitute a guaranteed promotion.",
            created_at=p.created_at,
            updated_at=p.updated_at
        ) for p in paths
    ]

@router.post("/career-paths", response_model=CareerPathResponse)
async def create_career_path(
    req: CareerPathCreate,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == req.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    cp = CareerPath(
        organization_id=org_ref,
        employee_id=req.employee_id,
        current_role=req.current_role,
        target_role=req.target_role,
        estimated_skill_coverage=req.estimated_skill_coverage,
        required_skills=req.required_skills,
        current_skills=req.current_skills,
        missing_skills=req.missing_skills,
        recommended_actions=req.recommended_actions,
        milestones=req.milestones,
        status=req.status.upper(),
        performance_context=req.performance_context,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await cp.insert()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="CAREER_PATH_CREATED",
        resource_type="CareerPath",
        resource_id=cp.career_path_id,
        status="SUCCESS"
    ).insert()

    return CareerPathResponse(
        career_path_id=cp.career_path_id,
        employee_id=cp.employee_id,
        employee_name=emp.name,
        current_role=cp.current_role,
        target_role=cp.target_role,
        estimated_skill_coverage=cp.estimated_skill_coverage,
        required_skills=cp.required_skills,
        current_skills=cp.current_skills,
        missing_skills=cp.missing_skills,
        recommended_actions=cp.recommended_actions,
        milestones=cp.milestones,
        status=cp.status,
        performance_context=cp.performance_context,
        is_ai_assisted=False,
        disclaimer="Manual HR career path plan.",
        created_at=cp.created_at,
        updated_at=cp.updated_at
    )

@router.get("/career-paths/analytics", response_model=CareerPathAnalyticsResponse)
async def get_career_path_analytics(
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    paths = await CareerPath.find({"organization_id.$id": org_id}).to_list()

    active_count = len([p for p in paths if p.status == "ACTIVE"])
    status_dist = {
        "ACTIVE": len([p for p in paths if p.status == "ACTIVE"]),
        "DRAFT": len([p for p in paths if p.status == "DRAFT"]),
        "COMPLETED": len([p for p in paths if p.status == "COMPLETED"]),
        "ARCHIVED": len([p for p in paths if p.status == "ARCHIVED"]),
    }

    role_counts: Dict[str, int] = {}
    area_counts: Dict[str, int] = {}

    for p in paths:
        role_counts[p.target_role] = role_counts.get(p.target_role, 0) + 1
        for action in p.recommended_actions:
            area_counts[action] = area_counts.get(action, 0) + 1

    sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return CareerPathAnalyticsResponse(
        active_career_paths=active_count,
        target_roles=[{"role": r, "count": c} for r, c in sorted_roles],
        common_development_areas=[{"area": a, "count": c} for a, c in sorted_areas],
        status_distribution=status_dist
    )

@router.get("/career-paths/{career_path_id}", response_model=CareerPathResponse)
async def get_career_path(
    career_path_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    org_id = get_org_id(current_user.organization_id)
    cp = await CareerPath.find_one({
        "career_path_id": career_path_id,
        "organization_id.$id": org_id
    })
    if not cp:
        raise HTTPException(status_code=404, detail="Career path not found")

    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == cp.employee_id)
    emp_name = emp.name if emp else cp.employee_id

    return CareerPathResponse(
        career_path_id=cp.career_path_id,
        employee_id=cp.employee_id,
        employee_name=emp_name,
        current_role=cp.current_role,
        target_role=cp.target_role,
        estimated_skill_coverage=cp.estimated_skill_coverage,
        required_skills=cp.required_skills,
        current_skills=cp.current_skills,
        missing_skills=cp.missing_skills,
        recommended_actions=cp.recommended_actions,
        milestones=cp.milestones,
        status=cp.status,
        performance_context=cp.performance_context,
        is_ai_assisted=True,
        disclaimer="AI-assisted recommendation for career planning. Does not constitute a guaranteed promotion.",
        created_at=cp.created_at,
        updated_at=cp.updated_at
    )

@router.put("/career-paths/{career_path_id}", response_model=CareerPathResponse)
async def update_career_path(
    career_path_id: str,
    req: CareerPathUpdate,
    current_user: User = Depends(require_hr_manager)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    cp = await CareerPath.find_one({
        "career_path_id": career_path_id,
        "organization_id.$id": org_id
    })
    if not cp:
        raise HTTPException(status_code=404, detail="Career path not found")

    if req.status is not None:
        cp.status = req.status.upper()
    if req.milestones is not None:
        cp.milestones = req.milestones
    if req.recommended_actions is not None:
        cp.recommended_actions = req.recommended_actions
    cp.updated_at = datetime.now(timezone.utc)
    await cp.save()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="CAREER_PATH_UPDATED",
        resource_type="CareerPath",
        resource_id=cp.career_path_id,
        status="SUCCESS"
    ).insert()

    emp = await Employee.find_one({"organization_id.$id": org_id}, Employee.employee_id == cp.employee_id)
    emp_name = emp.name if emp else cp.employee_id

    return CareerPathResponse(
        career_path_id=cp.career_path_id,
        employee_id=cp.employee_id,
        employee_name=emp_name,
        current_role=cp.current_role,
        target_role=cp.target_role,
        estimated_skill_coverage=cp.estimated_skill_coverage,
        required_skills=cp.required_skills,
        current_skills=cp.current_skills,
        missing_skills=cp.missing_skills,
        recommended_actions=cp.recommended_actions,
        milestones=cp.milestones,
        status=cp.status,
        performance_context=cp.performance_context,
        is_ai_assisted=True,
        disclaimer="AI-assisted recommendation for career planning. Does not constitute a guaranteed promotion.",
        created_at=cp.created_at,
        updated_at=cp.updated_at
    )

@router.delete("/career-paths/{career_path_id}")
async def delete_career_path(
    career_path_id: str,
    current_user: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    cp = await CareerPath.find_one({
        "career_path_id": career_path_id,
        "organization_id.$id": org_id
    })
    if not cp:
        raise HTTPException(status_code=404, detail="Career path not found")

    await cp.delete()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="CAREER_PATH_DELETED",
        resource_type="CareerPath",
        resource_id=career_path_id,
        status="SUCCESS"
    ).insert()

    return {"message": "Career path deleted successfully"}
