from typing import List, Optional, Any, Dict
from app.integrations.models.integration import Integration, generate_integration_id
from app.integrations.models.data_mapping import DataMapping
from app.integrations.models.sync_log import SyncLog
from app.integrations.provider_registry import get_connector
from app.integrations.erp.mapper import DEFAULT_ERP_MAPPING
from app.integrations.hris.mapper import DEFAULT_HRIS_MAPPING
from bson import ObjectId
from datetime import datetime, timezone
import uuid

def _resolve_org_id(org_link_or_id: Any) -> Any:
    if hasattr(org_link_or_id, "to_ref"):
        return org_link_or_id.to_ref().id
    if hasattr(org_link_or_id, "ref"):
        return org_link_or_id.ref.id
    if hasattr(org_link_or_id, "id"):
        return org_link_or_id.id
    if isinstance(org_link_or_id, str) and ObjectId.is_valid(org_link_or_id):
        return ObjectId(org_link_or_id)
    return org_link_or_id

def _org_filter(organization_id: Any) -> dict:
    resolved = _resolve_org_id(organization_id)
    conditions = [
        {"organization_id": resolved},
        {"organization_id.$id": resolved}
    ]
    if isinstance(resolved, ObjectId):
        conditions.extend([
            {"organization_id": str(resolved)},
            {"organization_id.$id": str(resolved)}
        ])
    elif isinstance(resolved, str) and ObjectId.is_valid(resolved):
        oid = ObjectId(resolved)
        conditions.extend([
            {"organization_id": oid},
            {"organization_id.$id": oid}
        ])
    return {"$or": conditions}

def _id_filter(integration_id: str) -> dict:
    conditions = [{"integration_id": str(integration_id)}]
    if ObjectId.is_valid(str(integration_id)):
        conditions.append({"_id": ObjectId(str(integration_id))})
    return {"$or": conditions}

class IntegrationService:
    @staticmethod
    async def get_integrations(organization_id: Any) -> List[Integration]:
        """Fetch all integrations for an organization (tenant isolated)."""
        return await Integration.find(_org_filter(organization_id)).to_list()

    @staticmethod
    async def get_integration(integration_id: str, organization_id: Any) -> Optional[Integration]:
        """Fetch a specific integration ensuring strict organization scoping."""
        query = {
            "$and": [
                _id_filter(integration_id),
                _org_filter(organization_id)
            ]
        }
        return await Integration.find_one(query)

    @staticmethod
    async def create_integration(
        organization_id: Any,
        provider_name: str,
        provider_type: str,
        credentials: Optional[dict] = None,
        integration_id: Optional[str] = None
    ) -> Integration:
        """Create a new integration and automatically initialize default field mappings."""
        now = datetime.now(timezone.utc)
        resolved_org = _resolve_org_id(organization_id)
        
        # Check if already exists for this provider in this org
        existing = await Integration.find_one({
            "$and": [
                _org_filter(organization_id),
                {"provider_name": provider_name}
            ]
        })
        if existing:
            existing.status = "Connected"
            existing.updated_at = now
            if credentials is not None:
                existing.authorized_data = credentials
            await existing.save()
            return existing

        actual_id = integration_id or generate_integration_id()
        params = {
            "organization_id": organization_id,
            "integration_id": actual_id,
            "provider_name": provider_name,
            "provider_type": provider_type.upper(),
            "status": "Connected",
            "connection_method": "MOCK" if "demo" in provider_name.lower() or "mock" in provider_name.lower() else "API",
            "authorized_data": credentials or {},
            "created_at": now,
            "updated_at": now
        }
        integration = Integration(**params)
        await integration.insert()

        # Seed default DataMapping documents in DB for this integration
        await IntegrationService.seed_default_mappings(integration)

        return integration

    @staticmethod
    async def seed_default_mappings(integration: Integration) -> None:
        """Seed default field mappings into the database if none exist."""
        p_name = (integration.provider_name or "").lower()
        p_type = (integration.provider_type or "").lower()

        if "erp" in p_name or "erp" in p_type:
            defaults = DEFAULT_ERP_MAPPING
        elif "hris" in p_name or "hris" in p_type:
            defaults = DEFAULT_HRIS_MAPPING
        else:
            return

        for src, target in defaults.items():
            existing_mapping = await DataMapping.find_one({
                "$and": [
                    _org_filter(integration.organization_id),
                    {"integration_id": integration.integration_id},
                    {"source_field": src}
                ]
            })
            if not existing_mapping:
                mapping = DataMapping(
                    organization_id=integration.organization_id,
                    integration_id=integration.integration_id,
                    source_field=src,
                    target_field=target,
                    mapping_status="ACTIVE"
                )
                await mapping.insert()

    @staticmethod
    async def update_integration(
        integration_id: str,
        organization_id: Any,
        **kwargs
    ) -> Optional[Integration]:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if not integration:
            return None
        for k, v in kwargs.items():
            if hasattr(integration, k) and v is not None:
                setattr(integration, k, v)
        integration.updated_at = datetime.now(timezone.utc)
        await integration.save()
        return integration

    @staticmethod
    async def delete_integration(integration_id: str, organization_id: Any) -> bool:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if integration:
            # Also clean up associated mappings and sync logs
            await DataMapping.find({
                "$and": [
                    _org_filter(organization_id),
                    {"integration_id": integration.integration_id}
                ]
            }).delete()
            await integration.delete()
            return True
        return False

    @staticmethod
    async def connect_integration(integration_id: str, organization_id: Any) -> Optional[Integration]:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if integration:
            integration.status = "Connected"
            integration.updated_at = datetime.now(timezone.utc)
            await integration.save()
            return integration
        return None

    @staticmethod
    async def disconnect_integration(integration_id: str, organization_id: Any) -> bool:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if integration:
            integration.status = "Disconnected"
            integration.updated_at = datetime.now(timezone.utc)
            await integration.save()
            return True
        return False

    @staticmethod
    async def test_connection(integration_id: str, organization_id: Any) -> bool:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if not integration:
            return False
        try:
            connector = get_connector(integration.provider_name)
            return await connector.test_connection()
        except ValueError:
            p_name = (integration.provider_name or "").lower()
            p_type = (integration.provider_type or "").lower()
            if "erp" in p_name or "erp" in p_type:
                connector = get_connector("demo_erp")
            elif "csv" in p_name or "csv" in p_type:
                connector = get_connector("csv")
            else:
                connector = get_connector("demo_hris")
            return await connector.test_connection()

    # --- Data Mappings CRUD ---

    @staticmethod
    async def get_mappings(integration_id: str, organization_id: Any) -> List[DataMapping]:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if not integration:
            return []
        return await DataMapping.find({
            "$and": [
                _org_filter(organization_id),
                {"integration_id": integration.integration_id}
            ]
        }).to_list()

    @staticmethod
    async def create_mapping(
        integration_id: str,
        organization_id: Any,
        source_field: str,
        target_field: str,
        mapping_status: str = "ACTIVE"
    ) -> Optional[DataMapping]:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if not integration:
            return None
        mapping = DataMapping(
            organization_id=integration.organization_id,
            integration_id=integration.integration_id,
            source_field=source_field,
            target_field=target_field,
            mapping_status=mapping_status
        )
        await mapping.insert()
        return mapping

    @staticmethod
    async def update_mapping(
        integration_id: str,
        mapping_id: str,
        organization_id: Any,
        source_field: Optional[str] = None,
        target_field: Optional[str] = None,
        mapping_status: Optional[str] = None
    ) -> Optional[DataMapping]:
        mapping = await DataMapping.find_one({
            "$and": [
                _org_filter(organization_id),
                {"_id": ObjectId(mapping_id) if ObjectId.is_valid(mapping_id) else mapping_id}
            ]
        })
        if not mapping:
            return None
        if source_field is not None:
            mapping.source_field = source_field
        if target_field is not None:
            mapping.target_field = target_field
        if mapping_status is not None:
            mapping.mapping_status = mapping_status
        mapping.updated_at = datetime.now(timezone.utc)
        await mapping.save()
        return mapping

    @staticmethod
    async def delete_mapping(integration_id: str, mapping_id: str, organization_id: Any) -> bool:
        mapping = await DataMapping.find_one({
            "$and": [
                _org_filter(organization_id),
                {"_id": ObjectId(mapping_id) if ObjectId.is_valid(mapping_id) else mapping_id}
            ]
        })
        if mapping:
            await mapping.delete()
            return True
        return False

    # --- Sync Logs Retrieval ---

    @staticmethod
    async def get_sync_logs(integration_id: str, organization_id: Any) -> List[SyncLog]:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if not integration:
            return []
        return await SyncLog.find({
            "$and": [
                _org_filter(organization_id),
                {
                    "$or": [
                        {"integration_id": integration.integration_id},
                        {"integration_id": str(integration.id)}
                    ]
                }
            ]
        }).sort("-started_at").to_list()
