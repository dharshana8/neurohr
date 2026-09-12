import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
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
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath
from app.models.ai import AIChatConversation, HRPolicyDocument
from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.core.security import create_access_token, get_password_hash
from app.intelligence.services.sentiment_service import SentimentAnalysisService, get_org_id
from app.services.ai.grok_client import grok_client


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[
            Organization, User, Employee, Job, Candidate, CandidateMatch,
            AttritionPrediction, AuditLog, Skill, RoleSkillRequirement,
            SkillGapAnalysis, CareerPath, AIChatConversation, HRPolicyDocument,
            EmployeeFeedback, SentimentResult
        ]
    )

    await EmployeeFeedback.find_all().delete()
    await SentimentResult.find_all().delete()
    await Skill.find_all().delete()
    await RoleSkillRequirement.find_all().delete()
    await SkillGapAnalysis.find_all().delete()
    await CareerPath.find_all().delete()
    await Employee.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    await AuditLog.find_all().delete()
    yield


@pytest_asyncio.fixture
async def setup_data():
    # Setup Org A
    org_a = Organization(name="Acme Corporation")
    await org_a.insert()

    user_admin_a = User(
        organization_id=org_a,
        email="admin@acme.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_a.insert()

    user_hr_mgr_a = User(
        organization_id=org_a,
        email="hrmanager@acme.com",
        password_hash=get_password_hash("password"),
        role="HR_MANAGER"
    )
    await user_hr_mgr_a.insert()

    user_analyst_a = User(
        organization_id=org_a,
        email="analyst@acme.com",
        password_hash=get_password_hash("password"),
        role="HR_ANALYST"
    )
    await user_analyst_a.insert()

    user_recruiter_a = User(
        organization_id=org_a,
        email="recruiter@acme.com",
        password_hash=get_password_hash("password"),
        role="RECRUITER"
    )
    await user_recruiter_a.insert()

    # Setup Org B
    org_b = Organization(name="Beta Industries")
    await org_b.insert()

    user_admin_b = User(
        organization_id=org_b,
        email="admin@beta.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_b.insert()

    # Platform Admin (Global)
    user_platform_admin = User(
        organization_id=None,
        email="super@neurohr.com",
        password_hash=get_password_hash("password"),
        role="PLATFORM_ADMIN"
    )
    await user_platform_admin.insert()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "token_admin_a": create_access_token(str(user_admin_a.id)),
        "token_hr_a": create_access_token(str(user_hr_mgr_a.id)),
        "token_analyst_a": create_access_token(str(user_analyst_a.id)),
        "token_recruiter_a": create_access_token(str(user_recruiter_a.id)),
        "token_admin_b": create_access_token(str(user_admin_b.id)),
        "token_platform": create_access_token(str(user_platform_admin.id))
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. NLP Sentiment Classification & Scoring Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_nlp_sentiment_service_deterministic():
    """Verify local VADER NLP classifier delivers reproducible classification and normalized scores."""
    pos_res = SentimentAnalysisService.analyze_text("I love working here! The team culture is amazingly supportive and rewarding.")
    assert pos_res["sentiment"] == "POSITIVE"
    assert pos_res["sentiment_score"]["compound"] >= 0.05
    assert pos_res["model_name"] == "vader-sentiment"
    assert pos_res["model_version"] == "3.3.2"

    neg_res = SentimentAnalysisService.analyze_text("The excessive workload and micromanagement is causing terrible burnout.")
    assert neg_res["sentiment"] == "NEGATIVE"
    assert neg_res["sentiment_score"]["compound"] <= -0.05

    neu_res = SentimentAnalysisService.analyze_text("We completed our weekly status meeting at 10 AM.")
    assert neu_res["sentiment"] == "NEUTRAL"
    assert -0.05 < neu_res["sentiment_score"]["compound"] < 0.05


# ─────────────────────────────────────────────────────────────────────────────
# 2. Feedback CRUD Operations & Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feedback_crud_and_validation(setup_data):
    data = setup_data
    token_hr = data["token_hr_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Validation test: empty text
        res_empty = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_hr}"},
            json={"department": "Engineering", "category": "WORKLOAD", "feedback_text": "   "}
        )
        assert res_empty.status_code == 400

        # Create valid feedback
        res_create = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_hr}"},
            json={
                "department": "Engineering",
                "category": "CULTURE",
                "feedback_text": "Collaborative atmosphere with great mentorship across squads.",
                "employee_id": "EMP-001",
                "source": "SURVEY"
            }
        )
        assert res_create.status_code == 200, res_create.text
        fb_data = res_create.json()
        fid = fb_data["feedback_id"]
        assert fb_data["department"] == "Engineering"
        assert fb_data["sentiment_result"] is not None
        assert fb_data["sentiment_result"]["sentiment"] == "POSITIVE"

        # List feedback
        res_list = await ac.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_hr}"}
        )
        assert res_list.status_code == 200
        list_data = res_list.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["feedback_id"] == fid

        # Get feedback by id
        res_get = await ac.get(
            f"/api/v1/feedback/{fid}",
            headers={"Authorization": f"Bearer {token_hr}"}
        )
        assert res_get.status_code == 200
        assert res_get.json()["feedback_id"] == fid

        # Update feedback with new text -> triggers re-analysis
        res_update = await ac.put(
            f"/api/v1/feedback/{fid}",
            headers={"Authorization": f"Bearer {token_hr}"},
            json={"feedback_text": "Management communication is terrible and stressful."}
        )
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["sentiment_result"]["sentiment"] == "NEGATIVE"

        # Delete feedback
        res_del = await ac.delete(
            f"/api/v1/feedback/{fid}",
            headers={"Authorization": f"Bearer {token_hr}"}
        )
        assert res_del.status_code == 200

        # Verify deletion
        res_verify = await ac.get(
            f"/api/v1/feedback/{fid}",
            headers={"Authorization": f"Bearer {token_hr}"}
        )
        assert res_verify.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 3. Batch Analysis & Department/Trend Aggregations
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_analysis_and_analytics(setup_data):
    data = setup_data
    token_admin = data["token_admin_a"]
    token_analyst = data["token_analyst_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create 3 feedbacks
        f1 = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"department": "Engineering", "category": "CULTURE", "feedback_text": "Amazing peers and supportive environment."}
        )
        f2 = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"department": "Engineering", "category": "WORKLOAD", "feedback_text": "Excessive workload and burnout on projects."}
        )
        f3 = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"department": "Sales", "category": "COMPENSATION", "feedback_text": "Fair compensation and good commissions."}
        )
        assert f1.status_code == 200 and f2.status_code == 200 and f3.status_code == 200

        # Test Batch Analyze All
        res_batch = await ac.post(
            "/api/v1/sentiment/analyze-all?force=true",
            headers={"Authorization": f"Bearer {token_analyst}"}
        )
        assert res_batch.status_code == 200
        batch_data = res_batch.json()
        assert batch_data["total_evaluated"] == 3
        assert batch_data["analyzed_count"] == 3

        # Test Department Sentiment Aggregation
        res_dept = await ac.get(
            "/api/v1/sentiment/department",
            headers={"Authorization": f"Bearer {token_analyst}"}
        )
        assert res_dept.status_code == 200
        dept_data = res_dept.json()
        assert dept_data["total_feedback"] == 3
        eng_dept = next((d for d in dept_data["departments"] if d["department"] == "Engineering"), None)
        assert eng_dept is not None
        assert eng_dept["total_feedback"] == 2
        assert eng_dept["positive_count"] == 1
        assert eng_dept["negative_count"] == 1

        # Test Trends
        res_trends = await ac.get(
            "/api/v1/sentiment/trends",
            headers={"Authorization": f"Bearer {token_analyst}"}
        )
        assert res_trends.status_code == 200
        trend_data = res_trends.json()
        assert len(trend_data["trends"]) >= 1

        # Test Themes
        res_themes = await ac.get(
            "/api/v1/sentiment/themes",
            headers={"Authorization": f"Bearer {token_analyst}"}
        )
        assert res_themes.status_code == 200
        theme_data = res_themes.json()
        assert len(theme_data["themes"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 4. Grok AI Executive Insight Generation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grok_ai_insight_generation(setup_data):
    data = setup_data
    token_admin = data["token_admin_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"department": "Engineering", "category": "WORKLOAD", "feedback_text": "Workload is very heavy and demands better pacing."}
        )

        mock_insight = "Workplace sentiment highlights that engineering workload is currently the primary challenge requiring attention."

        with patch.object(grok_client, "is_configured", True), \
             patch.object(grok_client, "generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_insight

            res_ai = await ac.post(
                "/api/v1/sentiment/insight",
                headers={"Authorization": f"Bearer {token_admin}"},
                json={"department": "Engineering"}
            )
            assert res_ai.status_code == 200
            ai_data = res_ai.json()
            assert ai_data["insight"] == mock_insight
            assert ai_data["is_ai_assisted"] is True
            assert "Workload" in ai_data["top_themes"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. Strict Multi-Tenant Isolation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sentiment_multi_tenant_isolation(setup_data):
    data = setup_data
    token_admin_a = data["token_admin_a"]
    token_admin_b = data["token_admin_b"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create feedback in Org A
        res_a = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin_a}"},
            json={"department": "Product", "category": "CULTURE", "feedback_text": "Secret project feedback for Org A only."}
        )
        assert res_a.status_code == 200
        fb_id_a = res_a.json()["feedback_id"]

        # Org B lists feedbacks -> must NOT see Org A feedback
        res_list_b = await ac.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin_b}"}
        )
        assert res_list_b.status_code == 200
        items_b = res_list_b.json()["items"]
        assert all(item["feedback_id"] != fb_id_a for item in items_b)

        # Org B cannot get Org A feedback by id -> 404
        res_get_b = await ac.get(
            f"/api/v1/feedback/{fb_id_a}",
            headers={"Authorization": f"Bearer {token_admin_b}"}
        )
        assert res_get_b.status_code == 404

        # Org B cannot analyze Org A feedback -> 404
        res_analyze_b = await ac.post(
            f"/api/v1/sentiment/analyze/{fb_id_a}",
            headers={"Authorization": f"Bearer {token_admin_b}"}
        )
        assert res_analyze_b.status_code == 404

        # Org B department analytics shows zero
        res_dept_b = await ac.get(
            "/api/v1/sentiment/department",
            headers={"Authorization": f"Bearer {token_admin_b}"}
        )
        assert res_dept_b.status_code == 200
        assert res_dept_b.json()["total_feedback"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Strict RBAC & Privacy Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sentiment_rbac_and_privacy(setup_data):
    data = setup_data
    token_admin_a = data["token_admin_a"]
    token_analyst_a = data["token_analyst_a"]
    token_recruiter = data["token_recruiter_a"]
    token_platform = data["token_platform"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Recruiter is strictly blocked from feedback and sentiment endpoints (403)
        res_recruiter_fb = await ac.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_recruiter}"}
        )
        assert res_recruiter_fb.status_code == 403

        res_recruiter_dept = await ac.get(
            "/api/v1/sentiment/department",
            headers={"Authorization": f"Bearer {token_recruiter}"}
        )
        assert res_recruiter_dept.status_code == 403

        # 2. Platform Admin cannot access organization feedback (403)
        res_platform_fb = await ac.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_platform}"}
        )
        assert res_platform_fb.status_code == 403

        # 3. Create feedback with explicit employee_id as Organization Admin
        res_create = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_admin_a}"},
            json={
                "department": "HR",
                "category": "BENEFITS",
                "feedback_text": "Good health insurance coverage.",
                "employee_id": "EMP-SECRET-999"
            }
        )
        assert res_create.status_code == 200
        created_id = res_create.json()["feedback_id"]

        # 4. HR Analyst can view feedback, but employee_id MUST be masked/None for privacy
        res_analyst_list = await ac.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_analyst_a}"}
        )
        assert res_analyst_list.status_code == 200
        analyst_fb = next((item for item in res_analyst_list.json()["items"] if item["feedback_id"] == created_id), None)
        assert analyst_fb is not None
        assert analyst_fb["employee_id"] is None  # Masked for analyst role

        # 5. HR Analyst cannot mutate or delete feedback (403)
        res_analyst_mutate = await ac.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token_analyst_a}"},
            json={"department": "HR", "category": "BENEFITS", "feedback_text": "Test mutate"}
        )
        assert res_analyst_mutate.status_code == 403
