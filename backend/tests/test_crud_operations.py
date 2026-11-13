import pytest
import pytest_asyncio
import os
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
from app.models.organization import Organization
from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.ai import HRPolicyDocument
from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.models.audit import AuditLog
from app.core.security import create_access_token, get_password_hash

CSV_CONTENT = (
    "employee_id,name,department,role,joining_date,experience,salary,performance_score,engagement_score,overtime,skills,promotion_history,manager_feedback,employment_status,attrition\n"
    "EMP_DEL1,Test One,Engineering,Software Engineer,2021-01-15,3.5,85000,4.2,4.5,5,Python;React,1,Great,Active,0\n"
    "EMP_DEL2,Test Two,Engineering,Senior Engineer,2019-03-10,5.0,110000,4.8,4.0,2,Java;AWS,2,Excellent,Active,0\n"
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[
            Organization, User, Employee, AttritionPrediction,
            Candidate, CandidateMatch, HRPolicyDocument,
            EmployeeFeedback, SentimentResult, AuditLog
        ]
    )

    await Employee.find_all().delete()
    await AttritionPrediction.find_all().delete()
    await Candidate.find_all().delete()
    await CandidateMatch.find_all().delete()
    await HRPolicyDocument.find_all().delete()
    await EmployeeFeedback.find_all().delete()
    await SentimentResult.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def test_org():
    org = Organization(
        name="CRUD Corp",
        slug="crud-corp",
        plan="enterprise",
        created_at=datetime.now(timezone.utc)
    )
    await org.insert()
    return org

@pytest_asyncio.fixture
async def hr_token(test_org):
    user = User(
        organization_id=str(test_org.id),
        email="hr@crudcorp.com",
        password_hash=get_password_hash("securepass123"),
        role="HR_MANAGER",
        full_name="HR Manager",
        created_at=datetime.now(timezone.utc)
    )
    await user.insert()
    return create_access_token(str(user.id))

@pytest.mark.asyncio
async def test_workforce_import_and_delete_single(hr_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {hr_token}"}

        # 1. Import CSV
        files = {"file": ("employees.csv", BytesIO(CSV_CONTENT.encode("utf-8")), "text/csv")}
        import_res = await ac.post("/api/v1/workforce/import", headers=headers, files=files)
        assert import_res.status_code == 200
        assert import_res.json()["imported_rows"] == 2

        # Verify count
        list_res = await ac.get("/api/v1/workforce/employees", headers=headers)
        assert len(list_res.json()) == 2

        # 2. Delete single employee EMP_DEL1
        del_res = await ac.delete("/api/v1/workforce/employees/EMP_DEL1", headers=headers)
        assert del_res.status_code == 200
        assert "deleted successfully" in del_res.json()["message"]

        # Verify remaining is 1
        list_res2 = await ac.get("/api/v1/workforce/employees", headers=headers)
        assert len(list_res2.json()) == 1
        assert list_res2.json()[0]["employee_id"] == "EMP_DEL2"

@pytest.mark.asyncio
async def test_workforce_clear_data(hr_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {hr_token}"}

        # Import
        files = {"file": ("employees.csv", BytesIO(CSV_CONTENT.encode("utf-8")), "text/csv")}
        await ac.post("/api/v1/workforce/import", headers=headers, files=files)

        # Clear data
        clear_res = await ac.delete("/api/v1/workforce/clear-data", headers=headers)
        assert clear_res.status_code == 200
        data = clear_res.json()
        assert data["count"] == 2

        # Verify empty
        list_res = await ac.get("/api/v1/workforce/employees", headers=headers)
        assert len(list_res.json()) == 0

@pytest.mark.asyncio
async def test_candidate_delete_and_clear_all(hr_token, test_org):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {hr_token}"}

        # Manually create mock candidate with dummy file
        upload_dir = "uploads/resumes"
        os.makedirs(upload_dir, exist_ok=True)
        dummy_file = f"test_resume_{test_org.id}.txt"
        dummy_path = os.path.join(upload_dir, dummy_file)
        with open(dummy_path, "w") as f:
            f.write("Resume content for testing")

        cand = Candidate(
            organization_id=str(test_org.id),
            candidate_id="CAND_TEST_99",
            name="Alice Test",
            email="alice@test.com",
            skills=["Python", "FastAPI"],
            experience=4,
            resume_file=dummy_file,
            raw_text="Resume content for testing",
            parsing_status="Completed"
        )
        await cand.insert()

        # Check candidate exists
        get_res = await ac.get("/api/v1/recruitment/candidates", headers=headers)
        assert len(get_res.json()) == 1

        # Delete single candidate
        del_res = await ac.delete("/api/v1/recruitment/candidates/CAND_TEST_99", headers=headers)
        assert del_res.status_code == 200
        assert not os.path.exists(dummy_path)  # physical file unlinked

        # Insert 2 candidates for clear all test
        cand1 = Candidate(organization_id=str(test_org.id), candidate_id="CAND_A", name="A", skills=[], experience=1, resume_file="", raw_text="", parsing_status="Completed")
        cand2 = Candidate(organization_id=str(test_org.id), candidate_id="CAND_B", name="B", skills=[], experience=2, resume_file="", raw_text="", parsing_status="Completed")
        await cand1.insert()
        await cand2.insert()

        # Clear all
        clear_res = await ac.delete("/api/v1/recruitment/candidates/actions/clear-all", headers=headers)
        assert clear_res.status_code == 200
        assert clear_res.json()["count"] == 2

        get_res2 = await ac.get("/api/v1/recruitment/candidates", headers=headers)
        assert len(get_res2.json()) == 0

@pytest.mark.asyncio
async def test_policy_document_delete(hr_token, test_org):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {hr_token}"}

        # Create policy document
        doc = HRPolicyDocument(
            organization_id=test_org,
            document_id="POL_TEST_1",
            title="Remote Work Policy",
            category="Workplace",
            content="Employees can work remotely 2 days a week.",
            chunks=["Employees can work remotely 2 days a week."]
        )
        await doc.insert()

        # Verify exists
        pol_res = await ac.get("/api/v1/ai/policies", headers=headers)
        assert len(pol_res.json()) == 1
        assert pol_res.json()[0]["document_id"] == "POL_TEST_1"

        # Delete policy
        del_res = await ac.delete("/api/v1/ai/policies/POL_TEST_1", headers=headers)
        assert del_res.status_code == 200
        assert "removed successfully" in del_res.json()["message"]

        # Verify policy list is now empty
        pol_res2 = await ac.get("/api/v1/ai/policies", headers=headers)
        assert len(pol_res2.json()) == 0

@pytest.mark.asyncio
async def test_sentiment_feedback_crud_and_clear_all(hr_token, test_org):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {hr_token}"}

        # 1. Create feedback
        fb_payload = {
            "department": "Engineering",
            "category": "WORKLOAD",
            "feedback_text": "Team workload is well balanced and sprint goals are realistic.",
            "source": "SURVEY"
        }
        create_res = await ac.post("/api/v1/sentiment/feedback", headers=headers, json=fb_payload)
        assert create_res.status_code == 200
        fb_data = create_res.json()
        assert fb_data["department"] == "Engineering"
        feedback_id = fb_data["feedback_id"]

        # 2. List feedback
        list_res = await ac.get("/api/v1/sentiment/feedback", headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1

        # 3. Delete single feedback
        del_res = await ac.delete(f"/api/v1/sentiment/feedback/{feedback_id}", headers=headers)
        assert del_res.status_code == 200
        assert "deleted successfully" in del_res.json()["message"]

        # Verify empty
        list_res2 = await ac.get("/api/v1/sentiment/feedback", headers=headers)
        assert list_res2.json()["total"] == 0

        # 4. Import feedback via CSV
        feedback_csv = (
            "feedback_text,department,category,source\n"
            "Great team culture and collaboration,Engineering,CULTURE,SURVEY\n"
            "Need more training opportunities,Sales,CAREER,SURVEY\n"
        )
        files = {"file": ("feedback.csv", BytesIO(feedback_csv.encode("utf-8")), "text/csv")}
        import_res = await ac.post("/api/v1/sentiment/feedback/import", headers=headers, files=files)
        assert import_res.status_code == 200
        assert import_res.json()["imported_count"] == 2

        # Verify count is 2
        list_res3 = await ac.get("/api/v1/sentiment/feedback", headers=headers)
        assert list_res3.json()["total"] == 2

        # 5. Clear all feedback
        clear_res = await ac.delete("/api/v1/sentiment/feedback/actions/clear-all", headers=headers)
        assert clear_res.status_code == 200
        assert clear_res.json()["count"] == 2

        # Verify count is 0
        list_res4 = await ac.get("/api/v1/sentiment/feedback", headers=headers)
        assert list_res4.json()["total"] == 0
