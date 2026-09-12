import asyncio
import time
import sys
import httpx
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = "http://127.0.0.1:8000/api/v1"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "neurohr"

async def run_verification():
    print("==================================================")
    print("LIVE VERIFICATION: BUG-PHASE4-001 Integration Fix")
    print("==================================================")

    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    integrations_coll = db["integrations"]

    ts = int(time.time())
    org_a_email = f"int_admin_a_{ts}@acme.com"
    org_b_email = f"int_admin_b_{ts}@beta.com"
    password = "TestPassword123!"

    async with httpx.AsyncClient(timeout=15.0) as http:
        # Step 1: Verify backend is running
        try:
            health = await http.get("http://127.0.0.1:8000/")
            assert health.status_code == 200 and "NeuroHR X" in health.text
            print("[PASS] Step 1: Backend is running and healthy on http://127.0.0.1:8000")
        except Exception as e:
            print(f"FAIL: Backend is not running on http://127.0.0.1:8000: {e}")
            sys.exit(1)

        # Register Tenant A
        reg_a = await http.post(f"{BASE_URL}/auth/register-tenant", json={
            "organization_name": f"Integration Org A {ts}",
            "admin_email": org_a_email,
            "admin_password": password
        })
        assert reg_a.status_code == 200, f"Tenant A registration failed: {reg_a.text}"
        org_a_id = reg_a.json()["organization_id"]

        # Register Tenant B
        reg_b = await http.post(f"{BASE_URL}/auth/register-tenant", json={
            "organization_name": f"Integration Org B {ts}",
            "admin_email": org_b_email,
            "admin_password": password
        })
        assert reg_b.status_code == 200, f"Tenant B registration failed: {reg_b.text}"
        org_b_id = reg_b.json()["organization_id"]

        # Login User A
        login_a = await http.post(f"{BASE_URL}/auth/login", data={"username": org_a_email, "password": password})
        assert login_a.status_code == 200, f"Login A failed: {login_a.text}"
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Login User B
        login_b = await http.post(f"{BASE_URL}/auth/login", data={"username": org_b_email, "password": password})
        assert login_b.status_code == 200, f"Login B failed: {login_b.text}"
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print("[PASS] Authenticated Admin A and Admin B")
        # Step 2: Create an integration through actual API
        create_payload = {
            "provider_name": "demo_hris",
            "provider_type": "hris",
            "credentials": {"api_key": "live-test-key-123"}
        }
        res_create = await http.post(f"{BASE_URL}/integrations/", json=create_payload, headers=headers_a)
        print(f"POST /api/v1/integrations/ -> status {res_create.status_code}")
        
        # Step 3: Verify HTTP success
        if res_create.status_code not in [200, 201]:
            print(f"FAIL: Create integration failed with status {res_create.status_code}: {res_create.text}")
            sys.exit(1)
        created_data = res_create.json()
        print(f"[PASS] Step 2 & 3: HTTP success on POST /api/v1/integrations/: {created_data}")

        int_id = created_data.get("id")
        unique_integration_id = created_data.get("integration_id")
        assert int_id, "Response missing id"
        assert unique_integration_id, "Response missing integration_id"
        print(f"[PASS] Created Integration response: id={int_id}, integration_id={unique_integration_id}")

        # Step 4: Verify the integration is persisted in MongoDB
        mongo_doc = integrations_coll.find_one({"_id": ObjectId(int_id)})
        if not mongo_doc:
            print(f"FAIL: Integration _id={int_id} not found in MongoDB collection 'integrations'")
            sys.exit(1)
        print(f"[PASS] Step 4: Integration persisted in MongoDB: {mongo_doc}")

        # Step 5: Verify integration_id exists and is unique
        doc_integration_id = mongo_doc.get("integration_id")
        if not doc_integration_id or doc_integration_id != unique_integration_id:
            print(f"FAIL: MongoDB doc integration_id '{doc_integration_id}' mismatch with API '{unique_integration_id}'")
            sys.exit(1)
        print(f"[PASS] Step 5: integration_id exists in MongoDB: '{doc_integration_id}'")

        # Create second integration to test uniqueness
        res_create_2 = await http.post(f"{BASE_URL}/integrations/", json={
            "provider_name": "demo_erp",
            "provider_type": "erp",
            "credentials": {"token": "erp-token-789"}
        }, headers=headers_a)
        assert res_create_2.status_code in [200, 201], f"Create integration 2 failed: {res_create_2.text}"
        created_data_2 = res_create_2.json()
        doc_2 = integrations_coll.find_one({"_id": ObjectId(created_data_2["id"])})
        doc_integration_id_2 = doc_2.get("integration_id")

        assert doc_integration_id != doc_integration_id_2, f"integration_ids are duplicate! {doc_integration_id}"
        print(f"[PASS] Step 5 (Uniqueness verified): Integration 1 ID = {doc_integration_id}, Integration 2 ID = {doc_integration_id_2}")

        # Step 6: Test GET / UPDATE / DELETE for the created integration
        # 6a. GET list
        res_list = await http.get(f"{BASE_URL}/integrations/", headers=headers_a)
        assert res_list.status_code == 200
        list_ids = [i["id"] for i in res_list.json()]
        assert int_id in list_ids and created_data_2["id"] in list_ids
        print(f"[PASS] Step 6a: GET /api/v1/integrations/ successfully lists all {len(list_ids)} integrations for Org A")

        # 6b. GET single (by Mongo _id and by integration_id UUID)
        res_get_by_id = await http.get(f"{BASE_URL}/integrations/{int_id}", headers=headers_a)
        assert res_get_by_id.status_code == 200, f"GET by Mongo id failed: {res_get_by_id.status_code}"
        res_get_by_uuid = await http.get(f"{BASE_URL}/integrations/{doc_integration_id}", headers=headers_a)
        assert res_get_by_uuid.status_code == 200, f"GET by UUID failed: {res_get_by_uuid.status_code}"
        assert res_get_by_id.json()["id"] == res_get_by_uuid.json()["id"]
        print(f"[PASS] Step 6b: GET /api/v1/integrations/{{id}} works by both Mongo id and UUID")

        # 6c. Test connection
        res_test = await http.post(f"{BASE_URL}/integrations/{int_id}/test", headers=headers_a)
        assert res_test.status_code == 200
        print("[PASS] Step 6c: POST /api/v1/integrations/{id}/test succeeded")

        # 6d. UPDATE (PATCH)
        res_update = await http.patch(f"{BASE_URL}/integrations/{int_id}", json={"status": "Syncing"}, headers=headers_a)
        assert res_update.status_code == 200
        assert res_update.json()["status"] == "Syncing"
        # verify MongoDB reflected change
        updated_doc = integrations_coll.find_one({"_id": ObjectId(int_id)})
        assert updated_doc["status"] == "Syncing"
        print("[PASS] Step 6d: UPDATE (PATCH) /api/v1/integrations/{id} updated status in DB to 'Syncing'")

        # 6e. Test Disconnect
        res_disc = await http.post(f"{BASE_URL}/integrations/{int_id}/disconnect", headers=headers_a)
        assert res_disc.status_code == 200
        disc_doc = integrations_coll.find_one({"_id": ObjectId(int_id)})
        assert disc_doc["status"] == "Disconnected"
        print("[PASS] Step 6e: POST /api/v1/integrations/{id}/disconnect marked status 'Disconnected'")

        # 6f. DELETE
        res_del = await http.delete(f"{BASE_URL}/integrations/{int_id}", headers=headers_a)
        assert res_del.status_code == 200
        deleted_doc = integrations_coll.find_one({"_id": ObjectId(int_id)})
        assert deleted_doc is None, "Document still in DB after DELETE"
        res_get_del = await http.get(f"{BASE_URL}/integrations/{int_id}", headers=headers_a)
        assert res_get_del.status_code == 404
        print("[PASS] Step 6f: DELETE /api/v1/integrations/{id} completely removed integration from MongoDB")

        # Step 7: Test cross-tenant access
        int_2_id = created_data_2["id"]
        # Org B tries to GET Org A's integration
        res_cross_get = await http.get(f"{BASE_URL}/integrations/{int_2_id}", headers=headers_b)
        assert res_cross_get.status_code in [403, 404], f"Cross-tenant leak on GET: {res_cross_get.status_code}"
        
        # Org B tries to UPDATE Org A's integration
        res_cross_update = await http.patch(f"{BASE_URL}/integrations/{int_2_id}", json={"status": "Hacked"}, headers=headers_b)
        assert res_cross_update.status_code in [403, 404], f"Cross-tenant leak on UPDATE: {res_cross_update.status_code}"

        # Org B tries to DELETE Org A's integration
        res_cross_del = await http.delete(f"{BASE_URL}/integrations/{int_2_id}", headers=headers_b)
        assert res_cross_del.status_code in [403, 404], f"Cross-tenant leak on DELETE: {res_cross_del.status_code}"

        # Org B list must be empty or not contain Org A's integration
        res_list_b = await http.get(f"{BASE_URL}/integrations/", headers=headers_b)
        assert res_list_b.status_code == 200
        assert not any(i["id"] == int_2_id for i in res_list_b.json()), "Org A integration visible to Org B!"
        print(f"[PASS] Step 7: Cross-tenant access strictly blocked (GET/UPDATE/DELETE returned {res_cross_get.status_code}/404)")

        # Cleanup Org A's second integration
        await http.delete(f"{BASE_URL}/integrations/{int_2_id}", headers=headers_a)

    print("\n==================================================")
    print("ALL 7 VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_verification())
