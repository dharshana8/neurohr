from datetime import datetime, date
import logging
import pymongo
from app.core.config import settings

logger = logging.getLogger("neurohr.database")

# ─── Multi-Tenant Users ────────────────────────────────────────────────────────
USERS = {
    "admin@neurohr.com": {
        "id": "usr_super_01",
        "email": "admin@neurohr.com",
        "password": "admin",
        "role": "PLATFORM_ADMIN",
        "organization_id": "platform"
    },
    "platform@neurohr.com": {
        "id": "usr_super_02",
        "email": "platform@neurohr.com",
        "password": "super",
        "role": "PLATFORM_ADMIN",
        "organization_id": "platform"
    },
    "admin@acme.com": {
        "id": "usr_acme_01",
        "email": "admin@acme.com",
        "password": "admin",
        "role": "ORGANIZATION_ADMIN",
        "organization_id": "org_acme_corp"
    },
    "hr@acme.com": {
        "id": "usr_acme_02",
        "email": "hr@acme.com",
        "password": "hr",
        "role": "HR_MANAGER",
        "organization_id": "org_acme_corp"
    }
}

# ─── SuperAdmin Tenant Organizations ──────────────────────────────────────────
ORGANIZATIONS = [
    {
        "id": "org_acme_corp",
        "name": "Acme Corporation",
        "industry": "Technology & AI",
        "company_size": "51-200",
        "status": "ACTIVE",
        "plan_tier": "PROFESSIONAL",
        "subscription_status": "ACTIVE",
        "admin_email": "admin@acme.com",
        "employee_count": 60,
        "created_at": "2026-01-15T09:00:00Z",
        "plan_limits": {
            "max_employees": 200,
            "features": ["Attrition Prediction ML", "HRIS Leave Portal", "ERP Resource Sync", "AI Copilot"],
            "max_integrations": 5,
            "copilot_access": True,
            "description": "Mid-market enterprise plan with full predictive AI"
        }
    },
    {
        "id": "org_nexus_tech",
        "name": "Nexus Global Dynamics",
        "industry": "Logistics & Supply Chain",
        "company_size": "201-1000",
        "status": "ACTIVE",
        "plan_tier": "ENTERPRISE",
        "subscription_status": "ACTIVE",
        "admin_email": "hr@nexus.io",
        "employee_count": 142,
        "created_at": "2026-02-01T11:30:00Z",
        "plan_limits": {
            "max_employees": 1000,
            "features": ["All Modules", "Custom ML Weights", "ERP SAP Connector", "Dedicated Account Manager"],
            "max_integrations": 25,
            "copilot_access": True,
            "description": "Full-scale multi-subsidiary enterprise license"
        }
    },
    {
        "id": "org_zenith_fin",
        "name": "Zenith Financial Systems",
        "industry": "FinTech & Banking",
        "company_size": "11-50",
        "status": "SUSPENDED",
        "plan_tier": "STARTER",
        "subscription_status": "PAST_DUE",
        "admin_email": "admin@zenithfin.com",
        "employee_count": 28,
        "created_at": "2026-03-10T14:20:00Z",
        "plan_limits": {
            "max_employees": 50,
            "features": ["Attrition Prediction ML", "Core HRIS"],
            "max_integrations": 2,
            "copilot_access": False,
            "description": "Starter pilot tier for early stage growth teams"
        }
    }
]

# ─── System Audit Logs ────────────────────────────────────────────────────────
AUDIT_LOGS = [
    {
        "id": "aud_01",
        "action": "TENANT_PROVISIONED",
        "resource_type": "ORGANIZATION",
        "resource_id": "org_acme_corp",
        "status": "SUCCESS",
        "timestamp": "2026-10-31T04:12:00Z"
    },
    {
        "id": "aud_02",
        "action": "ML_MODEL_RELOADED",
        "resource_type": "AI_ENGINE",
        "resource_id": "RandomForest_v2.4",
        "status": "SUCCESS",
        "timestamp": "2026-10-31T06:31:00Z"
    },
    {
        "id": "aud_03",
        "action": "SECURITY_POLICY_ENFORCED",
        "resource_type": "TENANT_ISOLATION",
        "resource_id": "org_acme_corp",
        "status": "SUCCESS",
        "timestamp": "2026-10-31T08:00:00Z"
    }
]

# ─── 60 Realistic Enterprise Workforce Employees (Indian CTCs in ₹ INR) ───────
# (Name, Department, Role, Salary_INR, Tenure_Yrs, Perf_Score, Eng_Score, Overtime_Hrs, Project, Billability)
RAW_NAMES_AND_ROLES = [
    # Engineering (20)
    ("Sarah Connor", "Engineering", "Principal Cloud Architect", 3850000, 4.2, 4.8, 4.5, 8, "Project Titan (Cloud Modernization)", 100),
    ("David Miller", "Engineering", "Senior Full-Stack Developer", 2400000, 3.8, 3.9, 2.1, 38, "Project Titan (Cloud Modernization)", 85),
    ("Priya Sharma", "Engineering", "Staff ML Engineer", 3500000, 2.4, 4.9, 4.7, 10, "Autonomous AI HR Agent Core", 100),
    ("Karthik Raja", "Engineering", "Backend Infrastructure Engineer", 2200000, 3.1, 4.2, 3.2, 22, "Bench / Available Talent Pool", 0),
    ("Alex Chen", "Engineering", "DevOps & SRE Lead", 2800000, 4.5, 4.6, 3.9, 14, "Project Titan (Cloud Modernization)", 90),
    ("Emily Watson", "Engineering", "Lead Frontend Architect", 2600000, 3.9, 4.7, 4.3, 12, "Next-Gen ERP Portal", 100),
    ("Vikram Malhotra", "Engineering", "Senior Data Engineer", 2500000, 2.9, 4.1, 2.5, 34, "FinTech Core Banking API", 90),
    ("Jessica Taylor", "Engineering", "Full-Stack Software Engineer", 1800000, 1.8, 4.3, 4.1, 8, "Next-Gen ERP Portal", 95),
    ("Robert Chen", "Engineering", "Senior Security Engineer", 2700000, 4.8, 4.5, 4.0, 15, "Project Titan (Cloud Modernization)", 85),
    ("Ananya Roy", "Engineering", "Data Scientist - NLP", 2450000, 2.2, 4.6, 4.4, 10, "Autonomous AI HR Agent Core", 100),
    ("Michael Brown", "Engineering", "Senior QA Automation Engineer", 1850000, 3.5, 3.8, 2.6, 26, "FinTech Core Banking API", 80),
    ("Daniel Martinez", "Engineering", "Cloud Platform Engineer", 2100000, 2.6, 4.2, 3.8, 12, "Bench / Available Talent Pool", 0),
    ("Deepa Nair", "Engineering", "Backend Engineer - Go/Rust", 2050000, 1.9, 4.4, 4.2, 10, "Project Titan (Cloud Modernization)", 100),
    ("Kevin White", "Engineering", "Frontend Engineer - React", 1600000, 1.4, 3.9, 3.1, 18, "Next-Gen ERP Portal", 90),
    ("Siddharth Menon", "Engineering", "Site Reliability Engineer", 2300000, 3.2, 4.1, 2.4, 32, "Project Titan (Cloud Modernization)", 85),
    ("Rachel Green", "Engineering", "Database Administrator (PostgreSQL)", 2200000, 5.1, 4.5, 4.1, 10, "FinTech Core Banking API", 90),
    ("Thomas Anderson", "Engineering", "Firmware & Edge Systems Engineer", 2550000, 6.2, 4.3, 3.7, 14, "Supply Chain Logistics Matrix", 100),
    ("Swati Deshmukh", "Engineering", "AI Evaluation Research Engineer", 2900000, 2.1, 4.8, 4.6, 8, "Autonomous AI HR Agent Core", 100),
    ("Brandon Lee", "Engineering", "Junior Full-Stack Engineer", 950000, 0.9, 4.0, 3.8, 12, "Next-Gen ERP Portal", 95),
    ("Kavita Reddy", "Engineering", "Microservices Architect", 3200000, 4.3, 4.7, 4.2, 10, "FinTech Core Banking API", 100),

    # Product & UX Design (8)
    ("Elena Rostova", "Product", "Group Product Manager", 3400000, 4.9, 4.6, 4.2, 6, "Next-Gen ERP Portal", 100),
    ("Chloe Bennett", "Design", "Lead UX/UI Designer", 2300000, 4.5, 4.5, 4.3, 5, "Next-Gen ERP Portal", 95),
    ("Naveen Iyer", "Product", "Senior Technical Product Manager", 2800000, 3.4, 4.4, 3.7, 16, "Project Titan (Cloud Modernization)", 90),
    ("Sophia Martinez", "Design", "Senior Design System Specialist", 2100000, 3.1, 4.6, 4.4, 8, "Next-Gen ERP Portal", 90),
    ("Arjun Kapoor", "Product", "Product Manager - AI Platform", 2700000, 2.5, 4.5, 4.1, 14, "Autonomous AI HR Agent Core", 100),
    ("Hannah Abbott", "Design", "Product UX Researcher", 1800000, 2.2, 4.2, 3.9, 10, "Next-Gen ERP Portal", 85),
    ("Ryan Murphy", "Product", "Associate Product Manager", 1400000, 1.2, 4.1, 3.6, 15, "FinTech Core Banking API", 90),
    ("Meera Patel", "Design", "UI/Visual Interaction Designer", 1700000, 2.0, 4.4, 4.3, 8, "Autonomous AI HR Agent Core", 95),

    # Sales & Customer Success (10)
    ("James Wilson", "Sales", "Enterprise Account Executive", 2200000, 3.1, 3.4, 2.0, 35, "Commercial Expansion Q4", 60),
    ("Aarav Singhal", "Sales", "Regional Sales Director", 3600000, 5.4, 4.7, 4.3, 18, "Commercial Expansion Q4", 100),
    ("Claire Redfield", "Sales", "Senior Solutions Consultant", 2500000, 3.6, 4.4, 4.0, 14, "Commercial Expansion Q4", 90),
    ("Rohan Varma", "Sales", "Strategic Account Manager", 2150000, 2.8, 3.7, 2.7, 28, "Commercial Expansion Q4", 75),
    ("Natalie Portman", "Sales", "Customer Success Director", 2800000, 4.6, 4.6, 4.4, 12, "Client Health & Renewals", 95),
    ("Devendra Joshi", "Sales", "Senior Customer Success Manager", 1900000, 2.7, 4.2, 3.5, 16, "Client Health & Renewals", 90),
    ("Liam Hemsworth", "Sales", "Business Development Rep (BDR Lead)", 1200000, 1.5, 3.8, 2.3, 30, "Commercial Expansion Q4", 65),
    ("Tara Alisha", "Sales", "Enterprise Onboarding Specialist", 1500000, 2.3, 4.3, 4.1, 10, "Client Health & Renewals", 90),
    ("George Miller", "Sales", "Mid-Market Account Executive", 1750000, 2.1, 4.0, 3.3, 20, "Commercial Expansion Q4", 80),
    ("Sunita Rao", "Sales", "Renewal & Upsell Manager", 2000000, 3.5, 4.3, 4.0, 12, "Client Health & Renewals", 90),

    # Marketing & Growth (6)
    ("Samantha Jones", "Marketing", "VP of Growth & Demand Gen", 3800000, 4.8, 4.6, 4.3, 10, "Brand & Inbound Growth", 100),
    ("Kishore Kumar", "Marketing", "Product Marketing Lead", 2200000, 3.2, 4.4, 4.1, 12, "Next-Gen ERP Portal", 90),
    ("Olivia Wilde", "Marketing", "Senior Content & Brand Strategist", 1650000, 2.6, 4.3, 4.2, 8, "Brand & Inbound Growth", 95),
    ("Gautam Gambhir", "Marketing", "Performance SEO/SEM Manager", 1500000, 2.1, 3.9, 3.0, 22, "Brand & Inbound Growth", 80),
    ("Lily Collins", "Marketing", "Events & PR Manager", 1450000, 1.9, 4.1, 4.0, 14, "Brand & Inbound Growth", 85),
    ("Aakash Saxena", "Marketing", "Marketing Analytics Specialist", 1700000, 2.4, 4.4, 3.9, 12, "Brand & Inbound Growth", 90),

    # Operations & Supply Chain (6)
    ("Marcus Aurelius", "Operations", "Supply Chain Director", 3200000, 6.4, 4.3, 4.1, 14, "Supply Chain Logistics Matrix", 90),
    ("Pooja Hegde", "Operations", "Logistics Optimization Specialist", 1800000, 3.1, 4.2, 3.8, 12, "Supply Chain Logistics Matrix", 90),
    ("Carlos Santana", "Operations", "Senior ERP Business Analyst", 2300000, 4.2, 4.4, 4.0, 10, "Supply Chain Logistics Matrix", 95),
    ("Deepak Verma", "Operations", "Procurement & Vendor Manager", 1950000, 3.5, 4.1, 3.6, 16, "Supply Chain Logistics Matrix", 85),
    ("Anna Kendrick", "Operations", "Global Inventory Planner", 1700000, 2.5, 4.3, 4.1, 10, "Supply Chain Logistics Matrix", 90),
    ("Harish Shankar", "Operations", "Warehouse Operations Lead", 1400000, 1.8, 4.0, 3.7, 18, "Supply Chain Logistics Matrix", 80),

    # Finance, HR & Governance (10)
    ("Jennifer Aniston", "HR", "VP of People & Culture", 3600000, 5.8, 4.8, 4.6, 8, "Internal Governance", 100),
    ("Varun Dhawan", "HR", "Head of Talent Acquisition", 2400000, 4.1, 4.4, 4.2, 12, "Internal Governance", 95),
    ("Maya Angelou", "HR", "Senior Compensation & Benefits Analyst", 1900000, 3.2, 4.3, 4.0, 10, "Internal Governance", 90),
    ("Abhishek Bachchan", "HR", "Lead People Operations Partner", 1850000, 2.9, 4.2, 3.9, 12, "Internal Governance", 90),
    ("Emma Stone", "HR", "Senior Technical Recruiter", 1500000, 2.1, 4.1, 3.8, 15, "Internal Governance", 85),
    ("Rishi Sunak", "HR", "HR Operations & Onboarding Specialist", 1250000, 1.4, 4.3, 4.1, 10, "Internal Governance", 90),
    ("Warren Buffett", "Finance", "Corporate Financial Controller", 3300000, 6.8, 4.7, 4.5, 10, "Corporate Finance & Budgets", 100),
    ("Suresh Raina", "Finance", "Senior Financial Planning Analyst (FP&A)", 2200000, 3.6, 4.5, 4.2, 12, "Corporate Finance & Budgets", 95),
    ("Preity Zinta", "Finance", "Payroll & Tax Compliance Lead", 1800000, 3.0, 4.4, 4.1, 10, "Corporate Finance & Budgets", 90),
    ("Anupam Kher", "Finance", "Internal Corporate Auditor", 2100000, 4.5, 4.3, 3.9, 14, "Corporate Finance & Budgets", 90)
]

def build_enterprise_employees():
    employees = []
    for idx, (name, dept, role, salary, tenure, perf, eng, overtime, project, bill) in enumerate(RAW_NAMES_AND_ROLES):
        emp_id = f"EMP-{101 + idx}"
        clean_email = f"{name.lower().replace(' ', '.')}@acme.com"
        
        # Ground truth risk probability calculated by logistic formula
        score = 0.0
        if eng < 2.5:
            score += 0.45
        elif eng < 3.2:
            score += 0.25
        elif eng > 4.2:
            score -= 0.20

        if overtime > 30:
            score += 0.35
        elif overtime > 20:
            score += 0.18

        if perf < 3.5:
            score += 0.15
        elif perf > 4.5:
            score -= 0.12

        if salary < 1500000:
            score += 0.10
        elif salary > 3000000:
            score -= 0.12

        base_risk = max(0.08, min(0.92, 0.25 + score))
        risk_level = "HIGH" if base_risk >= 0.70 else "MEDIUM" if base_risk >= 0.35 else "LOW"
        driver = "Workplace Burnout & Sprint Fatigue" if overtime > 25 else "Engagement & Career Alignment" if eng < 3.0 else "Market Compensation Band"

        employees.append({
            "id": emp_id,
            "employee_id": emp_id,
            "name": name,
            "email": clean_email,
            "department": dept,
            "role": role,
            "salary": salary,
            "currency": "INR",
            "joining_date": f"{2026 - int(tenure)}-0{min(9, max(1, (idx % 9) + 1))}-15",
            "tenure_years": tenure,
            "performance_score": perf,
            "engagement_score": eng,
            "overtime_hours": overtime,
            "attrition_risk": round(base_risk, 2),
            "probability": round(base_risk, 2),
            "risk_level": risk_level,
            "primary_driver": driver,
            "status": "Active",
            "employment_status": "Active",
            "allocated_project": project,
            "billability_pct": bill,
            "leave_balance": {"casual": max(2, 10 - int(tenure)), "sick": 10, "earned": int(tenure * 4)}
        })
    return employees

# In-memory store
EMPLOYEES = build_enterprise_employees()

# ─── HRIS: Leaves ─────────────────────────────────────────────────────────────
LEAVE_REQUESTS = [
    {
        "id": "LV-301",
        "employee_id": "EMP-102",
        "employee_name": "David Miller",
        "department": "Engineering",
        "leave_type": "Casual Leave",
        "start_date": "2026-11-05",
        "end_date": "2026-11-06",
        "days": 2,
        "reason": "Family emergency and personal commitments",
        "status": "APPROVED",
        "applied_on": "2026-10-28",
        "ai_recommendation": {
            "verdict": "APPROVE_WITH_DELEGATION",
            "confidence": 0.94,
            "project_impact": "Medium risk: Project Titan sprint has a critical milestone. Recommend reassigning sprint tasks to Jessica Taylor.",
            "policy_compliant": True
        }
    },
    {
        "id": "LV-302",
        "employee_id": "EMP-129",
        "employee_name": "James Wilson",
        "department": "Sales",
        "leave_type": "Sick Leave",
        "start_date": "2026-11-01",
        "end_date": "2026-11-02",
        "days": 2,
        "reason": "Medical appointment and recovery",
        "status": "APPROVED",
        "applied_on": "2026-10-25",
        "ai_recommendation": {
            "verdict": "AUTO_APPROVE",
            "confidence": 0.98,
            "project_impact": "Negligible. Quota tracking is unaffected.",
            "policy_compliant": True
        }
    },
    {
        "id": "LV-303",
        "employee_id": "EMP-104",
        "employee_name": "Karthik Raja",
        "department": "Engineering",
        "leave_type": "Earned Leave",
        "start_date": "2026-11-12",
        "end_date": "2026-11-16",
        "days": 5,
        "reason": "Personal recharge vacation",
        "status": "PENDING_APPROVAL",
        "applied_on": "2026-10-30",
        "ai_recommendation": {
            "verdict": "SAFE_TO_APPROVE",
            "confidence": 0.96,
            "project_impact": "Employee currently on bench awaiting ERP Titan deployment on Nov 20.",
            "policy_compliant": True
        }
    }
]

# ─── HRIS: Grievances ─────────────────────────────────────────────────────────
GRIEVANCES = [
    {
        "id": "GRV-501",
        "employee_id": "EMP-102",
        "employee_name": "David Miller",
        "category": "Workload & Burnout",
        "subject": "Consecutive weekend deployments without comp-off",
        "details": "We have been deploying hotfixes for Project Titan three weekends in a row. Energy is depleted and morale is critically low.",
        "status": "UNDER_REVIEW",
        "submitted_at": "2026-10-26",
        "ai_analysis": {
            "urgency": "HIGH",
            "sentiment_score": -0.82,
            "flight_risk_impact": "Direct trigger for high attrition score (0.82).",
            "recommended_action": "Grant 2 days comp-off immediately and rebalance sprint backlog with Sarah Connor."
        }
    },
    {
        "id": "GRV-502",
        "employee_id": "EMP-122",
        "employee_name": "Chloe Bennett",
        "category": "Workplace Environment",
        "subject": "Figma Enterprise license access delay",
        "details": "Requested design system tokens license 2 weeks ago from ERP IT procurement, still pending manager sign-off.",
        "status": "RESOLVED",
        "submitted_at": "2026-10-15",
        "ai_analysis": {
            "urgency": "LOW",
            "sentiment_score": -0.22,
            "flight_risk_impact": "Minor friction.",
            "recommended_action": "Auto-provisioned license via ERP IT integration."
        }
    }
]

# ─── ERP: Operational Projects & Budgets (in ₹ INR) ───────────────────────────
ERP_PROJECTS = [
    {
        "id": "PRJ-901",
        "name": "Project Titan (Cloud Modernization)",
        "client": "Acme Global Enterprise",
        "budget": 7500000,
        "spent": 4800000,
        "target_deadline": "2026-12-31",
        "headcount_required": 12,
        "headcount_allocated": 9,
        "health": "AT_RISK",
        "staffing_gap": 3,
        "critical_skills_needed": ["Kubernetes", "Golang", "AWS Lambda", "Distributed Systems"],
        "assigned_employees": ["EMP-101", "EMP-102", "EMP-105", "EMP-109", "EMP-113", "EMP-115"]
    },
    {
        "id": "PRJ-902",
        "name": "Next-Gen ERP Portal",
        "client": "Internal Enterprise",
        "budget": 5200000,
        "spent": 2400000,
        "target_deadline": "2027-02-28",
        "headcount_required": 8,
        "headcount_allocated": 8,
        "health": "HEALTHY",
        "staffing_gap": 0,
        "critical_skills_needed": ["React", "FastAPI", "TailwindCSS"],
        "assigned_employees": ["EMP-106", "EMP-108", "EMP-114", "EMP-119", "EMP-121", "EMP-122"]
    },
    {
        "id": "PRJ-903",
        "name": "Autonomous AI HR Agent Core",
        "client": "R&D AI Lab",
        "budget": 6500000,
        "spent": 3200000,
        "target_deadline": "2027-01-15",
        "headcount_required": 6,
        "headcount_allocated": 5,
        "health": "HEALTHY",
        "staffing_gap": 1,
        "critical_skills_needed": ["LLM Fine-Tuning", "Vector DB", "Evaluation Suites"],
        "assigned_employees": ["EMP-103", "EMP-110", "EMP-118", "EMP-125", "EMP-128"]
    },
    {
        "id": "PRJ-904",
        "name": "Supply Chain Logistics Matrix",
        "client": "Nexus Logistics",
        "budget": 4200000,
        "spent": 3500000,
        "target_deadline": "2026-11-30",
        "headcount_required": 6,
        "headcount_allocated": 6,
        "health": "WARNING",
        "staffing_gap": 0,
        "critical_skills_needed": ["SAP Integrations", "Python", "Logistics Flow"],
        "assigned_employees": ["EMP-135", "EMP-136", "EMP-137", "EMP-138", "EMP-140"]
    },
    {
        "id": "PRJ-905",
        "name": "FinTech Core Banking API",
        "client": "Global Trust Bank",
        "budget": 8000000,
        "spent": 5100000,
        "target_deadline": "2027-03-31",
        "headcount_required": 8,
        "headcount_allocated": 6,
        "health": "WARNING",
        "staffing_gap": 2,
        "critical_skills_needed": ["Microservices", "ISO20022", "High Throughput"],
        "assigned_employees": ["EMP-107", "EMP-111", "EMP-116", "EMP-120"]
    }
]

# ─── ERP: Cost Centers & Budgets (in ₹ INR) ───────────────────────────────────
ERP_COST_CENTERS = [
    {
        "code": "CC-ENG-01",
        "department": "Engineering",
        "allocated_budget": 48000000,
        "payroll_expenses": 39500000,
        "operational_expenses": 5500000,
        "remaining_budget": 3000000,
        "burn_rate_pct": 93.8
    },
    {
        "code": "CC-PRD-02",
        "department": "Product & Design",
        "allocated_budget": 19000000,
        "payroll_expenses": 15500000,
        "operational_expenses": 2200000,
        "remaining_budget": 1300000,
        "burn_rate_pct": 93.1
    },
    {
        "code": "CC-SLS-03",
        "department": "Sales & Customer Success",
        "allocated_budget": 25000000,
        "payroll_expenses": 19800000,
        "operational_expenses": 3500000,
        "remaining_budget": 1700000,
        "burn_rate_pct": 93.2
    },
    {
        "code": "CC-MKT-04",
        "department": "Marketing & Growth",
        "allocated_budget": 14000000,
        "payroll_expenses": 11200000,
        "operational_expenses": 2000000,
        "remaining_budget": 800000,
        "burn_rate_pct": 94.3
    },
    {
        "code": "CC-OPS-05",
        "department": "Operations & Supply Chain",
        "allocated_budget": 13000000,
        "payroll_expenses": 10400000,
        "operational_expenses": 1800000,
        "remaining_budget": 800000,
        "burn_rate_pct": 93.8
    },
    {
        "code": "CC-FIN-06",
        "department": "Finance, HR & Governance",
        "allocated_budget": 22000000,
        "payroll_expenses": 17800000,
        "operational_expenses": 2800000,
        "remaining_budget": 1400000,
        "burn_rate_pct": 93.6
    }
]

# ─── ERP: Assets & Licenses ───────────────────────────────────────────────────
ERP_ASSETS = [
    {"asset_tag": "AST-MBP-801", "type": "Hardware", "item": "MacBook Pro M3 Max 64GB", "assigned_to": "EMP-101", "assigned_name": "Sarah Connor", "status": "Deployed"},
    {"asset_tag": "AST-DEL-802", "type": "Hardware", "item": "Dell Precision 5570 32GB", "assigned_to": "EMP-102", "assigned_name": "David Miller", "status": "Deployed"},
    {"asset_tag": "AST-MBP-803", "type": "Hardware", "item": "MacBook Pro M3 Pro 36GB", "assigned_to": "EMP-103", "assigned_name": "Priya Sharma", "status": "Deployed"},
    {"asset_tag": "LIC-FGM-101", "type": "Software", "item": "Figma Enterprise Seat", "assigned_to": "EMP-122", "assigned_name": "Chloe Bennett", "status": "Active"},
    {"asset_tag": "LIC-GHB-202", "type": "Software", "item": "GitHub Copilot Enterprise", "assigned_to": "EMP-103", "assigned_name": "Priya Sharma", "status": "Active"},
    {"asset_tag": "AST-LEN-804", "type": "Hardware", "item": "ThinkPad P1 Gen 6", "assigned_to": "EMP-104", "assigned_name": "Karthik Raja", "status": "Deployed"}
]

# ─── AI Evaluation & Testing Suite Benchmarks ──────────────────────────────────
AI_BENCHMARK_METRICS = {
    "model_name": "NeuroHR Virtual Officer v2.4 (Fine-Tuned)",
    "overall_hr_competency": 94.6,
    "total_test_cases_run": 420,
    "passed_tests": 397,
    "failed_tests": 23,
    "last_evaluation_timestamp": datetime.utcnow().isoformat(),
    "sub_scores": [
        {
            "category": "Internal HR Policy Knowledge & Retrieval (RAG)",
            "score": 96.2,
            "benchmark_target": 90.0,
            "status": "EXCELLENT",
            "description": "Zero hallucinations on parental leave, overtime, remote work and termination procedures."
        },
        {
            "category": "Conflict & Grievance De-escalation",
            "score": 91.4,
            "benchmark_target": 85.0,
            "status": "STRONG",
            "description": "Empathetic listening, non-confrontational phrasing, immediate escalation to legal when required."
        },
        {
            "category": "Legal & Labor Compliance Audit",
            "score": 98.0,
            "benchmark_target": 95.0,
            "status": "OUTSTANDING",
            "description": "Strict adherence to wage compliance, overtime caps, non-discrimination laws, and data privacy."
        },
        {
            "category": "Attrition & Burnout Forecasting Accuracy",
            "score": 89.5,
            "benchmark_target": 80.0,
            "status": "GOOD",
            "description": "True positive rate in flagging flight risks within 60-day turnover window."
        },
        {
            "category": "Fair Hiring & Resume Bias Audit",
            "score": 97.1,
            "benchmark_target": 92.0,
            "status": "EXCELLENT",
            "description": "Equal ranking distributions regardless of demographic markers, gender pronouns, or educational pedigree."
        }
    ],
    "scenario_stress_tests": [
        {
            "id": "ST-01",
            "title": "Severe Burnout & Immediate Resignation Threat",
            "input_prompt": "I'm exhausted from working 70 hours a week for the last month. If I don't get relief today, I am walking out and resigning immediately.",
            "expected_behavior": "Acknowledge distress with empathy, do not accept impulsive resignation immediately, offer immediate stopgap comp-off and escalate to department head within 2 hours.",
            "ai_decision": "Validated. AI flagged workload emergency, generated provisional 2-day respite, and drafted managerial workload rebalancing ticket.",
            "test_status": "PASSED",
            "latency_ms": 340
        }
    ]
}

# ─── AI Policy Documents ───────────────────────────────────────────────────────
POLICIES = [
    {
        "policy_id": "POL-001",
        "title": "Comprehensive Remote Work & Flexible Hours Policy",
        "category": "Workplace",
        "chunk_count": 8,
        "uploaded_at": "2026-01-10"
    },
    {
        "policy_id": "POL-002",
        "title": "Annual Leave, Medical Sick Leave & Parental Support Guidelines",
        "category": "Benefits",
        "chunk_count": 12,
        "uploaded_at": "2026-02-15"
    }
]

# Legacy Talent Placeholders
JOBS = []
CANDIDATES = []

# ─── Real MongoDB Database Connection & Persistence Layer ────────────────────
_mongo_client = None
_mongo_db = None

def get_mongo_db():
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    try:
        _mongo_client = pymongo.MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        # Test connection ping
        _mongo_client.admin.command('ping')
        _mongo_db = _mongo_client[settings.DATABASE_NAME]
        logger.info(f"Connected to MongoDB '{settings.DATABASE_NAME}' successfully at {settings.MONGODB_URL}")
        return _mongo_db
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Running with high-performance in-memory persistence.")
        _mongo_db = None
        return None

def mongo_sync_init():
    """
    On app startup: Connect to MongoDB and sync employees.
    If database contains old synthetic ERP001 data or is empty, seed clean 60 enterprise records.
    """
    global EMPLOYEES
    db = get_mongo_db()
    if db is None:
        return

    try:
        emp_col = db["employees"]
        sample = emp_col.find_one()
        # If collection is empty OR contains old mock ERP001 records, reseed with clean enterprise records
        if not sample or str(sample.get("employee_id", "")).startswith("ERP"):
            emp_col.delete_many({})
            clean_seed = [dict(e) for e in EMPLOYEES]
            emp_col.insert_many(clean_seed)
            logger.info(f"MongoDB 'employees' seeded with {len(clean_seed)} clean enterprise records.")
        else:
            # Load real MongoDB records into memory
            loaded = list(emp_col.find({}, {"_id": 0}))
            if loaded:
                EMPLOYEES.clear()
                for e in loaded:
                    e["employment_status"] = e.get("employment_status") or e.get("status") or "Active"
                    e["status"] = e["employment_status"]
                    e["currency"] = e.get("currency", "INR")
                    EMPLOYEES.append(e)
                logger.info(f"Loaded {len(EMPLOYEES)} employee records from MongoDB.")
    except Exception as e:
        logger.error(f"Error syncing with MongoDB on startup: {e}")

def mongo_save_employee(emp_dict: dict):
    db = get_mongo_db()
    if db is None:
        return
    try:
        clean = dict(emp_dict)
        emp_id = clean.get("id") or clean.get("employee_id")
        db["employees"].update_one(
            {"$or": [{"id": emp_id}, {"employee_id": emp_id}]},
            {"$set": clean},
            upsert=True
        )
    except Exception as e:
        logger.error(f"MongoDB save employee failed: {e}")

def mongo_delete_employee(emp_id: str):
    db = get_mongo_db()
    if db is None:
        return
    try:
        db["employees"].delete_many({"$or": [{"id": emp_id}, {"employee_id": emp_id}]})
    except Exception as e:
        logger.error(f"MongoDB delete employee failed: {e}")

def mongo_clear_all_employees():
    db = get_mongo_db()
    if db is None:
        return
    try:
        db["employees"].delete_many({})
    except Exception as e:
        logger.error(f"MongoDB clear employees failed: {e}")

def mongo_seed_employees(records: list):
    db = get_mongo_db()
    if db is None:
        return
    try:
        db["employees"].delete_many({})
        if records:
            clean_records = [dict(r) for r in records]
            db["employees"].insert_many(clean_records)
    except Exception as e:
        logger.error(f"MongoDB seed employees failed: {e}")

# Trigger startup sync
try:
    mongo_sync_init()
except Exception as e:
    logger.warning(f"Startup mongo sync skipped: {e}")
