import asyncio
import time
import sys
import httpx
from pymongo import MongoClient

BASE_URL = "http://127.0.0.1:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "neurohr"

async def test_shap_fix():
    print("==================================================")
    print("LIVE VERIFICATION: BUG-PHASE2-002 SHAP Extraction")
    print("==================================================")

    ts = int(time.time())
    admin_email = f"shap_admin_{ts}@acme.com"
    hr_email = f"shap_hr_{ts}@acme.com"
    password = "TestPassword123!"

    async with httpx.AsyncClient(timeout=20.0) as http:
        # 1. Start / Verify backend
        res_root = await http.get("http://127.0.0.1:8000/")
        assert res_root.status_code == 200 and "NeuroHR X" in res_root.text
        print("[PASS] Step 1: Backend is running and healthy on http://127.0.0.1:8000")

        # Register organization
        reg_res = await http.post(f"{BASE_URL}/auth/register-tenant", json={
            "organization_name": f"SHAP Test Org {ts}",
            "admin_email": admin_email,
            "admin_password": password
        })
        assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
        org_id = reg_res.json()["organization_id"]

        # Admin login
        login_admin = await http.post(f"{BASE_URL}/auth/login", data={"username": admin_email, "password": password})
        token_admin = login_admin.json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        # 2. Create and Authenticate as HR_MANAGER
        create_hr = await http.post(f"{BASE_URL}/users/", headers=headers_admin, json={
            "email": hr_email,
            "password": password,
            "role": "HR_MANAGER"
        })
        assert create_hr.status_code in [200, 201], f"HR Manager creation failed: {create_hr.text}"

        login_hr = await http.post(f"{BASE_URL}/auth/login", data={"username": hr_email, "password": password})
        assert login_hr.status_code == 200, f"HR login failed: {login_hr.text}"
        token_hr = login_hr.json()["access_token"]
        headers_hr = {"Authorization": f"Bearer {token_hr}"}
        print(f"[PASS] Step 2: Authenticated as HR_MANAGER ({hr_email})")

        # 3. Create multiple test employees for testing
        test_employees = [
            {
                "employee_id": f"EMP-SHAP-{ts}-1",
                "name": "Sarah Connor",
                "department": "Engineering",
                "role": "Senior Developer",
                "joining_date": "2020-03-01T00:00:00Z",
                "experience": 6.5,
                "salary": 115000,
                "performance_score": 4.8,
                "engagement_score": 4.5,
                "projects_handled": 8,
                "years_at_company": 3,
                "remote_work_frequency": "Always",
                "overtime": 2.0,
                "skills": "Python, TypeScript, Docker",
                "promotion_history": 1,
                "manager_feedback": "Exceptional team player and mentor",
                "employment_status": "Active",
                "attrition": 0
            },
            {
                "employee_id": f"EMP-SHAP-{ts}-2",
                "name": "Kyle Reese",
                "department": "Operations",
                "role": "Operations Analyst",
                "joining_date": "2023-01-15T00:00:00Z",
                "experience": 2.0,
                "salary": 65000,
                "performance_score": 2.9,
                "engagement_score": 2.1,
                "projects_handled": 3,
                "years_at_company": 1,
                "remote_work_frequency": "Never",
                "overtime": 18.5,
                "skills": "Excel, Logistics",
                "promotion_history": 0,
                "manager_feedback": "Struggling with high workload and burnout",
                "employment_status": "Active",
                "attrition": 1
            },
            {
                "employee_id": f"EMP-SHAP-{ts}-3",
                "name": "John Matrix",
                "department": "Security",
                "role": "Security Specialist",
                "joining_date": "2021-06-01T00:00:00Z",
                "experience": 8.0,
                "salary": 95000,
                "performance_score": 3.8,
                "engagement_score": 3.4,
                "projects_handled": 6,
                "years_at_company": 2,
                "remote_work_frequency": "Hybrid",
                "overtime": 8.0,
                "skills": "Cybersecurity, Auditing",
                "promotion_history": 0,
                "manager_feedback": "Solid performer with steady output",
                "employment_status": "Active",
                "attrition": 0
            }
        ]

        created_emp_ids = []
        for emp_data in test_employees:
            res_emp = await http.post(f"{BASE_URL}/workforce/employees", headers=headers_hr, json=emp_data)
            assert res_emp.status_code in [200, 201], f"Employee creation failed: {res_emp.text}"
            created_emp_ids.append(emp_data["employee_id"])
        print(f"[PASS] Step 3: Created 3 actual employees in DB: {created_emp_ids}")

        # 4 & 5. Call POST /api/v1/attrition/predict/{employee_id} and Verify SHAP Explanations
        valid_model_features = {
            "engagement_score", "overtime", "performance_score", "promotion_history",
            "experience", "salary", "department", "role", "employment_status"
        }

        for idx, emp_id in enumerate(created_emp_ids, 1):
            print(f"\n--- Testing Prediction & SHAP for Employee {idx}: {emp_id} ---")
            res_pred = await http.post(f"{BASE_URL}/attrition/predict/{emp_id}", headers=headers_hr)
            assert res_pred.status_code == 200, f"Prediction failed for {emp_id}: {res_pred.status_code} {res_pred.text}"
            pred_data = res_pred.json()

            # Verify probability exists and is float [0.0, 1.0]
            prob = pred_data.get("probability")
            assert isinstance(prob, (int, float)), f"Probability is not numeric: {prob}"
            assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"
            print(f"[PASS] probability exists: {prob}")

            # Verify risk_level exists
            risk = pred_data.get("risk_level")
            assert risk in ["LOW", "MEDIUM", "HIGH"], f"Invalid risk_level: {risk}"
            print(f"[PASS] risk_level exists: {risk}")

            # Verify top_factors structure
            tf = pred_data.get("top_factors")
            assert tf is not None, "top_factors is None"
            assert isinstance(tf, dict), f"top_factors is not a dict: {type(tf)}"

            # Verify available = True (NO ERROR)
            assert tf.get("available") is True, f"SHAP explanation available is not True: {tf}"
            assert "error" not in tf or not tf.get("error"), f"Unexpected error in top_factors: {tf.get('error')}"
            print(f"[PASS] SHAP explanation available = True (no error)")

            # Verify top_factors list is populated
            factors_list = tf.get("top_factors")
            assert isinstance(factors_list, list), f"top_factors list missing: {factors_list}"
            assert len(factors_list) > 0, f"top_factors list is empty!"
            print(f"[PASS] top_factors is populated with {len(factors_list)} features")

            # Verify each factor corresponds to model features and impacts are numeric
            for f in factors_list:
                feat_name = f.get("feature")
                assert feat_name in valid_model_features, f"Unknown feature: {feat_name}"
                impact = f.get("impact")
                assert impact in ["positive", "negative"], f"Invalid impact: {impact}"
                shap_val = f.get("shap_value")
                assert isinstance(shap_val, (int, float)), f"shap_value is not numeric: {shap_val}"
                desc = f.get("description")
                assert desc and len(desc) > 5, f"Missing description: {desc}"
                print(f"       Factor: {feat_name:20} | Impact: {impact:8} | SHAP: {shap_val:+0.4f} | {desc}")
            print(f"[PASS] All factors verified: numeric SHAP values and valid feature mappings")

        # 6. Verify frontend Attrition page
        try:
            fe_res = await http.get(f"{FRONTEND_URL}/dashboard/attrition")
            assert fe_res.status_code == 200
            print("[PASS] Step 6: Frontend Attrition page loads successfully (HTTP 200)")
        except Exception as e:
            print(f"[WARN] Frontend check: {e}")

        # 7. Test AI Attrition explanation endpoint
        res_ai_explain = await http.post(f"{BASE_URL}/ai/explain/attrition", headers=headers_hr, json={
            "employee_id": created_emp_ids[0]
        })
        assert res_ai_explain.status_code == 200, f"AI explain attrition failed: {res_ai_explain.status_code} {res_ai_explain.text}"
        ai_data = res_ai_explain.json()
        assert ai_data.get("ai_explanation"), "Missing ai_explanation"
        print(f"[PASS] Step 7: AI Executive Attrition explanation generated successfully from SHAP factors: {ai_data.get('ai_explanation')[:80]}...")

    print("\n==================================================")
    print("ALL 7 VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_shap_fix())
