import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient

if not hasattr(AgnosticClient, "append_metadata"):
    setattr(AgnosticClient, "append_metadata", lambda self, *args, **kwargs: None)

from beanie import init_beanie
from app.main import app
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.audit import AuditLog
from app.integrations.models.integration import Integration
from app.integrations.models.data_mapping import DataMapping
from app.integrations.models.sync_log import SyncLog
from app.core.security import create_access_token, get_password_hash

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[Organization, User, AuditLog, Integration, DataMapping, SyncLog]
    )

    await Integration.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def setup_tenants():
    org_a = Organization(name="Organization A")
    await org_a.insert()
    user_a = User(
        organization_id=org_a,
        email="admin_a@orga.com",
        password_hash=get_password_hash("pass123"),
        role="ORGANIZATION_ADMIN"
    )
    await user_a.insert()

    org_b = Organization(name="Organization B")
    await org_b.insert()
    user_b = User(
        organization_id=org_b,
        email="admin_b@orgb.com",
        password_hash=get_password_hash("pass123"),
        role="ORGANIZATION_ADMIN"
    )
    await user_b.insert()

    return {
        "org_a": org_a,
        "user_a": user_a,
        "token_a": create_access_token(str(user_a.id)),
        "org_b": org_b,
        "user_b": user_b,
        "token_b": create_access_token(str(user_b.id))
    }

@pytest.mark.asyncio
async def test_integration_crud_and_isolation(setup_tenants):
    data = setup_tenants
    token_a = data["token_a"]
    token_b = data["token_b"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Integration (Org A)
        payload = {
            "provider_name": "demo_hris",
            "provider_type": "hris",
            "credentials": {"api_key": "pytest-key-1"}
        }
        res_create = await ac.post("/api/v1/integrations/", json=payload, headers={"Authorization": f"Bearer {token_a}"})
        assert res_create.status_code == 200, f"Failed create: {res_create.text}"
        res_data = res_create.json()
        int_id = res_data["id"]
        integration_uuid = res_data.get("integration_id")

        assert int_id is not None
        assert integration_uuid is not None and len(integration_uuid) > 10

        # 2. Verify in MongoDB
        db_doc = await Integration.find_one({"integration_id": integration_uuid})
        assert db_doc is not None
        assert db_doc.provider_name == "demo_hris"
        assert db_doc.status == "Connected"

        # 3. Create Second Integration and verify unique ID
        res_create_2 = await ac.post("/api/v1/integrations/", json={
            "provider_name": "demo_erp",
            "provider_type": "erp",
            "credentials": {}
        }, headers={"Authorization": f"Bearer {token_a}"})
        assert res_create_2.status_code == 200
        int_2_uuid = res_create_2.json().get("integration_id")
        assert int_2_uuid != integration_uuid

        # 4. List Integrations (Org A)
        res_list_a = await ac.get("/api/v1/integrations/", headers={"Authorization": f"Bearer {token_a}"})
        assert res_list_a.status_code == 200
        assert len(res_list_a.json()) == 2

        # 5. Get Single (by Mongo ID and by UUID)
        res_get_by_id = await ac.get(f"/api/v1/integrations/{int_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_get_by_id.status_code == 200
        res_get_by_uuid = await ac.get(f"/api/v1/integrations/{integration_uuid}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_get_by_uuid.status_code == 200
        assert res_get_by_id.json()["id"] == res_get_by_uuid.json()["id"]

        # 6. Update (PATCH)
        res_update = await ac.patch(f"/api/v1/integrations/{int_id}", json={"status": "Syncing"}, headers={"Authorization": f"Bearer {token_a}"})
        assert res_update.status_code == 200
        assert res_update.json()["status"] == "Syncing"

        # 7. Disconnect
        res_disc = await ac.post(f"/api/v1/integrations/{int_id}/disconnect", headers={"Authorization": f"Bearer {token_a}"})
        assert res_disc.status_code == 200

        # 8. Cross-Tenant Isolation: Org B cannot see, read, update, or delete Org A's integration
        res_list_b = await ac.get("/api/v1/integrations/", headers={"Authorization": f"Bearer {token_b}"})
        assert res_list_b.status_code == 200
        assert len(res_list_b.json()) == 0

        res_cross_get = await ac.get(f"/api/v1/integrations/{int_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_cross_get.status_code == 404

        res_cross_update = await ac.patch(f"/api/v1/integrations/{int_id}", json={"status": "Hacked"}, headers={"Authorization": f"Bearer {token_b}"})
        assert res_cross_update.status_code == 404

        res_cross_del = await ac.delete(f"/api/v1/integrations/{int_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_cross_del.status_code == 404

        # 9. Delete Integration (Org A)
        res_del = await ac.delete(f"/api/v1/integrations/{int_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_del.status_code == 200
        check_del = await ac.get(f"/api/v1/integrations/{int_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert check_del.status_code == 404
