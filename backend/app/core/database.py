from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient
if not hasattr(AgnosticClient, "append_metadata"):
    setattr(AgnosticClient, "append_metadata", lambda self, *args, **kwargs: None)

from beanie import init_beanie
from .config import settings
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


async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Organization,
            User,
            Employee,
            AttritionPrediction,
            Job,
            Candidate,
            CandidateMatch,
            AuditLog,
            Skill,
            RoleSkillRequirement,
            SkillGapAnalysis,
            CareerPath,
            AIChatConversation,
            HRPolicyDocument,
            EmployeeFeedback,
            SentimentResult,
            Integration,
            DataMapping,
            SyncLog,
        ]
    )

    from app.core.security import get_password_hash
    # Seed default SuperAdmin if not exists
    superadmin = await User.find_one(User.email == "admin@neurohr.com")
    if not superadmin:
        admin_user = User(
            email="admin@neurohr.com",
            password_hash=get_password_hash("admin"),
            role="PLATFORM_ADMIN",
            is_active=True
        )
        await admin_user.insert()

    # Seed default Demo Tenant Admin if not exists
    demo_admin = await User.find_one(User.email == "admin@acme.com")
    if not demo_admin:
        acme_org = await Organization.find_one(Organization.name == "Acme Corporation")
        if not acme_org:
            acme_org = Organization(
                name="Acme Corporation",
                industry="Technology",
                company_size="51-200",
                status="ACTIVE",
                plan_tier="PROFESSIONAL"
            )
            await acme_org.insert()
        demo_user = User(
            organization_id=acme_org,
            email="admin@acme.com",
            password_hash=get_password_hash("admin"),
            role="ORGANIZATION_ADMIN",
            is_active=True
        )
        await demo_user.insert()

