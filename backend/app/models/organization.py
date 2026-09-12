from typing import Optional
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document

class Organization(Document):
    name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    status: str = "ACTIVE" # ACTIVE, SUSPENDED, INACTIVE
    plan_tier: str = "STARTER" # STARTER, PROFESSIONAL, ENTERPRISE
    plan_limits: Optional[dict] = Field(default_factory=dict)
    subscription_status: str = "ACTIVE" # ACTIVE, PAST_DUE, CANCELLED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "organizations"
