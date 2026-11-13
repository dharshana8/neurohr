from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
from app.models.organization import Organization
from app.models.user import User

class AuditLog(Document):
    user_id: Link[User]
    organization_id: Optional[Link[Organization]] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str = "SUCCESS"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"
