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
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath
from app.core.security import create_access_token, get_password_hash

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client["neurohr_test"],
        document_models=[
            Organization, User, Employee, Job, Candidate, CandidateMatch,
            AttritionPrediction, AuditLog, Skill, RoleSkillRequirement,
            SkillGapAnalysis, CareerPath
        ]
    )

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
    org_a = Organization(name="Acme Corp")
    await org_a.insert()

    user_admin_a = User(
        organization_id=org_a,
        email="admin@acme.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_a.insert()

    user_hr_a = User(
        organization_id=org_a,
        email="hrmanager@acme.com",
        password_hash=get_password_hash("password"),
        role="HR_MANAGER"
    )
    await user_hr_a.insert()

    user_recruiter_a = User(
        organization_id=org_a,
        email="recruiter@acme.com",
        password_hash=get_password_hash("password"),
        role="RECRUITER"
    )
    await user_recruiter_a.insert()

    # Setup Org B
    org_b = Organization(name="Beta Corp")
    await org_b.insert()

    user_admin_b = User(
        organization_id=org_b,
        email="admin@beta.com",
        password_hash=get_password_hash("password"),
        role="ORGANIZATION_ADMIN"
    )
    await user_admin_b.insert()

    # Employee in Org A
    emp_a = Employee(
        organization_id=org_a.to_ref(),
        employee_id="EMP-001",
        name="John Backend",
        department="Engineering",
        role="Backend Developer",
        joining_date="2022-01-15T00:00:00Z",
        experience=3.5,
        salary=95000,
        performance_score=4.2,
        engagement_score=4.0,
        overtime=5.0,
        skills="python3, FastAPI, mongo, react.js",
        promotion_history=0,
        manager_feedback="Solid backend engineer",
        employment_status="Active",
        attrition=0
    )
    await emp_a.insert()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "token_admin_a": create_access_token(str(user_admin_a.id)),
        "token_hr_a": create_access_token(str(user_hr_a.id)),
        "token_recruiter_a": create_access_token(str(user_recruiter_a.id)),
        "token_admin_b": create_access_token(str(user_admin_b.id)),
        "emp_a": emp_a,
    }

@pytest.mark.asyncio
async def test_skill_taxonomy_crud(setup_data):
    data = setup_data
    token = data["token_admin_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create custom skill
        res = await ac.post(
            "/api/v1/intelligence/skills",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "GraphQL",
                "category": "API",
                "aliases": ["graphql-api", "gql"],
                "description": "GraphQL query language"
            }
        )
        assert res.status_code == 200, res.text
        skill_json = res.json()
        skill_id = skill_json["skill_id"]
        assert skill_json["name"] == "GraphQL"
        assert "gql" in skill_json["aliases"]

        # 2. List skills (taxonomy includes standard + newly created)
        res_list = await ac.get(
            "/api/v1/intelligence/skills",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_list.status_code == 200
        names = [s["name"] for s in res_list.json()]
        assert "GraphQL" in names
        assert "Python" in names

        # 3. Update skill
        res_up = await ac.put(
            f"/api/v1/intelligence/skills/{skill_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Updated GraphQL description"}
        )
        assert res_up.status_code == 200
        assert res_up.json()["description"] == "Updated GraphQL description"

        # 4. Delete custom skill
        res_del = await ac.delete(
            f"/api/v1/intelligence/skills/{skill_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_del.status_code == 200

@pytest.mark.asyncio
async def test_role_skill_requirement_crud(setup_data):
    data = setup_data
    token = data["token_admin_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/intelligence/role-requirements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "role": "Senior Backend Developer",
                "required_skills": ["Python", "FastAPI", "MongoDB"],
                "preferred_skills": ["Docker", "AWS"],
                "skill_levels": {
                    "Python": "ADVANCED",
                    "FastAPI": "INTERMEDIATE",
                    "MongoDB": "INTERMEDIATE",
                    "Docker": "INTERMEDIATE",
                    "AWS": "INTERMEDIATE"
                }
            }
        )
        assert res.status_code == 200, res.text
        req_id = res.json()["requirement_id"]
        assert res.json()["role"] == "Senior Backend Developer"
        assert "Python" in res.json()["required_skills"]

        # Get requirement
        res_get = await ac.get(
            f"/api/v1/intelligence/role-requirements/{req_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_get.status_code == 200
        assert res_get.json()["role"] == "Senior Backend Developer"

@pytest.mark.asyncio
async def test_skill_gap_analysis_and_normalization(setup_data):
    data = setup_data
    token = data["token_hr_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create role requirements: Required: Python, FastAPI, MongoDB; Preferred: Docker, AWS
        await ac.post(
            "/api/v1/intelligence/role-requirements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "role": "Senior Backend Developer",
                "required_skills": ["Python", "FastAPI", "MongoDB"],
                "preferred_skills": ["Docker", "AWS"],
                "skill_levels": {}
            }
        )

        # Run skill gap analysis for EMP-001 (skills: "python3, FastAPI, mongo, react.js")
        # Notice python3 normalizes to Python, mongo to MongoDB!
        res_analyze = await ac.post(
            "/api/v1/intelligence/skill-gaps/analyze",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "employee_id": "EMP-001",
                "target_role": "Senior Backend Developer"
            }
        )
        assert res_analyze.status_code == 200, res_analyze.text
        gap = res_analyze.json()
        assert gap["employee_id"] == "EMP-001"
        assert gap["target_role"] == "Senior Backend Developer"
        
        # Required skills = 3 (Python, FastAPI, MongoDB). All 3 matched!
        # Coverage score should be 100.0% for required skills!
        assert gap["skill_coverage_score"] == 100.0
        assert gap["matched_count"] >= 3
        
        # Missing preferred skills: Docker, AWS
        missing_names = [m["skill"] for m in gap["missing_skills"]]
        assert "Docker" in missing_names
        assert "AWS" in missing_names

        # Verify recommendations explain why
        recs = gap["recommended_development_areas"]
        assert len(recs) > 0
        docker_rec = next(r for r in recs if r["skill"] == "Docker")
        assert "Docker" in docker_rec["reason"]

@pytest.mark.asyncio
async def test_career_path_generation_and_crud(setup_data):
    data = setup_data
    token = data["token_hr_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Generate Career Path
        res_gen = await ac.post(
            "/api/v1/intelligence/career-paths/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "employee_id": "EMP-001",
                "target_role": "Senior Backend Developer"
            }
        )
        assert res_gen.status_code == 200, res_gen.text
        cp = res_gen.json()
        assert cp["employee_id"] == "EMP-001"
        assert cp["target_role"] == "Senior Backend Developer"
        assert cp["is_ai_assisted"] is True
        assert "guaranteed promotion" in cp["disclaimer"].lower()
        assert len(cp["milestones"]) >= 4

        path_id = cp["career_path_id"]

        # 2. Update Milestone status
        milestones = cp["milestones"]
        milestones[0]["completed"] = True
        res_up = await ac.put(
            f"/api/v1/intelligence/career-paths/{path_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "status": "ACTIVE",
                "milestones": milestones
            }
        )
        assert res_up.status_code == 200
        assert res_up.json()["milestones"][0]["completed"] is True

        # 3. Analytics
        res_analytics = await ac.get(
            "/api/v1/intelligence/career-paths/analytics",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_analytics.status_code == 200
        analytics = res_analytics.json()
        assert analytics["active_career_paths"] >= 1

@pytest.mark.asyncio
async def test_multi_tenant_isolation(setup_data):
    data = setup_data
    token_a = data["token_admin_a"]
    token_b = data["token_admin_b"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Org A creates Role Requirement
        res_req = await ac.post(
            "/api/v1/intelligence/role-requirements",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "role": "Confidential A Role",
                "required_skills": ["Python"],
                "preferred_skills": [],
                "skill_levels": {}
            }
        )
        req_id_a = res_req.json()["requirement_id"]

        # 2. Org B tries to access Org A requirement -> 404
        res_req_b = await ac.get(
            f"/api/v1/intelligence/role-requirements/{req_id_a}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_req_b.status_code == 404

        # 3. Org B tries to analyze Org A employee EMP-001 -> 404
        res_gap_b = await ac.post(
            "/api/v1/intelligence/skill-gaps/analyze",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "employee_id": "EMP-001",
                "target_role": "Backend Developer"
            }
        )
        assert res_gap_b.status_code == 404

        # 4. Generate Career Path in Org A
        res_cp = await ac.post(
            "/api/v1/intelligence/career-paths/generate",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "employee_id": "EMP-001",
                "target_role": "Backend Lead"
            }
        )
        cp_id_a = res_cp.json()["career_path_id"]

        # 5. Org B tries to view or delete Org A career path -> 404
        res_cp_b = await ac.get(
            f"/api/v1/intelligence/career-paths/{cp_id_a}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_cp_b.status_code == 404

@pytest.mark.asyncio
async def test_rbac_restrictions(setup_data):
    data = setup_data
    token_recruiter = data["token_recruiter_a"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # RECRUITER must not have access to employee skill gap analysis or career development data
        res_gap = await ac.post(
            "/api/v1/intelligence/skill-gaps/analyze",
            headers={"Authorization": f"Bearer {token_recruiter}"},
            json={
                "employee_id": "EMP-001",
                "target_role": "Backend Developer"
            }
        )
        assert res_gap.status_code == 403

        res_cp = await ac.get(
            "/api/v1/intelligence/career-paths",
            headers={"Authorization": f"Bearer {token_recruiter}"}
        )
        assert res_cp.status_code == 403
