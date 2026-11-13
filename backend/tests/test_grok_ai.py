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
from app.core.security import create_access_token, get_password_hash
from app.services.ai.grok_client import grok_client
from app.services.ai.exceptions import AIRateLimitError

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[
            Organization, User, Employee, Job, Candidate, CandidateMatch,
            AttritionPrediction, AuditLog, Skill, RoleSkillRequirement,
            SkillGapAnalysis, CareerPath, AIChatConversation, HRPolicyDocument
        ]
    )

    await AIChatConversation.find_all().delete()
    await HRPolicyDocument.find_all().delete()
    await Employee.find_all().delete()
    await Job.find_all().delete()
    await Candidate.find_all().delete()
    await CandidateMatch.find_all().delete()
    await AttritionPrediction.find_all().delete()
    await User.find_all().delete()
    await Organization.find_all().delete()
    yield

@pytest_asyncio.fixture
async def setup_data():
    # Setup Org A
    org_a = Organization(name="Nexus Global")
    await org_a.insert()

    user_admin_a = User(
        organization_id=org_a,
        email="hr_admin@nexus.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_a.insert()

    user_recruiter_a = User(
        organization_id=org_a,
        email="recruiter@nexus.com",
        password_hash=get_password_hash("password"),
        role="RECRUITER"
    )
    await user_recruiter_a.insert()

    # Setup Org B
    org_b = Organization(name="Vortex Inc")
    await org_b.insert()

    user_admin_b = User(
        organization_id=org_b,
        email="admin@vortex.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_b.insert()

    from datetime import datetime, timezone
    # Employee in Org A
    emp_a = Employee(
        organization_id=org_a.to_ref(),
        employee_id="EMP-100",
        name="Sarah Connor",
        department="Engineering",
        role="Backend Developer",
        joining_date=datetime(2021, 6, 1, tzinfo=timezone.utc),
        experience=4.0,
        salary=105000,
        performance_score=4.5,
        engagement_score=3.2,
        overtime=12.0,
        skills="Python, FastAPI, MongoDB",
        promotion_history=1,
        manager_feedback="High output but working long hours",
        employment_status="Active",
        attrition=0
    )
    await emp_a.insert()

    # Attrition Prediction in Org A
    pred_a = AttritionPrediction(
        organization_id=org_a.to_ref(),
        employee_id="EMP-100",
        probability=0.78,
        risk_level="HIGH",
        top_factors={"overtime": 0.45, "engagement_score": -0.25}
    )
    await pred_a.insert()

    # Job & Candidate in Org A
    job_a = Job(
        organization_id=org_a.to_ref(),
        job_id="JOB-100",
        title="Senior Python Developer",
        description="Senior backend engineer needed",
        required_skills=["Python", "FastAPI", "Docker", "AWS"],
        minimum_experience=3.0,
        status="Open"
    )
    await job_a.insert()

    candidate_a = Candidate(
        organization_id=org_a.to_ref(),
        candidate_id="CAND-100",
        name="John Doe",
        email="john@example.com",
        phone="555-0199",
        resume_text="Senior Python and FastAPI developer with 5 years experience.",
        skills=["Python", "FastAPI"],
        experience=5.0
    )
    await candidate_a.insert()

    match_a = CandidateMatch(
        organization_id=org_a.to_ref(),
        candidate_id="CAND-100",
        job_id="JOB-100",
        match_score=82.5,
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Docker", "AWS"],
        experience_match="Match"
    )
    await match_a.insert()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "token_admin_a": create_access_token(str(user_admin_a.id)),
        "token_recruiter_a": create_access_token(str(user_recruiter_a.id)),
        "token_admin_b": create_access_token(str(user_admin_b.id)),
        "emp_a": emp_a,
        "job_a": job_a,
        "candidate_a": candidate_a
    }

@pytest.mark.asyncio
async def test_copilot_demo_mode_when_unconfigured(setup_data):
    """Verify Copilot gracefully returns demo response without crashing when XAI_API_KEY is empty."""
    data = setup_data
    token = data["token_admin_a"]

    with patch.object(grok_client, "is_configured", False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/copilot",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Which department has high attrition risk?"}
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["demo_mode"] is True
            assert "Demo Mode" in res_data["answer"]
            assert "Engineering" in res_data["answer"]
            assert len(res_data["conversation_id"]) > 0

@pytest.mark.asyncio
async def test_copilot_with_mocked_grok(setup_data):
    """Verify Copilot calls Grok with structured context and saves conversation."""
    data = setup_data
    token = data["token_admin_a"]

    mock_grok_response = "Based on verified organization analytics, Engineering exhibits the highest estimated attrition risk with 1 high-risk employee."

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_grok_response

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/copilot",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Which department has the highest attrition risk?"}
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["answer"] == mock_grok_response
            assert res_data["is_ai_assisted"] is True
            assert mock_chat.called

            # Verify prompt received verified data without leaking PII
            call_args = mock_chat.call_args[1]["messages"]
            system_context = next(m["content"] for m in call_args if "VERIFIED ORGANIZATION CONTEXT" in m["content"])
            assert "High Attrition Risk Count: 1" in system_context
            assert "Sarah Connor" not in system_context  # PII minimization!

@pytest.mark.asyncio
async def test_attrition_explanation_endpoint(setup_data):
    """Verify Grok explains model SHAP factors without inventing factors."""
    data = setup_data
    token = data["token_admin_a"]

    mock_explanation = "Estimated attrition risk is high. The main contributing factors identified by the model are overtime hours and lower engagement score."

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_explanation

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/explain/attrition",
                headers={"Authorization": f"Bearer {token}"},
                json={"employee_id": "EMP-100"}
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["risk_level"] == "HIGH"
            assert res_data["risk_score"] == 0.78
            assert res_data["ai_explanation"] == mock_explanation
            assert res_data["is_ai_assisted"] is True

@pytest.mark.asyncio
async def test_career_recommendation_endpoint(setup_data):
    """Verify Grok produces structured JSON development plan with milestones."""
    data = setup_data
    token = data["token_admin_a"]

    mock_career_json = {
        "summary": "Targeted progression plan to bridge Docker and AWS competencies.",
        "development_areas": [
            {
                "skill": "Docker",
                "reason": "Docker is required for Senior Backend Developer",
                "recommended_action": "Complete Docker containerization project"
            },
            {
                "skill": "AWS",
                "reason": "AWS cloud knowledge is preferred for role",
                "recommended_action": "Deploy FastAPI service on AWS ECS"
            }
        ],
        "milestones": [
            "Milestone 1: Containerize backend with Docker",
            "Milestone 2: Deploy to AWS ECS",
            "Milestone 3: Manager review"
        ]
    }

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_json", new_callable=AsyncMock) as mock_json:
        mock_json.return_value = mock_career_json

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/explain/career",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "employee_id": "EMP-100",
                    "target_role": "Senior Backend Developer"
                }
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["target_role"] == "Senior Backend Developer"
            assert len(res_data["development_areas"]) == 2
            assert "guaranteed promotion" in res_data["disclaimer"].lower()

@pytest.mark.asyncio
async def test_recruitment_explanation_endpoint(setup_data):
    """Verify Grok explains candidate match results."""
    data = setup_data
    token = data["token_recruiter_a"]

    mock_match_explanation = "Candidate has strong alignment with Python and FastAPI requirements and satisfies the experience requirement. Docker and AWS are the primary missing skills."

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_match_explanation

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/explain/recruitment",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "candidate_id": "CAND-100",
                    "job_id": "JOB-100"
                }
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["match_score"] == 82.5
            assert "Python" in res_data["matched_skills"]
            assert res_data["ai_explanation"] == mock_match_explanation

@pytest.mark.asyncio
async def test_sentiment_summary_endpoint(setup_data):
    """Verify aggregated sentiment summary generation without PII."""
    data = setup_data
    token = data["token_admin_a"]

    mock_summary = "Engineering feedback reflects strong performance and overall engagement, though elevated overtime in some teams warrants workload balancing."

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_summary

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/summarize/sentiment",
                headers={"Authorization": f"Bearer {token}"},
                json={"department": "Engineering"}
            )
            assert res.status_code == 200, res.text
            res_data = res.json()
            assert res_data["total_feedbacks"] >= 1
            assert res_data["ai_summary"] == mock_summary

@pytest.mark.asyncio
async def test_policy_rag_upload_and_query(setup_data):
    """Verify uploading an HR policy, chunking, and querying with Grok."""
    data = setup_data
    token = data["token_admin_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload policy
        res_upload = await ac.post(
            "/api/v1/ai/policies/upload",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Maternity & Parental Leave Policy 2026",
                "category": "Leave & Benefits",
                "content": "All full-time employees are entitled to 16 weeks of fully paid maternity leave following 6 months of continuous service. Paternity leave provides 4 weeks of fully paid leave."
            }
        )
        assert res_upload.status_code == 200, res_upload.text
        assert res_upload.json()["chunk_count"] >= 1

        # 2. Query policy with Grok mocked
        mock_rag_answer = "Under the Maternity & Parental Leave Policy 2026, full-time employees are entitled to 16 weeks of fully paid maternity leave after 6 months of continuous service."
        with patch.object(grok_client, "is_configured", True), \
             patch.object(grok_client, "generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_rag_answer

            res_query = await ac.post(
                "/api/v1/ai/policies/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is the maternity leave entitlement?"}
            )
            assert res_query.status_code == 200, res_query.text
            query_json = res_query.json()
            assert "16 weeks" in query_json["answer"]
            assert "Maternity & Parental Leave Policy 2026" in query_json["sources"]

@pytest.mark.asyncio
async def test_rag_and_copilot_tenant_isolation(setup_data):
    """Verify Org B cannot retrieve or search Org A's policies or conversations."""
    data = setup_data
    token_a = data["token_admin_a"]
    token_b = data["token_admin_b"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Org A uploads confidential policy
        await ac.post(
            "/api/v1/ai/policies/upload",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "title": "Confidential Nexus M&A Retention Bonus Policy",
                "category": "Executive",
                "content": "Eligible executives receive a 25% retention bonus payable in December 2026."
            }
        )

        # 2. Org B queries for retention bonus
        res_b = await ac.post(
            "/api/v1/ai/policies/query",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"query": "What is the retention bonus policy?"}
        )
        assert res_b.status_code == 200
        # Org B must receive not found!
        assert "couldn't find this information" in res_b.json()["answer"].lower()
        assert len(res_b.json()["sources"]) == 0

@pytest.mark.asyncio
async def test_rate_limit_error_handling(setup_data):
    """Verify rate limit errors from Grok are handled gracefully with clean user messages."""
    data = setup_data
    token = data["token_admin_a"]

    with patch.object(grok_client, "is_configured", True), \
         patch.object(grok_client, "generate_chat", side_effect=AIRateLimitError("High traffic")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                "/api/v1/ai/copilot",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Give me a summary"}
            )
            # Must return 500 with friendly message, not leaking secrets
            assert res.status_code == 500
            assert "traffic" in res.json()["detail"].lower() or "rate limit" in res.json()["detail"].lower()
