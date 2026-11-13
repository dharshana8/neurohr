from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from datetime import datetime
import csv
import io

from app.core.database import (
    EMPLOYEES, 
    build_enterprise_employees,
    mongo_clear_all_employees,
    mongo_seed_employees,
    mongo_save_employee,
    mongo_delete_employee,
    get_tenant_employees,
    mongo_clear_tenant_employees,
    get_mongo_db
)
from app.api.v1.auth import get_current_user
from app.ml.attrition.service import attrition_service

router = APIRouter()

@router.get("/stats")
def get_workforce_stats(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    total = len(emps)
    high_attrition = sum(1 for e in emps if float(e.get("attrition_risk", 0)) >= 0.65 or e.get("risk_level") == "HIGH")
    avg_perf = (sum(float(e.get("performance_score", 0)) for e in emps) / total) if total > 0 else 0.0
    avg_eng = (sum(float(e.get("engagement_score", 0)) for e in emps) / total) if total > 0 else 0.0
    attrition_rate = round((high_attrition / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_employees": total,
        "high_attrition_risk": high_attrition,
        "attrition_rate": attrition_rate,
        "avg_performance": round(avg_perf, 2),
        "avg_engagement": round(avg_eng, 2)
    }

@router.get("/employees")
def list_employees(
    department: Optional[str] = None, 
    risk_level: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    res = []
    for e in emps:
        if department and e.get("department", "").lower() != department.lower():
            continue
        if risk_level and str(e.get("risk_level", "")).upper() != risk_level.upper():
            continue
        emp_dict = dict(e)
        emp_dict["employee_id"] = e.get("employee_id") or e.get("id")
        emp_dict["id"] = e.get("id") or e.get("employee_id")
        emp_dict["employment_status"] = e.get("employment_status") or e.get("status") or "Active"
        emp_dict["status"] = emp_dict["employment_status"]
        emp_dict["currency"] = e.get("currency", "INR")
        res.append(emp_dict)
    return res

@router.get("/employees/{employee_id}")
def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    emps = get_tenant_employees(org_id)
    for e in emps:
        if e.get("id") == employee_id or e.get("employee_id") == employee_id:
            emp_dict = dict(e)
            emp_dict["employee_id"] = e.get("id")
            return emp_dict
    raise HTTPException(status_code=404, detail="Employee not found")

def get_department_skills(department: str, role: str) -> list:
    dept = (department or "").lower()
    r = (role or "").lower()
    if "eng" in dept or "tech" in dept:
        if "ml" in r or "data" in r or "nlp" in r:
            return ["Deep Learning", "PyTorch", "MLOps Pipelines", "Feature Engineering", "Data Modeling", "Algorithm Evaluation"]
        if "cloud" in r or "devops" in r or "sre" in r:
            return ["Cloud Architecture (AWS/GCP)", "Kubernetes Orchestration", "Terraform IaC", "CI/CD Reliability", "System Security", "Incident Response"]
        return ["Distributed Systems", "REST & gRPC APIs", "Microservices Design", "Database Optimization", "High-Concurrency Backend", "Code Refactoring"]
    elif "sales" in dept:
        return ["Enterprise Deal Structuring", "B2B Sales Pipeline", "Contract Negotiations", "Strategic Account Mapping", "Executive Pitching", "Quota Attainment"]
    elif "prod" in dept:
        return ["Product Strategy", "Agile Sprints", "User Journey Mapping", "Backlog Prioritization", "Feature Roadmapping", "Metrics & OKRs"]
    elif "design" in dept:
        return ["Design Systems", "Figma Enterprise", "User Experience (UX) Research", "Interactive Prototyping", "Information Architecture", "Design Tokens"]
    elif "market" in dept:
        return ["Demand Generation", "SEO/SEM Strategy", "Growth Marketing", "Content Positioning", "Attribution Modeling", "Omnichannel Campaigns"]
    elif "op" in dept or "supply" in dept:
        return ["Supply Chain Optimization", "ERP Logistics Flow", "Vendor Contract Management", "Procurement Operations", "Inventory SLA Tracking", "Process Re-engineering"]
    elif "fin" in dept:
        return ["Financial Planning & Analysis (FP&A)", "Corporate Ledger Auditing", "Variance Reconciliation", "Statutory Compliance (TDS/GST)", "Budget Allocation", "Cash Flow Forecasting"]
    elif "hr" in dept:
        return ["Talent Acquisition Strategy", "People Operations", "Workplace Relations", "Compliance & Labor Governance", "Compensation Benchmarking", "Employee Engagement Retention"]
    return ["Cross-Functional Collaboration", "Strategic Execution", "Stakeholder Communication", "Project Governance", "Operational Quality"]

def generate_personalized_ai_insights(emp: dict) -> dict:
    name = emp.get("name", "Employee")
    role = emp.get("role", "Specialist")
    dept = emp.get("department", "General")
    perf = float(emp.get("performance_score", 4.0))
    eng = float(emp.get("engagement_score", 3.5))
    ot = float(emp.get("overtime_hours", 10))
    salary = float(emp.get("salary", 2200000))
    tenure = float(emp.get("tenure_years", 3.0))
    risk_prob = float(emp.get("probability", emp.get("attrition_risk", 0.15)))
    project = emp.get("allocated_project", "Core Enterprise Deliverables")

    strengths = []
    if perf >= 4.5:
        strengths.append(f"Top-tier performance appraisal ({perf:.1f}/5.0): Consistently exceeds departmental deliverable targets in {dept}.")
    elif perf >= 3.8:
        strengths.append(f"Reliable core throughput ({perf:.1f}/5.0): Dependable execution on {project}.")

    if eng >= 4.2:
        strengths.append(f"High cultural engagement ({eng:.1f}/5.0): Acts as an organizational pillar and positive team champion.")
    
    if tenure >= 3.0:
        strengths.append(f"Established institutional tenure ({tenure:.1f} years): Deep historical understanding of cross-team dependencies.")
    else:
        strengths.append(f"High agility ramp-up: Rapidly mastering core workflows across {dept} priorities.")

    if ot <= 10:
        strengths.append(f"Disciplined sprint pacing: Maintains a sustainable work cadence ({int(ot)} hrs overtime/month).")

    if not strengths:
        strengths = [f"Dedicated domain specialist in {role}", "Proactive cross-functional communication", "Strong alignment with company milestones"]

    attention = []
    if ot > 25:
        attention.append(f"Critical Burnout Redline: Logging {int(ot)} hrs/mo overtime on {project}. Sprint fatigue is acute.")
    elif ot > 18:
        attention.append(f"Sprint Creep: Recent overtime ({int(ot)} hrs/mo) is trending above team median.")

    if eng < 2.8:
        attention.append(f"Severe Detachment Alert: Pulse engagement score ({eng:.1f}/5.0) signals elevated risk of early departure.")
    elif eng < 3.4:
        attention.append(f"Sub-optimal Morale ({eng:.1f}/5.0): Room for improving role alignment and motivational support.")

    if salary < 1800000 and tenure > 2.0:
        attention.append(f"Compensation Friction: Current CTC of ₹{salary/100000:.1f} Lakhs is trailing external market offers for {role}.")

    if tenure > 3.0 and emp.get("promotion_history", 0) == 0:
        attention.append(f"Tenure Stagnation: Has spent {tenure:.1f} years at Acme without a major title promotion.")

    if not attention:
        attention = [
            f"Low immediate flight risk ({int(risk_prob*100)}%): Employee is primed for higher project leadership and expanded scope.",
            "Maintain ongoing regular check-ins to safeguard current high retention index."
        ]

    actions = []
    if risk_prob >= 0.65 or ot > 25:
        actions.append(f"Immediate: Authorize 2 days of paid comp-off to alleviate sprint fatigue from {project}.")
        actions.append(f"Workforce Balancing: Reassign secondary backlog tasks to ERP bench pool to reduce monthly overtime below 15h.")
        actions.append(f"Stay Interview: Schedule a private 1:1 retention discussion with {dept} leadership within 48 hours.")
    elif risk_prob >= 0.35 or eng < 3.2:
        actions.append(f"Manager Check-in: Review quarterly project milestones and remove day-to-day delivery friction points.")
        actions.append(f"Recognition: Acknowledge high contribution in upcoming town hall and explore compensation band review.")
    else:
        actions.append(f"Leadership Track: Nominate {name} for advanced architectural / strategic leadership mentoring.")
        actions.append(f"Retention Anchor: Assign as onboarding buddy or mentor for new hires in {dept}.")

    summary_text = (
        f"{name} currently serves as {role} in {dept}, assigned to {project}. "
        f"The predictive ML model computes a {int(risk_prob * 100)}% flight risk ({'HIGH' if risk_prob >= 0.65 else 'MEDIUM' if risk_prob >= 0.35 else 'LOW'} band) "
        f"based on current engagement ({eng:.1f}/5.0), performance ({perf:.1f}/5.0), and {int(ot)} hours/mo sprint overtime."
    )

    return {
        "summary": summary_text,
        "strengths": strengths[:3],
        "key_areas_requiring_attention": attention[:3],
        "recommended_hr_actions": actions[:3]
    }

@router.get("/employees/{employee_id}/360")
def get_employee_360(employee_id: str, current_user: dict = Depends(get_current_user)):
    emp = next((e for e in EMPLOYEES if e.get("id") == employee_id or e.get("employee_id") == employee_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    risk_prob = float(emp.get("probability", emp.get("attrition_risk", 0.15)))
    tenure = float(emp.get("tenure_years", 3.0))
    salary = int(emp.get("salary", 2200000))
    perf = float(emp.get("performance_score", 4.2))
    eng = float(emp.get("engagement_score", 3.8))
    overtime = int(emp.get("overtime_hours", 12))
    dept = emp.get("department", "Engineering")
    role = emp.get("role", "Specialist")

    personalized_ai = generate_personalized_ai_insights(emp)
    skills = get_department_skills(dept, role)

    # Manager feedback tailored to performance & engagement
    if perf >= 4.5 and eng >= 4.0:
        feedback = f"{emp['name']} is an exemplary team pillar in {dept}. Demonstrates exceptional technical throughput, high ownership, and proactive mentorship."
    elif perf >= 4.0 and overtime > 25:
        feedback = f"{emp['name']} delivers high quality deliverables under heavy sprint pressure. However, recent overtime crunch ({overtime}h) is taking a toll on energy levels."
    elif eng < 2.8:
        feedback = f"{emp['name']} possesses strong foundational capability, but recent engagement pulse indicates detachment from team goals. Recommending a constructive 1:1 check-in."
    else:
        feedback = f"{emp['name']} maintains steady, reliable execution across assigned {emp.get('allocated_project', 'deliverables')} with consistent stakeholder communication."

    return {
        "basic_info": {
            "employee_id": emp["id"],
            "name": emp["name"],
            "department": dept,
            "role": role,
            "manager": "Sarah Connor" if emp["id"] != "EMP-101" else "Board of Directors",
            "joining_date": emp.get("joining_date", "2023-01-15"),
            "employment_status": emp.get("status", "Active")
        },
        "professional_info": {
            "experience": round(tenure, 1),
            "skills": skills,
            "performance_score": perf,
            "engagement_score": eng,
            "overtime": overtime,
            "promotion_history": 1 if tenure > 3.0 else 0,
            "manager_feedback": feedback
        },
        "compensation": {
            "accessible": True,
            "salary": salary,
            "currency": "INR",
            "message": None
        },
        "attrition": {
            "is_available": True,
            "estimated_attrition_risk": risk_prob,
            "risk_band": emp.get("risk_level", "HIGH" if risk_prob >= 0.65 else "MEDIUM" if risk_prob >= 0.35 else "LOW"),
            "prediction_timestamp": datetime.utcnow().isoformat(),
            "model_version": "RandomForest-v2.4",
            "explanation_factors": [
                {"factor": "Sprint Overtime Crunch", "weight": f"+{round(overtime*0.012, 2)}" if overtime > 20 else "-0.15"},
                {"factor": "Engagement Survey Score", "weight": f"-{round((5.0-eng)*0.15, 2)}" if eng < 3.0 else "+0.22"},
                {"factor": "Market Compensation Alignment", "weight": "-0.20" if salary >= 2200000 else "+0.25"}
            ],
            "message": None
        },
        "sentiment": {
            "accessible": True,
            "is_available": True,
            "recent_sentiment": "POSITIVE" if eng >= 3.5 else "CONCERNED",
            "sentiment_scores": {"positive": 0.74 if eng >= 3.5 else 0.25, "neutral": 0.18, "negative": 0.08 if eng >= 3.5 else 0.57},
            "feedback_count": 5,
            "themes": [f"{dept} Quality", "Team Culture", "Work-Life Balance"],
            "trend": "STABLE" if eng >= 3.5 else "DECLINING",
            "message": None
        },
        "ai_insights": {
            "is_available": True,
            "summary": personalized_ai["summary"],
            "strengths": personalized_ai["strengths"],
            "key_areas_requiring_attention": personalized_ai["key_areas_requiring_attention"],
            "recommended_hr_actions": personalized_ai["recommended_hr_actions"],
            "generated_at": datetime.utcnow().isoformat()
        }
    }

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    global EMPLOYEES
    initial_len = len(EMPLOYEES)
    EMPLOYEES = [e for e in EMPLOYEES if e.get("id") != employee_id and e.get("employee_id") != employee_id]
    if len(EMPLOYEES) == initial_len:
        raise HTTPException(status_code=404, detail="Employee not found")
    mongo_delete_employee(employee_id)
    return {"message": f"Employee {employee_id} deleted successfully."}

@router.delete("/clear-data")
def clear_workforce_data(current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    if org_id == "org_acme_corp":
        global EMPLOYEES
        EMPLOYEES = []
    mongo_clear_tenant_employees(org_id)
    db = get_mongo_db()
    if db is not None:
        try:
            db["organizations"].update_one({"id": org_id}, {"$set": {"employee_count": 0}})
        except Exception:
            pass
    return {"message": f"Workforce records for tenant '{org_id}' cleared successfully. Ready for fresh CSV upload."}

@router.post("/seed-defaults")
def seed_default_workforce(current_user: dict = Depends(get_current_user)):
    global EMPLOYEES
    EMPLOYEES.clear()
    EMPLOYEES.extend(build_enterprise_employees())
    mongo_seed_employees(EMPLOYEES)
    return {"message": f"Successfully loaded {len(EMPLOYEES)} realistic enterprise workforce records.", "total": len(EMPLOYEES)}

@router.post("/import")
async def import_workforce_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    org_id = current_user.get("organization_id", "org_acme_corp")
    contents = await file.read()
    try:
        decoded = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = contents.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    imported_count = 0
    high_count = 0
    db = get_mongo_db()

    for idx, raw_row in enumerate(reader):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        
        name = row.get("name") or row.get("employeename") or row.get("emp_name") or f"Employee {imported_count + 1}"
        dept = row.get("department") or row.get("dept") or "Engineering"
        role = row.get("role") or row.get("jobrole") or row.get("title") or "Specialist"
        emp_id = row.get("employeeid") or row.get("empid") or row.get("id") or f"EMP-{org_id[-4:]}-{101 + imported_count}"

        try:
            salary = float(row.get("salary") or row.get("monthlyincome") or row.get("ctc") or 1800000)
            if salary < 200000:
                salary = salary * 12.0
        except (ValueError, TypeError):
            salary = 1800000.0

        try:
            perf = float(row.get("performancescore") or row.get("performancerating") or row.get("performance") or 4.0)
        except (ValueError, TypeError):
            perf = 4.0

        try:
            eng = float(row.get("engagementscore") or row.get("jobsatisfaction") or row.get("engagement") or 3.5)
        except (ValueError, TypeError):
            eng = 3.5

        try:
            ot_raw = row.get("overtimehours") or row.get("overtime_hours") or row.get("overtime")
            if str(ot_raw).lower() in ["yes", "y", "true", "1"]:
                overtime = 25.0
            elif str(ot_raw).lower() in ["no", "n", "false", "0"]:
                overtime = 5.0
            else:
                overtime = float(ot_raw or 10.0)
        except (ValueError, TypeError):
            overtime = 10.0

        try:
            tenure = float(row.get("tenure") or row.get("yearsatcompany") or row.get("tenure_years") or 3.0)
        except (ValueError, TypeError):
            tenure = 3.0

        pred = attrition_service.predict_risk(
            salary=salary,
            tenure_years=tenure,
            performance=perf,
            engagement=eng,
            overtime_hours=overtime
        )

        prob = pred["attrition_probability"]
        level = pred["risk_level"]
        if level == "HIGH" or prob >= 0.65:
            high_count += 1

        emp_record = {
            "id": emp_id,
            "employee_id": emp_id,
            "organization_id": org_id,
            "name": name,
            "email": row.get("email") or f"{name.lower().replace(' ', '.')}@{org_id}.com",
            "department": dept,
            "role": role,
            "salary": salary,
            "currency": "INR",
            "tenure_years": tenure,
            "performance_score": perf,
            "engagement_score": eng,
            "overtime_hours": overtime,
            "attrition_risk": round(prob, 2),
            "probability": round(prob, 2),
            "risk_level": level,
            "primary_driver": pred["top_drivers"][0] if pred["top_drivers"] else "Compensation & Workload",
            "top_drivers": pred["top_drivers"],
            "status": "Active",
            "employment_status": "Active",
            "allocated_project": row.get("project") or "Core Deliverables",
            "billability_pct": float(row.get("billability") or 100),
            "leave_balance": {"casual": 8, "sick": 10, "earned": max(4, int(tenure * 4))}
        }

        mongo_save_employee(emp_record)
        if org_id == "org_acme_corp":
            EMPLOYEES.append(emp_record)
        imported_count += 1

    if db is not None:
        try:
            count = db["employees"].count_documents({"organization_id": org_id})
            db["organizations"].update_one(
                {"id": org_id},
                {"$set": {"employee_count": count}}
            )
        except Exception:
            pass

    attr_rate = round((high_count / max(imported_count, 1)) * 100, 1)
    return {
        "status": "SUCCESS",
        "total_rows": imported_count,
        "valid_rows": imported_count,
        "imported_rows": imported_count,
        "high_risk_count": high_count,
        "attrition_rate": attr_rate,
        "message": f"Successfully parsed and predicted attrition for {imported_count} employee records. Found {high_count} high-risk employees ({attr_rate}% attrition rate)."
    }
