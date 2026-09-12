from typing import List, Optional, Any
from app.integrations.models.integration import Integration
from app.integrations.provider_registry import get_connector
from bson import ObjectId
import datetime
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
        return await Integration.find(_org_filter(organization_id)).to_list()

    @staticmethod
    async def get_integration(integration_id: str, organization_id: Any) -> Optional[Integration]:
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
        credentials: dict,
        integration_id: Optional[str] = None
    ) -> Integration:
        now = datetime.datetime.now(datetime.timezone.utc)
        params = {
            "organization_id": organization_id,
            "provider_name": provider_name,
            "provider_type": provider_type,
            "status": "Connected",
            "connection_method": "oauth" if provider_type.lower() != "csv" else "upload",
            "authorized_data": credentials,
            "created_at": now,
            "updated_at": now
        }
        if integration_id:
            params["integration_id"] = integration_id
        integration = Integration(**params)
        await integration.insert()
        return integration

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
        integration.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await integration.save()
        return integration

    @staticmethod
    async def delete_integration(integration_id: str, organization_id: Any) -> bool:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if integration:
            await integration.delete()
            return True
        return False
    
    @staticmethod
    async def disconnect_integration(integration_id: str, organization_id: Any) -> bool:
        integration = await IntegrationService.get_integration(integration_id, organization_id)
        if integration:
            integration.status = "Disconnected"
            integration.updated_at = datetime.datetime.now(datetime.timezone.utc)
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
