from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timezone
from app.models.organization import Organization

class SyncLog(Document):
    """Tracks each sync operation for an integration."""
    organization_id: Link[Organization]
    integration_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    status: str = "IN_PROGRESS"  # IN_PROGRESS, SUCCESS, FAILED
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: str | None = None

    class Settings:
        name = "integration_sync_logs"
        indexes = ["organization_id", "integration_id", "started_at"]
