from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_active_user,
    require_organization_admin,
    require_hr_manager,
    require_hr_analyst
)
from app.models.user import User
from app.models.audit import AuditLog
from app.integrations.models.integration import Integration
from app.integrations.models.data_mapping import DataMapping
from app.integrations.models.sync_log import SyncLog
from app.integrations.services.integration_service import IntegrationService
from app.integrations.services.sync_service import SyncService

router = APIRouter()

# --- RBAC Helper Dependencies ---
def _check_recruiter_forbidden(current_user: User):
    if current_user.role == "RECRUITER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiters do not have access to external ERP/HRIS data integrations."
        )

async def require_integration_read(current_user: User = Depends(get_current_active_user)) -> User:
    _check_recruiter_forbidden(current_user)
    if current_user.role not in ["ORGANIZATION_ADMIN", "HR_MANAGER", "HR_ANALYST", "PLATFORM_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to view integrations.")
    return current_user

async def require_integration_sync(current_user: User = Depends(get_current_active_user)) -> User:
    _check_recruiter_forbidden(current_user)
    if current_user.role not in ["ORGANIZATION_ADMIN", "HR_MANAGER", "PLATFORM_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins and HR Managers may trigger synchronization.")
    return current_user

async def require_integration_admin(current_user: User = Depends(get_current_active_user)) -> User:
    _check_recruiter_forbidden(current_user)
    if current_user.role not in ["ORGANIZATION_ADMIN", "PLATFORM_ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can manage integration configurations.")
    return current_user

def _get_org_id(user: User):
    if hasattr(user.organization_id, "to_ref"):
        return user.organization_id.to_ref().id
    if hasattr(user.organization_id, "ref"):
        return user.organization_id.ref.id
    if hasattr(user.organization_id, "id"):
        return user.organization_id.id
    return user.organization_id

async def _record_audit(user: User, action: str, resource_id: str, result: str = "SUCCESS"):
    try:
        log = AuditLog(
            user_id=user,
            organization_id=user.organization_id,
            action=action,
            resource_type="INTEGRATION",
            resource_id=str(resource_id),
            status=result
        )
        await log.insert()
    except Exception:
        pass

# --- Schemas ---
class CreateIntegrationRequest(BaseModel):
    provider_name: str
    provider_type: str
    credentials: Dict[str, Any] = Field(default_factory=dict)

class UpdateIntegrationRequest(BaseModel):
    provider_name: Optional[str] = None
    provider_type: Optional[str] = None
    status: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None

class IntegrationResponse(BaseModel):
    id: str
    integration_id: str
    provider_name: str
    provider_type: str
    status: str
    last_sync_at: Optional[datetime] = None

class DataMappingRequest(BaseModel):
    source_field: str
    target_field: str
    mapping_status: Optional[str] = "ACTIVE"

class DataMappingResponse(BaseModel):
    id: str
    integration_id: str
    source_field: str
    target_field: str
    mapping_status: str

class SyncLogResponse(BaseModel):
    id: str
    integration_id: str
    status: str
    records_fetched: int
    records_created: int
    records_updated: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[List[str]] = Field(default_factory=list)

def _build_response(i: Integration) -> IntegrationResponse:
    return IntegrationResponse(
        id=str(i.id),
        integration_id=i.integration_id,
        provider_name=i.provider_name,
        provider_type=i.provider_type,
        status=i.status,
        last_sync_at=i.last_sync_at
    )

# --- Endpoints ---

@router.get("", response_model=List[IntegrationResponse])
@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(current_user: User = Depends(require_integration_read)):
    """List all integrations configured for the caller's tenant organization."""
    org_id = _get_org_id(current_user)
    integrations = await IntegrationService.get_integrations(org_id)
    return [_build_response(i) for i in integrations]

@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    req: CreateIntegrationRequest,
    current_user: User = Depends(require_integration_admin)
):
    """Create a new external data integration with automatic integration_id generation."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.create_integration(
        organization_id=org_id,
        provider_name=req.provider_name,
        provider_type=req.provider_type,
        credentials=req.credentials
    )
    await _record_audit(current_user, "INTEGRATION_CREATED", integration.integration_id)
    return _build_response(integration)

@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_read)
):
    """Retrieve integration details scoped strictly to tenant."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _build_response(integration)

@router.put("/{integration_id}", response_model=IntegrationResponse)
@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    req: UpdateIntegrationRequest,
    current_user: User = Depends(require_integration_admin)
):
    """Update integration settings and credentials."""
    org_id = _get_org_id(current_user)
    update_data = {}
    if req.provider_name is not None:
        update_data["provider_name"] = req.provider_name
    if req.provider_type is not None:
        update_data["provider_type"] = req.provider_type.upper()
    if req.status is not None:
        update_data["status"] = req.status
    if req.credentials is not None:
        update_data["authorized_data"] = req.credentials

    integration = await IntegrationService.update_integration(integration_id, org_id, **update_data)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await _record_audit(current_user, "INTEGRATION_UPDATED", integration.integration_id)
    return _build_response(integration)

@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_admin)
):
    """Delete an integration and its mappings."""
    org_id = _get_org_id(current_user)
    success = await IntegrationService.delete_integration(integration_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    await _record_audit(current_user, "INTEGRATION_DELETED", integration_id)
    return {"status": "SUCCESS", "message": "Integration deleted successfully"}

# --- Actions: Connect / Test / Sync / Disconnect ---

@router.post("/{integration_id}/connect", response_model=IntegrationResponse)
async def connect_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_sync)
):
    """Authorize and mark integration status as Connected."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.connect_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await _record_audit(current_user, "INTEGRATION_CONNECTED", integration.integration_id)
    return _build_response(integration)

@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_sync)
):
    """Execute live connection test against target integration service."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    success = await IntegrationService.test_connection(integration_id, org_id)
    audit_status = "SUCCESS" if success else "FAILED"
    await _record_audit(current_user, "CONNECTION_TESTED", integration.integration_id, audit_status)

    if not success:
        raise HTTPException(status_code=400, detail="Connection test failed for integration provider")
    return {"status": "SUCCESS", "message": "Connection test successful"}

@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_sync)
):
    """Execute synchronization pipeline with normalization and deduplication."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    sync_log = await SyncService.sync_integration(integration)
    await _record_audit(current_user, "INTEGRATION_SYNCED", integration.integration_id, sync_log.status)

    if sync_log.status == "FAILED" and sync_log.error_message and "disconnected" in sync_log.error_message.lower():
        raise HTTPException(status_code=400, detail=sync_log.error_message)

    return {
        "status": sync_log.status,
        "message": sync_log.message or sync_log.error_message,
        "records_fetched": sync_log.records_fetched,
        "records_created": sync_log.records_created,
        "records_updated": sync_log.records_updated,
        "records_failed": sync_log.records_failed
    }

@router.post("/{integration_id}/disconnect", response_model=IntegrationResponse)
async def disconnect_integration(
    integration_id: str,
    current_user: User = Depends(require_integration_sync)
):
    """Disconnect integration from receiving active synchronizations."""
    org_id = _get_org_id(current_user)
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    await IntegrationService.disconnect_integration(integration_id, org_id)
    integration.status = "Disconnected"
    await _record_audit(current_user, "INTEGRATION_DISCONNECTED", integration.integration_id)
    return _build_response(integration)

# --- Field Mappings Endpoints ---

@router.get("/{integration_id}/mappings", response_model=List[DataMappingResponse])
async def list_data_mappings(
    integration_id: str,
    current_user: User = Depends(require_integration_read)
):
    """List configurable data mappings for an integration."""
    org_id = _get_org_id(current_user)
    mappings = await IntegrationService.get_mappings(integration_id, org_id)
    return [
        DataMappingResponse(
            id=str(m.id),
            integration_id=m.integration_id,
            source_field=m.source_field,
            target_field=m.target_field,
            mapping_status=m.mapping_status
        )
        for m in mappings
    ]

@router.post("/{integration_id}/mappings", response_model=DataMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_data_mapping(
    integration_id: str,
    req: DataMappingRequest,
    current_user: User = Depends(require_integration_admin)
):
    """Add a custom field mapping for an integration."""
    org_id = _get_org_id(current_user)
    mapping = await IntegrationService.create_mapping(
        integration_id=integration_id,
        organization_id=org_id,
        source_field=req.source_field,
        target_field=req.target_field,
        mapping_status=req.mapping_status or "ACTIVE"
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Integration not found")
    await _record_audit(current_user, "MAPPING_CREATED", str(mapping.id))
    return DataMappingResponse(
        id=str(mapping.id),
        integration_id=mapping.integration_id,
        source_field=mapping.source_field,
        target_field=mapping.target_field,
        mapping_status=mapping.mapping_status
    )

@router.put("/{integration_id}/mappings/{mapping_id}", response_model=DataMappingResponse)
async def update_data_mapping(
    integration_id: str,
    mapping_id: str,
    req: DataMappingRequest,
    current_user: User = Depends(require_integration_admin)
):
    """Update an existing field mapping."""
    org_id = _get_org_id(current_user)
    mapping = await IntegrationService.update_mapping(
        integration_id=integration_id,
        mapping_id=mapping_id,
        organization_id=org_id,
        source_field=req.source_field,
        target_field=req.target_field,
        mapping_status=req.mapping_status
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    await _record_audit(current_user, "MAPPING_UPDATED", str(mapping.id))
    return DataMappingResponse(
        id=str(mapping.id),
        integration_id=mapping.integration_id,
        source_field=mapping.source_field,
        target_field=mapping.target_field,
        mapping_status=mapping.mapping_status
    )

@router.delete("/{integration_id}/mappings/{mapping_id}")
async def delete_data_mapping(
    integration_id: str,
    mapping_id: str,
    current_user: User = Depends(require_integration_admin)
):
    """Delete a custom field mapping."""
    org_id = _get_org_id(current_user)
    success = await IntegrationService.delete_mapping(integration_id, mapping_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    await _record_audit(current_user, "MAPPING_DELETED", mapping_id)
    return {"status": "SUCCESS", "message": "Mapping deleted successfully"}

# --- Sync Logs Endpoint ---

@router.get("/{integration_id}/sync-logs", response_model=List[SyncLogResponse])
async def get_integration_sync_logs(
    integration_id: str,
    current_user: User = Depends(require_integration_read)
):
    """Retrieve audit history and telemetry logs of past synchronizations."""
    org_id = _get_org_id(current_user)
    logs = await IntegrationService.get_sync_logs(integration_id, org_id)
    return [
        SyncLogResponse(
            id=str(log.id),
            integration_id=log.integration_id,
            status=log.status,
            records_fetched=log.records_fetched,
            records_created=log.records_created,
            records_updated=log.records_updated,
            records_failed=log.records_failed,
            started_at=log.started_at,
            completed_at=log.completed_at,
            message=log.message or log.error_message,
            error_message=log.error_message,
            details=log.details or []
        )
        for log in logs
    ]
