from typing import Optional
from datetime import datetime, timezone
from pydantic import Field, EmailStr
from beanie import Document, Link
from .organization import Organization

class User(Document):
    organization_id: Optional[Link[Organization]] = None
    email: EmailStr
    password_hash: str
    role: str = "ORGANIZATION_ADMIN" # PLATFORM_ADMIN, ORGANIZATION_ADMIN, HR_MANAGER, RECRUITER, HR_ANALYST
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            "email",
            "organization_id"
        ]
