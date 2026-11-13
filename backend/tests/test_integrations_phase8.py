import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient

if not hasattr(AgnosticClient, "append_metadata"):
    setattr(AgnosticClient, "append_metadata", lambda self, *args, **kwargs: None)

from beanie import init_beanie
from app.main import app
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.audit import AuditLog
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath
from app.models.ai import AIChatConversation, HRPolicyDocument
from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.integrations.models.integration import Integration
from app.integrations.models.data_mapping import DataMapping
from app.integrations.models.sync_log import SyncLog
from app.core.security import create_access_token, get_password_hash

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[
            Organization, User, Employee, AttritionPrediction, Job, Candidate, CandidateMatch,
            AuditLog, Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath,
            AIChatConversation, HRPolicyDocument, EmployeeFeedback, SentimentResult,
            Integration, DataMapping, SyncLog
        ]
    )

    await SyncLog.find_all().delete()
    await DataMapping.find_all().delete()
    await Integration.find_all().delete()
    await AuditLog.find_all().delete()
    await Employee.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def test_data():
    # Org A
    org_a = Organization(name="Nexus Enterprise A")
    await org_a.insert()

    admin_a = User(
        organization_id=org_a,
        email="admin_a@nexus.com",
        password_hash=get_password_hash("pass"),
        role="ORGANIZATION_ADMIN",
        is_active=True
    )
    await admin_a.insert()

    hr_a = User(
        organization_id=org_a,
        email="hr_a@nexus.com",
        password_hash=get_password_hash("pass"),
        role="HR_MANAGER",
        is_active=True
    )
    await hr_a.insert()

    recruiter_a = User(
        organization_id=org_a,
        email="recruiter_a@nexus.com",
        password_hash=get_password_hash("pass"),
        role="RECRUITER",
        is_active=True
    )
    await recruiter_a.insert()

    # Org B
    org_b = Organization(name="OmniCorp B")
    await org_b.insert()

    admin_b = User(
        organization_id=org_b,
        email="admin_b@omni.com",
        password_hash=get_password_hash("pass"),
        role="ORGANIZATION_ADMIN",
        is_active=True
    )
    await admin_b.insert()

    token_admin_a = create_access_token(subject=str(admin_a.id))
    token_hr_a = create_access_token(subject=str(hr_a.id))
    token_recruiter_a = create_access_token(subject=str(recruiter_a.id))
    token_admin_b = create_access_token(subject=str(admin_b.id))

    return {
        "org_a": org_a,
        "org_b": org_b,
        "token_admin_a": token_admin_a,
        "token_hr_a": token_hr_a,
        "token_recruiter_a": token_recruiter_a,
        "token_admin_b": token_admin_b,
    }

@pytest.mark.asyncio
async def test_full_phase8_erp_hris_integration_flow(test_data):
    """
    Complete Phase 8 Integration Verification:
    1. Create ERP & HRIS integrations with auto-generated integration_id
    2. Connection test on both
    3. Sync ERP -> creates 100 employees
    4. Sync HRIS -> updates 100 existing employees (0 duplicates)
    5. Sync again -> 100 updated, total count stays 100
    6. Mappings CRUD & Sync Logs
    7. Disconnect and sync-block verification
    8. RBAC and Cross-tenant isolation
    9. Audit log verification
    """
    token_admin_a = test_data["token_admin_a"]
    token_hr_a = test_data["token_hr_a"]
    token_recruiter_a = test_data["token_recruiter_a"]
    token_admin_b = test_data["token_admin_b"]
    headers_admin_a = {"Authorization": f"Bearer {token_admin_a}"}
    headers_hr_a = {"Authorization": f"Bearer {token_hr_a}"}
    headers_recruiter_a = {"Authorization": f"Bearer {token_recruiter_a}"}
    headers_admin_b = {"Authorization": f"Bearer {token_admin_b}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Demo ERP Integration
        res_erp = await ac.post(
            "/api/v1/integrations",
            headers=headers_admin_a,
            json={"provider_name": "demo_erp", "provider_type": "DEMO_ERP"}
        )
        assert res_erp.status_code == 201, res_erp.text
        erp_data = res_erp.json()
        assert erp_data["provider_name"] == "demo_erp"
        assert erp_data["status"] == "Connected"
        erp_id = erp_data["integration_id"]
        assert erp_id.startswith("INT-")

        # 2. Create Demo HRIS Integration
        res_hris = await ac.post(
            "/api/v1/integrations",
            headers=headers_admin_a,
            json={"provider_name": "demo_hris", "provider_type": "DEMO_HRIS"}
        )
        assert res_hris.status_code == 201, res_hris.text
        hris_data = res_hris.json()
        hris_id = hris_data["integration_id"]
        assert hris_id.startswith("INT-")

        # 3. Test Connection on both
        test_erp = await ac.post(f"/api/v1/integrations/{erp_id}/test", headers=headers_admin_a)
        assert test_erp.status_code == 200, test_erp.text
        assert test_erp.json()["status"] == "SUCCESS"

        test_hris = await ac.post(f"/api/v1/integrations/{hris_id}/test", headers=headers_admin_a)
        assert test_hris.status_code == 200, test_hris.text

        # 4. Sync Demo ERP: 100 records fetched, 100 created, 0 updated, 0 failed
        sync_erp = await ac.post(f"/api/v1/integrations/{erp_id}/sync", headers=headers_admin_a)
        assert sync_erp.status_code == 200, sync_erp.text
        sync_erp_res = sync_erp.json()
        assert sync_erp_res["status"] == "SUCCESS"
        assert sync_erp_res["records_fetched"] == 100
        assert sync_erp_res["records_created"] == 100
        assert sync_erp_res["records_updated"] == 0
        assert sync_erp_res["records_failed"] == 0

        # Verify 100 employees in database for Org A
        org_a_employees = await Employee.find({"organization_id.$id": test_data["org_a"].id}).to_list()
        assert len(org_a_employees) == 100
        first_emp = next(e for e in org_a_employees if e.employee_id == "ERP001")
        assert "ERP Master Record" in first_emp.manager_feedback

        # 5. Sync Demo HRIS (HR_MANAGER can sync): updates 100 existing profiles, 0 created
        sync_hris = await ac.post(f"/api/v1/integrations/{hris_id}/sync", headers=headers_hr_a)
        assert sync_hris.status_code == 200, sync_hris.text
        sync_hris_res = sync_hris.json()
        assert sync_hris_res["status"] == "SUCCESS"
        assert sync_hris_res["records_fetched"] == 100
        assert sync_hris_res["records_created"] == 0
        assert sync_hris_res["records_updated"] == 100
        assert sync_hris_res["records_failed"] == 0

        # Verify NO duplicates: total employee count in DB is STILL exactly 100!
        org_a_employees_after = await Employee.find({"organization_id.$id": test_data["org_a"].id}).to_list()
        assert len(org_a_employees_after) == 100
        # Verify fields were updated from HRIS
        updated_first = next(e for e in org_a_employees_after if e.employee_id == "ERP001")
        assert "HRIS Talent Review" in updated_first.manager_feedback

        # 6. Re-run ERP sync: 100 updated, 0 created, total count remains 100
        sync_erp_again = await ac.post(f"/api/v1/integrations/{erp_id}/sync", headers=headers_admin_a)
        assert sync_erp_again.status_code == 200
        assert sync_erp_again.json()["records_created"] == 0
        assert sync_erp_again.json()["records_updated"] == 100
        count_final = await Employee.find({"organization_id.$id": test_data["org_a"].id}).count()
        assert count_final == 100

        # 7. Verify Data Mappings endpoints
        get_mappings = await ac.get(f"/api/v1/integrations/{erp_id}/mappings", headers=headers_admin_a)
        assert get_mappings.status_code == 200
        mappings = get_mappings.json()
        assert len(mappings) > 0  # Seeded defaults exist!

        # Add custom mapping
        add_map = await ac.post(
            f"/api/v1/integrations/{erp_id}/mappings",
            headers=headers_admin_a,
            json={"source_field": "custom_erp_col", "target_field": "custom_attr"}
        )
        assert add_map.status_code == 201
        map_id = add_map.json()["id"]

        # Update custom mapping
        upd_map = await ac.put(
            f"/api/v1/integrations/{erp_id}/mappings/{map_id}",
            headers=headers_admin_a,
            json={"source_field": "custom_erp_col_v2", "target_field": "custom_attr"}
        )
        assert upd_map.status_code == 200
        assert upd_map.json()["source_field"] == "custom_erp_col_v2"

        # Delete custom mapping
        del_map = await ac.delete(f"/api/v1/integrations/{erp_id}/mappings/{map_id}", headers=headers_admin_a)
        assert del_map.status_code == 200

        # 8. Verify Sync Logs endpoint
        logs_res = await ac.get(f"/api/v1/integrations/{erp_id}/sync-logs", headers=headers_admin_a)
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert len(logs) >= 2
        assert logs[0]["records_fetched"] == 100
        assert logs[0]["status"] == "SUCCESS"

        # 9. Disconnect integration & verify sync prevention
        disconn = await ac.post(f"/api/v1/integrations/{erp_id}/disconnect", headers=headers_admin_a)
        assert disconn.status_code == 200
        assert disconn.json()["status"] == "Disconnected"

        # Syncing a disconnected integration must fail
        sync_disconn = await ac.post(f"/api/v1/integrations/{erp_id}/sync", headers=headers_admin_a)
        assert sync_disconn.status_code == 400
        assert "disconnected" in sync_disconn.text.lower()

        # Connect back
        conn = await ac.post(f"/api/v1/integrations/{erp_id}/connect", headers=headers_admin_a)
        assert conn.status_code == 200
        assert conn.json()["status"] == "Connected"

        # 10. RBAC: Recruiter role must be strictly FORBIDDEN (403)
        res_recruiter_list = await ac.get("/api/v1/integrations", headers=headers_recruiter_a)
        assert res_recruiter_list.status_code == 403
        res_recruiter_sync = await ac.post(f"/api/v1/integrations/{erp_id}/sync", headers=headers_recruiter_a)
        assert res_recruiter_sync.status_code == 403

        # 11. Multi-Tenant Cross-Isolation: Org B cannot access Org A's integration
        org_b_get = await ac.get(f"/api/v1/integrations/{erp_id}", headers=headers_admin_b)
        assert org_b_get.status_code == 404  # Integration not found in Org B!

        org_b_sync = await ac.post(f"/api/v1/integrations/{erp_id}/sync", headers=headers_admin_b)
        assert org_b_sync.status_code == 404

        org_b_list = await ac.get("/api/v1/integrations", headers=headers_admin_b)
        assert org_b_list.status_code == 200
        assert len(org_b_list.json()) == 0  # Org B has 0 integrations!

        # Org B employee count remains 0
        org_b_emp_count = await Employee.find({"organization_id.$id": test_data["org_b"].id}).count()
        assert org_b_emp_count == 0

        # 12. Audit Logs: Verify AuditLog collection holds records for key actions
        audit_logs = await AuditLog.find().to_list()
        actions = {a.action for a in audit_logs}
        assert "INTEGRATION_CREATED" in actions
        assert "CONNECTION_TESTED" in actions
        assert "INTEGRATION_SYNCED" in actions
        assert "INTEGRATION_DISCONNECTED" in actions
