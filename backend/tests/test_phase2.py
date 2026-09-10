import pytest
import pytest_asyncio
import asyncio
from io import BytesIO
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient

if not hasattr(AgnosticClient, "append_metadata"):
    setattr(AgnosticClient, "append_metadata", lambda self, *args, **kwargs: None)

from beanie import init_beanie
from app.main import app
from app.core.config import settings
from app.core.database import init_db
from app.models.organization import Organization
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.core.security import create_access_token, get_password_hash

VALID_CSV_CONTENT = (
    "employee_id,name,department,role,joining_date,experience,salary,performance_score,engagement_score,overtime,skills,promotion_history,manager_feedback,employment_status,attrition\n"
    "EMP001,John Doe,Engineering,Software Engineer,2021-01-15,3.5,85000,4.2,4.5,5,Python;React,1,Great performer,Active,0\n"
    "EMP002,Jane Smith,Engineering,Senior Engineer,2019-03-10,5.0,110000,4.8,4.0,2,Java;AWS,2,Excellent leadership,Active,0\n"
)

INVALID_CSV_CONTENT = (
    "employee_id,name,department,role,joining_date,experience,salary,performance_score,engagement_score,overtime,skills,promotion_history,manager_feedback,employment_status,attrition\n"
    "EMP003,Bob Wilson,Sales,Account Executive,2022-06-01,1.5,60000,INVALID_SCORE,2.1,15,Salesforce,0,Struggling,Active,1\n"
)

MISSING_COL_CSV_CONTENT = (
    "employee_id,name,role,joining_date\n"
    "EMP004,Alice Brown,HR Manager,2018-11-20\n"
)

DUPLICATE_ID_CSV_CONTENT = (
    "employee_id,name,department,role,joining_date,experience,salary,performance_score,engagement_score,overtime,skills,promotion_history,manager_feedback,employment_status,attrition\n"
    "EMP001,John Doe,Engineering,Software Engineer,2021-01-15,3.5,85000,4.2,4.5,5,Python,1,Good,Active,0\n"
    "EMP001,John Duplicate,Engineering,Software Engineer,2021-01-15,3.5,85000,4.2,4.5,5,Python,1,Good,Active,0\n"
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[Organization, User, Employee, AttritionPrediction]
    )

    await Employee.find_all().delete()
    await AttritionPrediction.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def test_org():
    org = Organization(name="Test Corp", slug="test-corp")
    await org.insert()
    return org

@pytest_asyncio.fixture
async def test_user(test_org):
    user = User(
        organization_id=test_org,
        email="admin@testcorp.com",
        password_hash=get_password_hash("password123"),
        role="Admin"
    )
    await user.insert()
    return user

@pytest_asyncio.fixture
async def auth_headers(test_user):
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_1_empty_database(auth_headers):
    """9. Empty database behavior"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/workforce/employees", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

        stats_res = await ac.get("/api/v1/workforce/stats", headers=auth_headers)
        assert stats_res.status_code == 200
        assert stats_res.json()["total_employees"] == 0

@pytest.mark.asyncio
async def test_2_unauthorized_access():
    """10. Unauthorized access check"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/workforce/employees")
        assert res.status_code in [401, 403]

@pytest.mark.asyncio
async def test_3_csv_upload_success(auth_headers):
    """1. CSV upload success"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("employees.csv", BytesIO(VALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        res = await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 2
        assert data["imported_rows"] == 2
        assert len(data["errors"]) == 0

@pytest.mark.asyncio
async def test_4_invalid_csv_data(auth_headers):
    """2. Invalid CSV handling"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("invalid.csv", BytesIO(INVALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        res = await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["invalid_rows"] == 1
        assert len(data["errors"]) > 0
        assert "Invalid performance_score" in data["errors"][0]

@pytest.mark.asyncio
async def test_5_missing_required_column(auth_headers):
    """3. Missing required column check"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("missing.csv", BytesIO(MISSING_COL_CSV_CONTENT.encode("utf-8")), "text/csv")}
        res = await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)
        assert res.status_code == 400
        assert "Missing required CSV columns" in res.json()["detail"]

@pytest.mark.asyncio
async def test_6_duplicate_employee_id(auth_headers):
    """4. Duplicate employee ID detection"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("dup.csv", BytesIO(DUPLICATE_ID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        res = await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 1
        assert any("Duplicate employee_id" in err for err in data["errors"])

@pytest.mark.asyncio
async def test_7_employee_retrieval(auth_headers):
    """5. Employee directory retrieval"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("employees.csv", BytesIO(VALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)

        res = await ac.get("/api/v1/workforce/employees", headers=auth_headers)
        assert res.status_code == 200
        emps = res.json()
        assert len(emps) == 2
        assert emps[0]["employee_id"] == "EMP001"

@pytest.mark.asyncio
async def test_8_organization_isolation(auth_headers, test_org):
    """6. Multi-tenant Organization isolation"""
    org2 = Organization(name="Other Corp", slug="other-corp")
    await org2.insert()
    user2 = User(organization_id=org2, email="admin2@othercorp.com", password_hash=get_password_hash("pass"), role="Admin")
    await user2.insert()
    token2 = create_access_token(str(user2.id))
    headers2 = {"Authorization": f"Bearer {token2}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Import to Org 1
        files = {"file": ("employees.csv", BytesIO(VALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)

        # Org 2 requests employees -> should be empty
        res2 = await ac.get("/api/v1/workforce/employees", headers=headers2)
        assert res2.status_code == 200
        assert res2.json() == []

@pytest.mark.asyncio
async def test_9_single_prediction(auth_headers):
    """7. Single attrition prediction"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("employees.csv", BytesIO(VALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)

        res = await ac.post("/api/v1/attrition/predict/EMP001", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["employee_id"] == "EMP001"
        assert "probability" in data
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert data["model_version"] == "demo-v1"

@pytest.mark.asyncio
async def test_10_bulk_prediction(auth_headers):
    """8. Bulk attrition prediction"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("employees.csv", BytesIO(VALID_CSV_CONTENT.encode("utf-8")), "text/csv")}
        await ac.post("/api/v1/workforce/import", headers=auth_headers, files=files)

        res = await ac.post("/api/v1/attrition/predict-all", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert (data["high"] + data["medium"] + data["low"]) == 2
