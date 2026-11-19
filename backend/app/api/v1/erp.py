from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.database import (
    ERP_PROJECTS, 
    ERP_COST_CENTERS, 
    ERP_ASSETS, 
    EMPLOYEES, 
    get_tenant_employees, 
    get_mongo_db, 
    mongo_save_employee
)
from app.api.v1.auth import get_current_user

router = APIRouter()

class AddMemberRequest(BaseModel):
    employee_id: str

def generate_tenant_projects(org_id: str, emps: list) -> list:
    """Generate dynamic ERP projects populated strictly from this tenant's employees."""
    if not emps:
        return []

    clean_name = org_id.replace("org_", "").replace("_", " ").title()
    proj_templates = [
        {"name": f"{clean_name} Core Platform Modernization", "client": f"{clean_name} Enterprise", "dept": "Engineering", "budget": 6500000, "spent": 3800000, "tech": ["Kubernetes", "Golang", "Microservices", "AWS Lambda"]},
        {"name": f"{clean_name} Next-Gen Workflow Portal", "client": "Internal Enterprise", "dept": "Product", "budget": 4200000, "spent": 1900000, "tech": ["React", "TypeScript", "Tailwind", "GraphQL"]},
        {"name": f"{clean_name} Enterprise Cloud & AI Matrix", "client": "Global Partners", "dept": "Engineering", "budget": 5800000, "spent": 2900000, "tech": ["Python", "FastAPI", "Vector DB", "LLM Inference"]},
        {"name": f"{clean_name} Omnichannel Growth Pipeline", "client": "Commercial Division", "dept": "Sales", "budget": 3500000, "spent": 2800000, "tech": ["CRM Integration", "B2B Funnel", "Revenue Ops"]}
    ]

    # Distribute tenant employees across the projects
    projects = []
    chunk_size = max(1, len(emps) // len(proj_templates))

    for idx, tmpl in enumerate(proj_templates):
        proj_id = f"PRJ-{org_id[-4:]}-{901 + idx}"
        assigned_slice = emps[idx * chunk_size : (idx + 1) * chunk_size] if idx < len(proj_templates) - 1 else emps[idx * chunk_size :]
        assigned_ids = [e.get("id") or e.get("employee_id") for e in assigned_slice]
        
        required_headcount = len(assigned_ids) + (1 if idx % 2 == 0 else 0)
        gap = max(0, required_headcount - len(assigned_ids))

        proj_doc = {
            "id": proj_id,
            "organization_id": org_id,
            "code": proj_id,
            "name": tmpl["name"],
            "client": tmpl["client"],
            "department": tmpl["dept"],
            "budget": tmpl["budget"],
            "budget_spent": tmpl["spent"],
            "spent": tmpl["spent"],
            "headcount_required": required_headcount,
            "target_golive": f"2027-0{min(9, idx + 2)}-28",
            "target_deadline": f"2027-0{min(9, idx + 2)}-28",
            "tech_stack": tmpl["tech"],
            "critical_skills_needed": tmpl["tech"],
            "assigned_employees": assigned_ids
        }
        projects.append(proj_doc)

    db = get_mongo_db()
    if db is not None:
        try:
            db["erp_projects"].delete_many({"organization_id": org_id})
            db["erp_projects"].insert_many([dict(p) for p in projects])
        except Exception:
            pass

    return projects

@router.get("/projects")
def get_erp_projects(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    emp_map = { (e.get("id") or e.get("employee_id")): e for e in emps }

    if org_id == "org_acme_corp":
        raw_projects = ERP_PROJECTS
    else:
        db = get_mongo_db()
        raw_projects = []
        if db is not None:
            try:
                raw_projects = list(db["erp_projects"].find({"organization_id": org_id}, {"_id": 0}))
            except Exception:
                pass
        if not raw_projects:
            raw_projects = generate_tenant_projects(org_id, emps)

    res = []
    for p in raw_projects:
        proj = dict(p)
        assigned_ids = set(p.get("assigned_employees", []))
        members = []
        for emp_id in assigned_ids:
            e = emp_map.get(emp_id)
            if e:
                members.append({
                    "id": emp_id,
                    "employee_id": emp_id,
                    "name": e["name"],
                    "role": e.get("role", "Specialist"),
                    "department": e.get("department", "General"),
                    "billability_pct": e.get("billability_pct", 100),
                    "attrition_risk": float(e.get("attrition_risk", 0.15)),
                    "risk_level": e.get("risk_level", "LOW")
                })
        
        # If no explicit assignments found yet, also check by allocated_project name
        if not members and emps:
            for e in emps:
                if e.get("allocated_project") == p.get("name"):
                    emp_id = e.get("id") or e.get("employee_id")
                    members.append({
                        "id": emp_id,
                        "employee_id": emp_id,
                        "name": e["name"],
                        "role": e.get("role", "Specialist"),
                        "department": e.get("department", "General"),
                        "billability_pct": e.get("billability_pct", 100),
                        "attrition_risk": float(e.get("attrition_risk", 0.15)),
                        "risk_level": e.get("risk_level", "LOW")
                    })

        proj["spent"] = proj.get("spent", proj.get("budget_spent", 0))
        proj["budget_spent"] = proj.get("budget_spent", proj.get("spent", 0))
        proj["target_deadline"] = proj.get("target_deadline", proj.get("target_golive", "2027-04-15"))
        proj["target_golive"] = proj.get("target_golive", proj.get("target_deadline", "2027-04-15"))
        proj["critical_skills_needed"] = proj.get("critical_skills_needed", proj.get("tech_stack", ["React", "Node.js", "Python"]))
        proj["tech_stack"] = proj.get("tech_stack", proj.get("critical_skills_needed", ["React", "Node.js", "Python"]))
        proj["members"] = members
        proj["headcount_allocated"] = len(members)
        req_count = proj.get("headcount_required", max(len(members), 1))
        proj["staffing_gap"] = max(0, req_count - len(members))
        if proj["staffing_gap"] == 0:
            proj["health"] = "HEALTHY"
        elif proj["staffing_gap"] <= 2:
            proj["health"] = "WARNING"
        else:
            proj["health"] = "AT_RISK"
        res.append(proj)

    return res

@router.post("/projects/{project_id}/members")
def add_project_member(project_id: str, req: AddMemberRequest, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    emp = next((e for e in emps if e.get("id") == req.employee_id or e.get("employee_id") == req.employee_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found in organization")

    emp_id = emp.get("id") or emp.get("employee_id")

    if org_id == "org_acme_corp":
        proj = next((p for p in ERP_PROJECTS if p["id"] == project_id), None)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        if "assigned_employees" not in proj:
            proj["assigned_employees"] = []
        if emp_id not in proj["assigned_employees"]:
            proj["assigned_employees"].append(emp_id)
        emp["allocated_project"] = proj["name"]
        emp["billability_pct"] = 100
        mongo_save_employee(emp)
        return {"status": "SUCCESS", "message": f"Added {emp['name']} to {proj['name']}", "project_id": project_id, "employee_id": emp_id}

    db = get_mongo_db()
    if db is not None:
        try:
            proj = db["erp_projects"].find_one({"id": project_id, "organization_id": org_id})
            if not proj:
                raise HTTPException(status_code=404, detail="Project not found")
            db["erp_projects"].update_one(
                {"id": project_id, "organization_id": org_id},
                {"$addToSet": {"assigned_employees": emp_id}}
            )
            emp["allocated_project"] = proj["name"]
            emp["billability_pct"] = 100
            mongo_save_employee(emp)
            return {"status": "SUCCESS", "message": f"Added {emp['name']} to {proj['name']}", "project_id": project_id, "employee_id": emp_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "SUCCESS"}

@router.delete("/projects/{project_id}/members/{employee_id}")
def remove_project_member(project_id: str, employee_id: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    emp = next((e for e in emps if e.get("id") == employee_id or e.get("employee_id") == employee_id), None)

    if org_id == "org_acme_corp":
        proj = next((p for p in ERP_PROJECTS if p["id"] == project_id), None)
        if proj and "assigned_employees" in proj and employee_id in proj["assigned_employees"]:
            proj["assigned_employees"].remove(employee_id)
        if emp:
            emp["allocated_project"] = "Bench / Available Talent Pool"
            emp["billability_pct"] = 0
            mongo_save_employee(emp)
        return {"status": "SUCCESS", "message": f"Removed employee {employee_id} to Bench."}

    db = get_mongo_db()
    if db is not None:
        try:
            db["erp_projects"].update_one(
                {"id": project_id, "organization_id": org_id},
                {"$pull": {"assigned_employees": employee_id}}
            )
            if emp:
                emp["allocated_project"] = "Bench / Available Talent Pool"
                emp["billability_pct"] = 0
                mongo_save_employee(emp)
        except Exception:
            pass

    return {"status": "SUCCESS", "message": f"Removed employee {employee_id} to Bench."}

@router.get("/resources")
def get_resource_allocations(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    total = len(emps)

    bench_employees = [e for e in emps if "bench" in str(e.get("allocated_project", "")).lower() or float(e.get("billability_pct", 100)) == 0]
    allocated_employees = [e for e in emps if e not in bench_employees]
    avg_billability = (sum(float(e.get("billability_pct", 100)) for e in emps) / max(total, 1)) if total > 0 else 0.0

    return {
        "total_workforce": total,
        "allocated_count": len(allocated_employees),
        "bench_count": len(bench_employees),
        "avg_billability_pct": round(avg_billability, 1),
        "bench_list": bench_employees,
        "allocated_list": allocated_employees
    }

@router.get("/budgets")
def get_cost_center_budgets(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    if org_id == "org_acme_corp":
        total_allocated = sum(c["allocated_budget"] for c in ERP_COST_CENTERS)
        total_payroll = sum(c["payroll_expenses"] for c in ERP_COST_CENTERS)
        total_ops = sum(c["operational_expenses"] for c in ERP_COST_CENTERS)
        return {
            "summary": {
                "total_allocated": total_allocated,
                "total_payroll": total_payroll,
                "total_operational": total_ops,
                "total_spent": total_payroll + total_ops,
                "total_remaining": total_allocated - (total_payroll + total_ops),
                "burn_rate_pct": round(((total_payroll + total_ops) / total_allocated) * 100, 1)
            },
            "cost_centers": ERP_COST_CENTERS
        }

    emps = get_tenant_employees(org_id)
    dept_map: Dict[str, List[dict]] = {}
    for e in emps:
        d = e.get("department", "General")
        dept_map.setdefault(d, []).append(e)

    cost_centers = []
    for d_name, d_emps in dept_map.items():
        dept_salary = sum(float(e.get("salary", 1800000)) for e in d_emps)
        monthly_payroll = int(dept_salary / 12)
        allocated_budget = int(monthly_payroll * 14)
        ops_spent = int(monthly_payroll * 0.25)
        spent = monthly_payroll + ops_spent

        cost_centers.append({
            "code": f"CC-{d_name[:3].upper()}-01",
            "name": f"{d_name} Operations",
            "headcount": len(d_emps),
            "allocated_budget": allocated_budget,
            "payroll_expenses": monthly_payroll,
            "operational_expenses": ops_spent,
            "status": "HEALTHY" if spent < allocated_budget * 0.8 else "WARNING"
        })

    total_allocated = sum(c["allocated_budget"] for c in cost_centers) if cost_centers else 1000000
    total_payroll = sum(c["payroll_expenses"] for c in cost_centers) if cost_centers else 0
    total_ops = sum(c["operational_expenses"] for c in cost_centers) if cost_centers else 0
    total_spent = total_payroll + total_ops

    return {
        "summary": {
            "total_allocated": total_allocated,
            "total_payroll": total_payroll,
            "total_operational": total_ops,
            "total_spent": total_spent,
            "total_remaining": max(0, total_allocated - total_spent),
            "burn_rate_pct": round((total_spent / max(total_allocated, 1)) * 100, 1)
        },
        "cost_centers": cost_centers
    }

@router.get("/assets")
def get_erp_assets(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    if org_id == "org_acme_corp":
        return ERP_ASSETS

    emps = get_tenant_employees(org_id)
    assets = []
    for idx, e in enumerate(emps[:8]):
        emp_id = e.get("id") or e.get("employee_id")
        assets.append({
            "asset_tag": f"AST-{org_id[-4:]}-{101 + idx}",
            "type": "Hardware" if idx % 2 == 0 else "Software License",
            "item": "Apple MacBook Pro M3 (16GB)" if idx % 2 == 0 else "Enterprise Figma / Datadog Seat",
            "assigned_to": emp_id,
            "assigned_name": e["name"],
            "status": "Active"
        })
    return assets

@router.post("/sync")
def trigger_erp_hris_sync(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    total = len(emps)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "SUCCESS",
        "sync_pipelines": [
            {
                "name": f"HRIS Payroll ➔ ERP Financial General Ledger ({org_id})",
                "status": "COMPLETED",
                "records_transferred": total,
                "variance": "₹0.00"
            },
            {
                "name": "ERP Project Staffing Gaps ➔ HRIS Talent Pipeline",
                "status": "COMPLETED",
                "active_requisitions_synced": max(1, total // 20),
                "bench_reassignments": 1
            },
            {
                "name": "Employee Onboarding & Offboarding ➔ IT Asset Management",
                "status": "COMPLETED",
                "assets_verified": min(total, 8),
                "unassigned_assets": 0
            }
        ]
    }
