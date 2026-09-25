from datetime import datetime, timezone
import uuid
from typing import Optional, Dict, Any
from beanie import Document, Link
from pydantic import Field
from app.models.organization import Organization

def generate_integration_id() -> str:
    return f"INT-{uuid.uuid4().hex[:8].upper()}"

class Integration(Document):
    """Represents an external data source integration for a tenant organization."""
    organization_id: Link[Organization]
    integration_id: str = Field(default_factory=generate_integration_id)
    provider_name: str   # e.g., "demo_erp", "demo_hris", "csv"
    provider_type: str   # e.g., "DEMO_ERP", "DEMO_HRIS", "CSV" (or "erp", "hris", "csv")
    status: str = "Connected"  # "Connected", "Disconnected", "Error", "Syncing"
    connection_method: str = "MOCK"  # "MOCK", "API", "OAUTH", "CSV_UPLOAD"
    authorized_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_sync_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "integrations"
        indexes = ["organization_id", "integration_id", "provider_type"]
