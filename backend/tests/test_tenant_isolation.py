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
from app.models.employee import Employee
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.attrition import AttritionPrediction
from app.models.audit import AuditLog
from app.core.security import create_access_token, get_password_hash

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[Organization, User, Employee, Job, Candidate, CandidateMatch, AttritionPrediction, AuditLog]
    )

    await Employee.find_all().delete()
    await Job.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def setup_organizations():
    # Setup Org A
    org_a = Organization(name="Organization A")
    await org_a.insert()
    user_a = User(
        organization_id=org_a,
        email="user_a@orga.com",
        password_hash=get_password_hash("pass"),
        role="RECRUITER"
    )
    await user_a.insert()

    # Setup Org B
    org_b = Organization(name="Organization B")
    await org_b.insert()
    user_b = User(
        organization_id=org_b,
        email="user_b@orgb.com",
        password_hash=get_password_hash("pass"),
        role="RECRUITER"
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
async def test_employee_isolation(setup_organizations):
    data = setup_organizations
    org_a, token_a = data["org_a"], data["token_a"]
    org_b, token_b = data["org_b"], data["token_b"]

    # Manually seed employees
    emp_a = Employee(
        organization_id=org_a.to_ref(),
        employee_id="EMP-A",
        name="Alice A",
        department="Engineering",
        role="Developer",
        salary=100000,
        performance_score=4.5,
        engagement_score=4.2,
        projects_handled=5,
        years_at_company=2,
        remote_work_frequency="Always",
        joining_date="2021-01-01",
        experience=5.0,
        overtime=10.5,
        skills="Python, SQL",
        promotion_history=1,
        manager_feedback="Good",
        employment_status="Active",
        attrition=0
    )
    await emp_a.insert()

    emp_b = Employee(
        organization_id=org_b.to_ref(),
        employee_id="EMP-B",
        name="Bob B",
        department="Marketing",
        role="Manager",
        salary=90000,
        performance_score=4.0,
        engagement_score=3.8,
        projects_handled=3,
        years_at_company=1,
        remote_work_frequency="Never",
        joining_date="2022-01-01",
        experience=3.0,
        overtime=0.0,
        skills="SEO",
        promotion_history=0,
        manager_feedback="Good",
        employment_status="Active",
        attrition=0
    )
    await emp_b.insert()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Org A requests employees
        res_a = await ac.get("/api/v1/workforce/employees", headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == 200
        emps_a = res_a.json()
        assert len(emps_a) == 1
        assert emps_a[0]["employee_id"] == "EMP-A"

        # Org B requests employees
        res_b = await ac.get("/api/v1/workforce/employees", headers={"Authorization": f"Bearer {token_b}"})
        assert res_b.status_code == 200
        emps_b = res_b.json()
        assert len(emps_b) == 1
        assert emps_b[0]["employee_id"] == "EMP-B"

        # Org A tries to access Org B's employee directly
        res_a_direct = await ac.get(f"/api/v1/workforce/employees/EMP-B", headers={"Authorization": f"Bearer {token_a}"})
        assert res_a_direct.status_code == 404

@pytest.mark.asyncio
async def test_job_isolation(setup_organizations):
    data = setup_organizations
    token_a = data["token_a"]
    token_b = data["token_b"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A creates a job
        job_payload = {
            "title": "Org A Secret Role",
            "description": "Secret",
            "required_skills": ["Stealth"],
            "minimum_experience": 5,
            "qualification": "Any",
            "location": "Remote",
            "employment_type": "Full Time",
            "status": "Open"
        }
        res_job_a = await ac.post("/api/v1/recruitment/jobs", json=job_payload, headers={"Authorization": f"Bearer {token_a}"})
        assert res_job_a.status_code == 200
        job_id_a = res_job_a.json()["job_id"]

        # User B lists jobs
        res_list_b = await ac.get("/api/v1/recruitment/jobs", headers={"Authorization": f"Bearer {token_b}"})
        assert len(res_list_b.json()) == 0

        # User B tries to access Job A directly
        res_get_b = await ac.get(f"/api/v1/recruitment/jobs/{job_id_a}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_get_b.status_code == 404
