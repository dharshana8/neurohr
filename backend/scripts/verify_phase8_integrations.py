import asyncio
import time
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def run_live_phase8_verification():
    print("=" * 60)
    print("LIVE END-TO-END PHASE 8 VERIFICATION")
    print("Demo ERP + Demo HRIS Real Integration Implementation")
    print("=" * 60)

    ts = int(time.time())
    admin_a_email = f"erp_admin_{ts}@acme.com"
    admin_b_email = f"erp_org_b_{ts}@omni.com"
    password = "TestPassword123!"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Health check
        res_root = await client.get("http://127.0.0.1:8000/")
        assert res_root.status_code == 200, f"Backend not running: {res_root.text}"
        print("[PASS] Step 1: Backend is running and healthy.")

        # Step 2: Register Org A & Login
        reg_a = await client.post(f"{BASE_URL}/auth/register-tenant", json={
            "organization_name": f"Enterprise Org A {ts}",
            "admin_email": admin_a_email,
            "admin_password": password
        })
        assert reg_a.status_code == 200, f"Registration failed: {reg_a.text}"
        org_a_id = reg_a.json()["organization_id"]

        login_a = await client.post(f"{BASE_URL}/auth/login", data={"username": admin_a_email, "password": password})
        assert login_a.status_code == 200
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print(f"[PASS] Step 2: Registered Org A ({org_a_id}) and authenticated as Admin.")

        # Step 3: Connect Demo ERP
        res_erp = await client.post(f"{BASE_URL}/integrations", headers=headers_a, json={
            "provider_name": "demo_erp",
            "provider_type": "DEMO_ERP"
        })
        assert res_erp.status_code in [200, 201], f"ERP creation failed: {res_erp.text}"
        erp_data = res_erp.json()
        erp_id = erp_data["integration_id"]
        assert erp_id.startswith("INT-")
        print(f"[PASS] Step 3: Demo ERP provisioned with auto-generated integration_id: {erp_id}")

        # Step 4: Test Connection on Demo ERP
        test_erp = await client.post(f"{BASE_URL}/integrations/{erp_id}/test", headers=headers_a)
        assert test_erp.status_code == 200
        assert test_erp.json()["status"] == "SUCCESS"
        print("[PASS] Step 4: Demo ERP live connection test successful.")

        # Step 5: Sync Demo ERP
        sync_erp = await client.post(f"{BASE_URL}/integrations/{erp_id}/sync", headers=headers_a)
        assert sync_erp.status_code == 200, f"ERP sync failed: {sync_erp.text}"
        res_sync_erp = sync_erp.json()
        assert res_sync_erp["records_fetched"] == 100
        assert res_sync_erp["records_created"] == 100
        assert res_sync_erp["records_updated"] == 0
        assert res_sync_erp["records_failed"] == 0
        print(f"[PASS] Step 5: Demo ERP sync complete: 100 fetched, 100 created in MongoDB.")

        # Step 6: Verify employees in Employee Directory
        emp_dir = await client.get(f"{BASE_URL}/workforce/employees", headers=headers_a)
        assert emp_dir.status_code == 200
        emps = emp_dir.json()
        assert len(emps) == 100
        print(f"[PASS] Step 6: Employee Directory displays all {len(emps)} synced employees.")

        # Step 7: Run bulk attrition prediction on synced employees
        bulk_attr = await client.post(f"{BASE_URL}/attrition/predict-all", headers=headers_a)
        assert bulk_attr.status_code == 200
        attr_summary = await client.get(f"{BASE_URL}/attrition/summary", headers=headers_a)
        assert attr_summary.status_code == 200
        summary_data = attr_summary.json()
        assert summary_data["total_analyzed"] == 100
        print(f"[PASS] Step 7: Attrition AI model successfully analyzed all 100 synced ERP employees.")
        print(f"       High Risk: {summary_data['high_risk']}, Medium: {summary_data['medium_risk']}, Low: {summary_data['low_risk']}")

        # Step 8: Open Skill Gap / Intelligence module
        skill_res = await client.get(f"{BASE_URL}/intelligence/skills", headers=headers_a)
        assert skill_res.status_code == 200
        print(f"[PASS] Step 8: Skill taxonomy verified: {len(skill_res.json())} skills accessible.")

        gap_res = await client.post(f"{BASE_URL}/intelligence/skill-gaps/analyze", headers=headers_a, json={
            "employee_id": "ERP001",
            "target_role": "Software Engineer"
        })
        assert gap_res.status_code in [200, 201], f"Skill gap failed: {gap_res.text}"
        gap_data = gap_res.json()
        print(f"[PASS] Step 8b: Skill Gap Analysis on ERP001 successful: Score = {gap_data.get('skill_coverage_score')}%")

        # Step 9: Connect Demo HRIS
        res_hris = await client.post(f"{BASE_URL}/integrations", headers=headers_a, json={
            "provider_name": "demo_hris",
            "provider_type": "DEMO_HRIS"
        })
        assert res_hris.status_code in [200, 201]
        hris_id = res_hris.json()["integration_id"]
        print(f"[PASS] Step 9: Demo HRIS provisioned with integration_id: {hris_id}")

        # Step 10: Sync Demo HRIS (Deduplication & In-place Update verification!)
        sync_hris = await client.post(f"{BASE_URL}/integrations/{hris_id}/sync", headers=headers_a)
        assert sync_hris.status_code == 200
        res_sync_hris = sync_hris.json()
        assert res_sync_hris["records_fetched"] == 100
        assert res_sync_hris["records_created"] == 0   # ZERO duplicates!
        assert res_sync_hris["records_updated"] == 100 # All 100 updated in-place!
        assert res_sync_hris["records_failed"] == 0
        print("[PASS] Step 10: Demo HRIS sync complete: 0 duplicates created, 100 employees updated in-place!")

        # Step 11: Verify total count in Employee Directory is STILL exactly 100
        emp_dir_after = await client.get(f"{BASE_URL}/workforce/employees", headers=headers_a)
        assert emp_dir_after.status_code == 200
        assert len(emp_dir_after.json()) == 100
        print("[PASS] Step 11: Employee Directory verified: Total count remains strictly 100 (no duplicate bloat).")

        # Step 12: Check Sync Logs
        logs_res = await client.get(f"{BASE_URL}/integrations/{erp_id}/sync-logs", headers=headers_a)
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert len(logs) >= 1
        print(f"[PASS] Step 12: Sync logs verified: {len(logs)} audit entries recorded with exact metrics.")

        # Step 13: Register Org B & Verify Multi-Tenant Isolation
        reg_b = await client.post(f"{BASE_URL}/auth/register-tenant", json={
            "organization_name": f"Enterprise Org B {ts}",
            "admin_email": admin_b_email,
            "admin_password": password
        })
        assert reg_b.status_code == 200
        login_b = await client.post(f"{BASE_URL}/auth/login", data={"username": admin_b_email, "password": password})
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Org B must not see Org A's integration
        org_b_get = await client.get(f"{BASE_URL}/integrations/{erp_id}", headers=headers_b)
        assert org_b_get.status_code == 404
        # Org B has 0 employees
        org_b_emps = await client.get(f"{BASE_URL}/workforce/employees", headers=headers_b)
        assert len(org_b_emps.json()) == 0
        print("[PASS] Step 13: Multi-tenant cross-isolation verified: Org B cannot access Org A integrations or employees.")

    print("=" * 60)
    print("ALL 13 LIVE VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_live_phase8_verification())
