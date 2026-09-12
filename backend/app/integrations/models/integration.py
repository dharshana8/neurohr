from datetime import datetime, timezone
import uuid
from typing import Optional
from beanie import Document, Link
from pydantic import Field
from app.models.organization import Organization

class Integration(Document):
    """Represents a data source integration for an organization."""
    organization_id: Link[Organization]
    integration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # unique identifier (e.g., UUID)
    provider_name: str   # human readable name, e.g., "Demo HRIS"
    provider_type: str   # HRIS, ERP, CSV
    status: str          # CONNECTED, DISCONNECTED, ERROR, SYNCING
    connection_method: str  # MOCK, API, OAUTH, CSV_UPLOAD
    authorized_data: Optional[dict] = Field(default_factory=dict)  # permissions selected by user
    last_sync_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "integrations"
        indexes = ["organization_id", "integration_id", "provider_type"]
