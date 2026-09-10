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


async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Organization,
            User,
            Employee,
            AttritionPrediction,
        ]
    )
