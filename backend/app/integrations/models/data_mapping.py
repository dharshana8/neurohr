from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
from app.models.organization import Organization

class DataMapping(Document):
    """Maps source fields to normalized NeuroHR fields for a specific integration."""
    organization_id: Link[Organization]
    integration_id: str  # reference to Integration.integration_id
    source_field: str
    target_field: str
    mapping_status: str = "ACTIVE"  # could be ACTIVE, INACTIVE, DEPRECATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "data_mappings"
        indexes = ["organization_id", "integration_id", "source_field"]
