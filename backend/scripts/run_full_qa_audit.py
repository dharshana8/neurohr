import os
import sys
import json
import time
import io
import requests

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

class QAResults:
    def __init__(self):
        self.passes = []
        self.warnings = []
        self.fails = []
        self.not_testable = []

    def pass_test(self, phase: str, test_id: str, description: str, details: str = ""):
        entry = {"phase": phase, "id": test_id, "desc": description, "details": details}
        self.passes.append(entry)
        print(f"[{phase}] [PASS] {test_id}: {description}")

    def warn_test(self, phase: str, test_id: str, description: str, warning_msg: str):
        entry = {"phase": phase, "id": test_id, "desc": description, "warning": warning_msg}
        self.warnings.append(entry)
        print(f"[{phase}] [WARN] {test_id}: {description} -> {warning_msg}")

    def fail_test(self, phase: str, test_id: str, description: str, error_msg: str, steps: str = "", root_cause: str = "", location: str = ""):
        entry = {
            "phase": phase,
            "id": test_id,
            "desc": description,
            "error": error_msg,
            "steps": steps,
            "root_cause": root_cause,
            "location": location
        }
        self.fails.append(entry)
        print(f"[{phase}] [FAIL] {test_id}: {description} -> {error_msg}")

    def not_testable_test(self, phase: str, test_id: str, description: str, reason: str):
        entry = {"phase": phase, "id": test_id, "desc": description, "reason": reason}
        self.not_testable.append(entry)
        print(f"[{phase}] [NOT TESTABLE] {test_id}: {description} -> {reason}")


qa = QAResults()

def run_qa_audit():
    print("==================================================")
    print("STARTING NEUROHR X FULL QA AUDIT (PHASES 1 - 7)")
    print("==================================================")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST ENVIRONMENT & STARTUP
    # ─────────────────────────────────────────────────────────────────────────
    try:
        fe_res = requests.get(FRONTEND_URL, timeout=5)
        if fe_res.status_code == 200 and "<html" in fe_res.text.lower():
            qa.pass_test("ENV", "ENV-01", "Frontend starts and serves HTML on port 5173", f"HTTP {fe_res.status_code}")
        else:
            qa.fail_test("ENV", "ENV-01", "Frontend serves HTML", f"Status: {fe_res.status_code}")
    except Exception as e:
        qa.fail_test("ENV", "ENV-01", "Frontend reachable", str(e))

    try:
        be_res = requests.get(f"{BASE_URL}/", timeout=5)
        if be_res.status_code == 200 and "NeuroHR X" in be_res.text:
            qa.pass_test("ENV", "ENV-02", "Backend health endpoint responds on port 8000", be_res.text)
        else:
            qa.fail_test("ENV", "ENV-02", "Backend health check", f"Status: {be_res.status_code}")
    except Exception as e:
        qa.fail_test("ENV", "ENV-02", "Backend health check", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1 — FOUNDATION + AUTH
    # ─────────────────────────────────────────────────────────────────────────
    ts = int(time.time())
    org_a_email = f"qa_admin_a_{ts}@acme.com"
    org_b_email = f"qa_admin_b_{ts}@beta.com"
    password = "TestPassword123!"

    reg_a = requests.post(f"{BASE_URL}/api/v1/auth/register-tenant", json={
        "organization_name": f"QA Acme Corp {ts}",
        "admin_email": org_a_email,
        "admin_password": password
    })
    if reg_a.status_code == 200:
        qa.pass_test("PHASE 1", "AUTH-01", "Tenant registration creates organization and admin", reg_a.text)
        org_a_id = reg_a.json().get("organization_id")
    else:
        qa.fail_test("PHASE 1", "AUTH-01", "Tenant registration", reg_a.text)
        org_a_id = None

    reg_b = requests.post(f"{BASE_URL}/api/v1/auth/register-tenant", json={
        "organization_name": f"QA Beta Corp {ts}",
        "admin_email": org_b_email,
        "admin_password": password
    })
    org_b_id = reg_b.json().get("organization_id") if reg_b.status_code == 200 else None

    # Login Valid Org A
    login_a = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": org_a_email, "password": password})
    if login_a.status_code == 200 and "access_token" in login_a.json():
        qa.pass_test("PHASE 1", "AUTH-02", "Login with valid credentials returns JWT", "access_token received")
        token_admin_a = login_a.json()["access_token"]
    else:
        qa.fail_test("PHASE 1", "AUTH-02", "Login with valid credentials", login_a.text)
        token_admin_a = None

    # Login Valid Org B
    login_b = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": org_b_email, "password": password})
    token_admin_b = login_b.json().get("access_token") if login_b.status_code == 200 else None

    # Login Invalid Credentials
    login_bad = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": org_a_email, "password": "WrongPassword"})
    if login_bad.status_code == 401:
        qa.pass_test("PHASE 1", "AUTH-03", "Login with invalid credentials returns 401 Unauthorized", login_bad.text)
    else:
        qa.fail_test("PHASE 1", "AUTH-03", "Login with invalid credentials", f"Status: {login_bad.status_code}")

    # Missing credentials
    login_missing = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": ""})
    if login_missing.status_code in [400, 422]:
        qa.pass_test("PHASE 1", "AUTH-04", "Login with missing credentials rejected with 422/400", f"Status: {login_missing.status_code}")
    else:
        qa.fail_test("PHASE 1", "AUTH-04", "Login with missing credentials", f"Status: {login_missing.status_code}")

    # Invalid JWT
    me_bad_jwt = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    if me_bad_jwt.status_code == 403:
        qa.pass_test("PHASE 1", "AUTH-05", "Invalid JWT rejected with 403 Forbidden", me_bad_jwt.text)
    else:
        qa.fail_test("PHASE 1", "AUTH-05", "Invalid JWT rejection", f"Status: {me_bad_jwt.status_code}")

    # Protected route without auth
    me_no_auth = requests.get(f"{BASE_URL}/api/v1/users/me")
    if me_no_auth.status_code in [401, 403]:
        qa.pass_test("PHASE 1", "AUTH-06", "Protected route without auth returns 401/403", f"Status: {me_no_auth.status_code}")
    else:
        qa.fail_test("PHASE 1", "AUTH-06", "Protected route without auth", f"Status: {me_no_auth.status_code}")

    # Authenticated user accessing allowed route
    me_auth = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token_admin_a}"})
    if me_auth.status_code == 200 and me_auth.json().get("email") == org_a_email:
        qa.pass_test("PHASE 1", "AUTH-07", "Authenticated user accesses /users/me", f"User: {me_auth.json().get('email')}, Role: {me_auth.json().get('role')}")
    else:
        qa.fail_test("PHASE 1", "AUTH-07", "Authenticated user route access", me_auth.text)

    # ─────────────────────────────────────────────────────────────────────────
    # CREATE USERS FOR RBAC IN ORG A
    # ─────────────────────────────────────────────────────────────────────────
    headers_admin_a = {"Authorization": f"Bearer {token_admin_a}"}

    hr_email = f"qa_hr_{ts}@acme.com"
    requests.post(f"{BASE_URL}/api/v1/users/", headers=headers_admin_a, json={
        "email": hr_email, "password": password, "role": "HR_MANAGER"
    })
    token_hr_a = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": hr_email, "password": password}).json().get("access_token")

    analyst_email = f"qa_analyst_{ts}@acme.com"
    requests.post(f"{BASE_URL}/api/v1/users/", headers=headers_admin_a, json={
        "email": analyst_email, "password": password, "role": "HR_ANALYST"
    })
    token_analyst_a = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": analyst_email, "password": password}).json().get("access_token")

    recruiter_email = f"qa_recruiter_{ts}@acme.com"
    requests.post(f"{BASE_URL}/api/v1/users/", headers=headers_admin_a, json={
        "email": recruiter_email, "password": password, "role": "RECRUITER"
    })
    token_recruiter_a = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": recruiter_email, "password": password}).json().get("access_token")

    headers_hr_a = {"Authorization": f"Bearer {token_hr_a}"}
    headers_analyst_a = {"Authorization": f"Bearer {token_analyst_a}"}
    headers_recruiter_a = {"Authorization": f"Bearer {token_recruiter_a}"}
    headers_admin_b = {"Authorization": f"Bearer {token_admin_b}"}

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2 — EMPLOYEE + ATTRITION
    # ─────────────────────────────────────────────────────────────────────────
    emp_payload = {
        "employee_id": f"EMP-QA-{ts}",
        "name": "Jane QA Engineer",
        "department": "Engineering",
        "role": "QA Lead",
        "joining_date": "2023-01-10T00:00:00Z",
        "experience": 5.0,
        "salary": 110000,
        "performance_score": 4.5,
        "engagement_score": 4.0,
        "overtime": 2.0,
        "skills": "Python, Selenium, Pytest, Docker, CI/CD",
        "promotion_history": 1,
        "manager_feedback": "Consistently exceeds test quality goals and drives automation.",
        "employment_status": "Active",
        "attrition": 0
    }
    create_emp = requests.post(f"{BASE_URL}/api/v1/workforce/employees", headers=headers_hr_a, json=emp_payload)
    if create_emp.status_code in [200, 201]:
        qa.pass_test("PHASE 2", "EMP-01", "Create employee via API", f"Created: {create_emp.json().get('employee_id')}")
    else:
        qa.fail_test("PHASE 2", "EMP-01", "Create employee", create_emp.text)

    read_emp = requests.get(f"{BASE_URL}/api/v1/workforce/employees/{emp_payload['employee_id']}", headers=headers_hr_a)
    if read_emp.status_code == 200 and read_emp.json().get("name") == "Jane QA Engineer":
        qa.pass_test("PHASE 2", "EMP-02", "Read employee by ID", read_emp.json().get("name"))
    else:
        qa.fail_test("PHASE 2", "EMP-02", "Read employee by ID", read_emp.text)

    list_emp = requests.get(f"{BASE_URL}/api/v1/workforce/employees", headers=headers_hr_a)
    if list_emp.status_code == 200 and any(e.get("employee_id") == emp_payload["employee_id"] for e in list_emp.json()):
        qa.pass_test("PHASE 2", "EMP-03", "List employees includes newly created employee", f"Count: {len(list_emp.json())}")
    else:
        qa.fail_test("PHASE 2", "EMP-03", "List employees", list_emp.text)

    update_emp = requests.put(f"{BASE_URL}/api/v1/workforce/employees/{emp_payload['employee_id']}", headers=headers_hr_a, json={"salary": 125000})
    if update_emp.status_code == 200 and update_emp.json().get("salary") == 125000:
        qa.pass_test("PHASE 2", "EMP-04", "Update employee salary", f"New salary: {update_emp.json().get('salary')}")
    else:
        qa.fail_test("PHASE 2", "EMP-04", "Update employee", update_emp.text)

    dup_emp = requests.post(f"{BASE_URL}/api/v1/workforce/employees", headers=headers_hr_a, json=emp_payload)
    if dup_emp.status_code == 400:
        qa.pass_test("PHASE 2", "EMP-05", "Duplicate employee_id returns 400 Bad Request", dup_emp.text)
    else:
        qa.fail_test("PHASE 2", "EMP-05", "Duplicate employee ID validation", f"Status: {dup_emp.status_code}")

    # CSV Upload
    csv_content = f"""employee_id,name,department,role,joining_date,experience,salary,performance_score,engagement_score,overtime,skills,promotion_history,manager_feedback,employment_status,attrition
CSV-EMP-{ts}-1,Alice CSV,Product,Product Manager,2022-05-01T00:00:00Z,4.0,95000,4.0,4.2,3.0,"Product Strategy, Agile",0,Good communicator,Active,0
CSV-EMP-{ts}-2,Bob CSV,Engineering,Developer,2021-08-15T00:00:00Z,3.0,85000,3.8,3.5,8.0,"React, TypeScript",1,Solid coder,Active,1
"""
    files = {"file": ("test_employees.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    csv_res = requests.post(f"{BASE_URL}/api/v1/workforce/import", headers=headers_hr_a, files=files)
    if csv_res.status_code in [200, 201]:
        qa.pass_test("PHASE 2", "CSV-01", "Valid CSV employee upload parsed & persisted", str(csv_res.json()))
    else:
        qa.fail_test("PHASE 2", "CSV-01", "Valid CSV employee upload", csv_res.text)

    bad_csv = "employee_id,name\nBAD-1,No Department\n"
    files_bad = {"file": ("bad.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")}
    bad_csv_res = requests.post(f"{BASE_URL}/api/v1/workforce/import", headers=headers_hr_a, files=files_bad)
    if bad_csv_res.status_code == 400:
        qa.pass_test("PHASE 2", "CSV-02", "Invalid CSV missing required columns returns 400", bad_csv_res.text)
    else:
        qa.fail_test("PHASE 2", "CSV-02", "Invalid CSV rejection", f"Status: {bad_csv_res.status_code}")

    # Attrition Prediction
    attr_res = requests.post(f"{BASE_URL}/api/v1/attrition/predict/{emp_payload['employee_id']}", headers=headers_hr_a)
    if attr_res.status_code == 200 and "risk_score" in attr_res.json():
        data_attr = attr_res.json()
        qa.pass_test("PHASE 2", "ATTR-01", "Single employee attrition prediction generated dynamically via ML",
                     f"Score: {data_attr.get('risk_score')}, Classification: {data_attr.get('risk_level') or data_attr.get('attrition_risk')}")
    else:
        qa.fail_test("PHASE 2", "ATTR-01", "Attrition prediction", attr_res.text)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3 — MULTI-TENANT ISOLATION & RBAC
    # ─────────────────────────────────────────────────────────────────────────
    cross_emp = requests.get(f"{BASE_URL}/api/v1/workforce/employees/{emp_payload['employee_id']}", headers=headers_admin_b)
    if cross_emp.status_code in [403, 404]:
        qa.pass_test("PHASE 3", "TENANT-01", "Org B admin cannot access Org A employee record (Tenant Isolation)", f"Status: {cross_emp.status_code}")
    else:
        qa.fail_test("PHASE 3", "TENANT-01", "Cross-tenant employee leak", f"Status: {cross_emp.status_code}")

    list_b = requests.get(f"{BASE_URL}/api/v1/workforce/employees", headers=headers_admin_b)
    if list_b.status_code == 200 and all(e.get("employee_id") != emp_payload["employee_id"] for e in list_b.json()):
        qa.pass_test("PHASE 3", "TENANT-02", "Org B employee list isolated from Org A", f"Org B count: {len(list_b.json())}")
    else:
        qa.fail_test("PHASE 3", "TENANT-02", "Cross-tenant employee list leakage", list_b.text)

    # RBAC: Recruiter trying to delete an employee -> DENIED (403)
    del_by_recruiter = requests.delete(f"{BASE_URL}/api/v1/workforce/employees/{emp_payload['employee_id']}", headers=headers_recruiter_a)
    if del_by_recruiter.status_code == 403:
        qa.pass_test("PHASE 3", "RBAC-01", "Recruiter role blocked from workforce employee mutation (403 Forbidden)", del_by_recruiter.text)
    else:
        qa.fail_test("PHASE 3", "RBAC-01", "Recruiter role restriction on workforce", f"Status: {del_by_recruiter.status_code}")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4 — INTEGRATION LAYER
    # ─────────────────────────────────────────────────────────────────────────
    integ_payload = {
        "provider_name": f"Workday Demo HRIS {ts}",
        "provider_type": "HRIS",
        "credentials": {"api_url": "https://api.workday.demo/v1", "auth_type": "Bearer", "api_key": "mock_hris_key"}
    }
    reg_integ = requests.post(f"{BASE_URL}/api/v1/integrations/", headers=headers_admin_a, json=integ_payload)
    if reg_integ.status_code in [200, 201]:
        integ_id = reg_integ.json().get("id")
        qa.pass_test("PHASE 4", "INT-01", "Register integration connector", f"ID: {integ_id}")
    else:
        qa.fail_test("PHASE 4", "INT-01", "Create integration connector", reg_integ.text)
        integ_id = None

    if integ_id:
        test_conn = requests.post(f"{BASE_URL}/api/v1/integrations/{integ_id}/test", headers=headers_admin_a)
        if test_conn.status_code == 200:
            qa.pass_test("PHASE 4", "INT-02", "Test integration connector connection", str(test_conn.json()))
        else:
            qa.warn_test("PHASE 4", "INT-02", "Test integration connection", f"Status: {test_conn.status_code}")

        cross_integ = requests.post(f"{BASE_URL}/api/v1/integrations/{integ_id}/test", headers=headers_admin_b)
        if cross_integ.status_code in [403, 404]:
            qa.pass_test("PHASE 4", "INT-03", "Cross-tenant integration access denied", f"Status: {cross_integ.status_code}")
        else:
            qa.fail_test("PHASE 4", "INT-03", "Cross-tenant integration access", f"Status: {cross_integ.status_code}")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 5 — RECRUITMENT / ATS
    # ─────────────────────────────────────────────────────────────────────────
    job_payload = {
        "title": f"Lead Automation Engineer {ts}",
        "description": "Leading the end-to-end automated test framework for NeuroHR X.",
        "required_skills": ["Python", "Pytest", "Selenium", "Docker"],
        "minimum_experience": 4.0,
        "qualification": "B.Tech Computer Science",
        "location": "Remote",
        "employment_type": "Full-time",
        "status": "Open"
    }
    create_job = requests.post(f"{BASE_URL}/api/v1/recruitment/jobs", headers=headers_recruiter_a, json=job_payload)
    if create_job.status_code in [200, 201]:
        job_id = create_job.json().get("job_id")
        qa.pass_test("PHASE 5", "ATS-01", "Recruiter creates job opening", f"Job ID: {job_id}")
    else:
        qa.fail_test("PHASE 5", "ATS-01", "Create job opening", create_job.text)
        job_id = None

    cand_payload = {
        "name": "Alex Candidate",
        "email": f"alex_{ts}@example.com",
        "skills": ["Python", "Pytest", "Selenium", "Docker", "AWS"],
        "experience": 5.5,
        "education": "Master of Science in Software Engineering",
        "source": "MANUAL",
        "status": "Applied"
    }
    create_cand = requests.post(f"{BASE_URL}/api/v1/recruitment/candidates", headers=headers_recruiter_a, json=cand_payload)
    if create_cand.status_code in [200, 201]:
        cand_id = create_cand.json().get("candidate_id")
        qa.pass_test("PHASE 5", "ATS-02", "Recruiter creates candidate profile", f"Candidate ID: {cand_id}")
    else:
        qa.fail_test("PHASE 5", "ATS-02", "Create candidate profile", create_cand.text)
        cand_id = None

    if job_id and cand_id:
        rank_res = requests.post(f"{BASE_URL}/api/v1/recruitment/jobs/{job_id}/rank", headers=headers_recruiter_a)
        if rank_res.status_code == 200:
            rank_data = rank_res.json()
            rankings = rank_data.get("rankings", [])
            cand_match = next((r for r in rankings if r.get("candidate_id") == cand_id), None)
            if cand_match and cand_match.get("match_score", 0) > 0:
                qa.pass_test("PHASE 5", "ATS-03", "Dynamic candidate-job match calculation",
                             f"Score: {cand_match.get('match_score')}%, Matched: {cand_match.get('matched_skills')}")
            else:
                qa.warn_test("PHASE 5", "ATS-03", "Candidate matching calculation returned rankings without candidate", str(rankings))
        else:
            qa.fail_test("PHASE 5", "ATS-03", "Candidate ranking endpoint", rank_res.text)

    if job_id:
        cross_job = requests.get(f"{BASE_URL}/api/v1/recruitment/jobs/{job_id}", headers=headers_admin_b)
        if cross_job.status_code in [403, 404]:
            qa.pass_test("PHASE 5", "ATS-04", "Cross-tenant job access denied", f"Status: {cross_job.status_code}")
        else:
            qa.fail_test("PHASE 5", "ATS-04", "Cross-tenant job access", f"Status: {cross_job.status_code}")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 6 — SKILL GAP + CAREER PATHING
    # ─────────────────────────────────────────────────────────────────────────
    skill_res = requests.post(f"{BASE_URL}/api/v1/intelligence/skills", headers=headers_hr_a, json={
        "name": f"End-to-End Automation {ts}", "category": "Testing", "aliases": ["E2E", "e2e testing"]
    })
    if skill_res.status_code in [200, 201]:
        qa.pass_test("PHASE 6", "SKILL-01", "Create skill in taxonomy", f"Skill: {skill_res.json().get('name')}")
    else:
        qa.fail_test("PHASE 6", "SKILL-01", "Create skill in taxonomy", skill_res.text)

    role_req = requests.post(f"{BASE_URL}/api/v1/intelligence/role-requirements", headers=headers_hr_a, json={
        "role": f"Principal QA Architect {ts}",
        "required_skills": ["Python", "Docker", "Kubernetes", "AWS"],
        "preferred_skills": ["FastAPI", "Machine Learning"]
    })
    if role_req.status_code in [200, 201]:
        qa.pass_test("PHASE 6", "SKILL-02", "Create role skill requirement", role_req.json().get("role"))
        target_role = f"Principal QA Architect {ts}"
    else:
        qa.fail_test("PHASE 6", "SKILL-02", "Create role skill requirement", role_req.text)
        target_role = None

    if target_role:
        gap_res = requests.post(f"{BASE_URL}/api/v1/intelligence/skill-gaps/analyze", headers=headers_hr_a, json={
            "employee_id": emp_payload["employee_id"],
            "target_role": target_role
        })
        if gap_res.status_code == 200:
            gap_data = gap_res.json()
            qa.pass_test("PHASE 6", "SKILL-03", "Dynamic skill gap analysis computed",
                         f"Coverage: {gap_data.get('skill_coverage_score')}%, Matched: {len(gap_data.get('matched_skills', []))}, Missing: {len(gap_data.get('missing_skills', []))}")
        else:
            qa.fail_test("PHASE 6", "SKILL-03", "Dynamic skill gap analysis", gap_res.text)

    if target_role:
        career_res = requests.post(f"{BASE_URL}/api/v1/intelligence/career-paths/generate", headers=headers_hr_a, json={
            "employee_id": emp_payload["employee_id"],
            "target_role": target_role
        })
        if career_res.status_code == 200:
            c_data = career_res.json()
            qa.pass_test("PHASE 6", "CAREER-01", "Career path recommendation plan generated",
                         f"Milestones: {len(c_data.get('milestones', []))}, Recommended Actions: {len(c_data.get('recommended_actions', []))}")
        else:
            qa.fail_test("PHASE 6", "CAREER-01", "Career path recommendation", career_res.text)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 7 — WORKPLACE SENTIMENT INTELLIGENCE
    # ─────────────────────────────────────────────────────────────────────────
    fb_res = requests.post(f"{BASE_URL}/api/v1/feedback", headers=headers_hr_a, json={
        "department": "Engineering",
        "category": "WORKLOAD",
        "feedback_text": "The sprint workload has been exhausting and task pacing requires review.",
        "employee_id": emp_payload["employee_id"],
        "source": "SURVEY"
    })
    if fb_res.status_code in [200, 201]:
        fb_id = fb_res.json().get("feedback_id")
        sent = fb_res.json().get("sentiment_result", {}).get("sentiment")
        qa.pass_test("PHASE 7", "SENT-01", "Submit employee feedback & automatic sentiment scoring", f"ID: {fb_id}, Sentiment: {sent}")
    else:
        qa.fail_test("PHASE 7", "SENT-01", "Submit employee feedback", fb_res.text)
        fb_id = None

    batch_res = requests.post(f"{BASE_URL}/api/v1/sentiment/analyze-all", headers=headers_analyst_a)
    if batch_res.status_code == 200:
        qa.pass_test("PHASE 7", "SENT-02", "Batch analyze all feedbacks for organization", str(batch_res.json()))
    else:
        qa.fail_test("PHASE 7", "SENT-02", "Batch analyze feedbacks", batch_res.text)

    dept_res = requests.get(f"{BASE_URL}/api/v1/sentiment/department", headers=headers_analyst_a)
    if dept_res.status_code == 200 and dept_res.json().get("total_feedback", 0) > 0:
        qa.pass_test("PHASE 7", "SENT-03", "Department sentiment aggregation from MongoDB records",
                     f"Total: {dept_res.json().get('total_feedback')}, Depts: {len(dept_res.json().get('departments', []))}")
    else:
        qa.fail_test("PHASE 7", "SENT-03", "Department sentiment aggregation", dept_res.text)

    theme_res = requests.get(f"{BASE_URL}/api/v1/sentiment/themes", headers=headers_analyst_a)
    if theme_res.status_code == 200 and len(theme_res.json().get("themes", [])) > 0:
        qa.pass_test("PHASE 7", "SENT-04", "Theme extraction taxonomy",
                     f"Top theme: {theme_res.json()['themes'][0].get('theme')} ({theme_res.json()['themes'][0].get('count')} mentions)")
    else:
        qa.fail_test("PHASE 7", "SENT-04", "Theme extraction", theme_res.text)

    insight_res = requests.post(f"{BASE_URL}/api/v1/sentiment/insight", headers=headers_analyst_a, json={})
    if insight_res.status_code == 200 and insight_res.json().get("insight"):
        qa.pass_test("PHASE 7", "SENT-05", "Grok/Fallback AI executive insight generated",
                     f"Insight: {insight_res.json().get('insight')[:80]}...")
    else:
        qa.fail_test("PHASE 7", "SENT-05", "Executive AI insight generation", insight_res.text)

    if fb_id:
        analyst_view = requests.get(f"{BASE_URL}/api/v1/feedback/{fb_id}", headers=headers_analyst_a)
        if analyst_view.status_code == 200:
            if analyst_view.json().get("employee_id") is None:
                qa.pass_test("PHASE 7", "PRIV-01", "Employee ID masked for HR_ANALYST role in feedback API", "employee_id: null")
            else:
                qa.fail_test("PHASE 7", "PRIV-01", "Employee ID privacy leak to HR_ANALYST", f"Exposed: {analyst_view.json().get('employee_id')}")
        else:
            qa.fail_test("PHASE 7", "PRIV-01", "Read feedback by analyst", analyst_view.text)

    recruiter_sent = requests.get(f"{BASE_URL}/api/v1/sentiment/department", headers=headers_recruiter_a)
    if recruiter_sent.status_code == 403:
        qa.pass_test("PHASE 7", "PRIV-02", "Recruiter role blocked from employee sentiment data (403 Forbidden)", recruiter_sent.text)
    else:
        qa.fail_test("PHASE 7", "PRIV-02", "Recruiter role sentiment access restriction", f"Status: {recruiter_sent.status_code}")

    # Clean up test employee
    requests.delete(f"{BASE_URL}/api/v1/workforce/employees/{emp_payload['employee_id']}", headers=headers_hr_a)

    print("\n==================================================")
    print("QA AUDIT SUMMARY:")
    print(f"PASS: {len(qa.passes)}")
    print(f"WARN: {len(qa.warnings)}")
    print(f"FAIL: {len(qa.fails)}")
    print(f"NOT TESTABLE: {len(qa.not_testable)}")
    print("==================================================")

    with open("qa_audit_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "passes": qa.passes,
            "warnings": qa.warnings,
            "fails": qa.fails,
            "not_testable": qa.not_testable
        }, f, indent=2)

if __name__ == "__main__":
    run_qa_audit()
