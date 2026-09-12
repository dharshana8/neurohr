from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any, Optional
from app.api.deps import get_current_active_user
from app.models.user import User
from app.integrations.services.integration_service import IntegrationService
from app.integrations.services.sync_service import SyncService
from pydantic import BaseModel
from app.integrations.models.integration import Integration

router = APIRouter()

class CreateIntegrationRequest(BaseModel):
    provider_name: str
    provider_type: str
    credentials: dict = {}

class UpdateIntegrationRequest(BaseModel):
    provider_name: Optional[str] = None
    provider_type: Optional[str] = None
    status: Optional[str] = None
    credentials: Optional[dict] = None

class IntegrationResponse(BaseModel):
    id: str
    provider_name: str
    provider_type: str
    status: str
    last_sync_at: Any
    integration_id: Optional[str] = None

    class Config:
        from_attributes = True

def _build_response(i: Integration) -> IntegrationResponse:
    return IntegrationResponse(
        id=str(i.id),
        provider_name=i.provider_name,
        provider_type=i.provider_type,
        status=i.status,
        last_sync_at=i.last_sync_at,
        integration_id=i.integration_id
    )

@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    integrations = await IntegrationService.get_integrations(org_id)
    return [_build_response(i) for i in integrations]

@router.post("/", response_model=IntegrationResponse)
async def create_integration(req: CreateIntegrationRequest, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    integration = await IntegrationService.create_integration(
        organization_id=org_id,
        provider_name=req.provider_name,
        provider_type=req.provider_type,
        credentials=req.credentials
    )
    return _build_response(integration)

@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration_id: str, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _build_response(integration)

@router.put("/{integration_id}", response_model=IntegrationResponse)
@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(integration_id: str, req: UpdateIntegrationRequest, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    update_data = {}
    if req.provider_name is not None:
        update_data["provider_name"] = req.provider_name
    if req.provider_type is not None:
        update_data["provider_type"] = req.provider_type
    if req.status is not None:
        update_data["status"] = req.status
    if req.credentials is not None:
        update_data["authorized_data"] = req.credentials
        
    integration = await IntegrationService.update_integration(integration_id, org_id, **update_data)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _build_response(integration)

@router.delete("/{integration_id}")
async def delete_integration(integration_id: str, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    success = await IntegrationService.delete_integration(integration_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"status": "success", "message": "Integration deleted successfully"}

@router.post("/{integration_id}/test")
async def test_integration(integration_id: str, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    success = await IntegrationService.test_connection(integration_id, org_id)
    if not success:
        raise HTTPException(status_code=400, detail="Connection failed")
    return {"status": "success", "message": "Connection successful"}

@router.post("/{integration_id}/sync")
async def sync_integration(integration_id: str, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    integration = await IntegrationService.get_integration(integration_id, org_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    sync_log = await SyncService.sync_integration(integration)
    
    return {
        "status": sync_log.status,
        "message": sync_log.message,
        "records_fetched": sync_log.records_fetched,
        "records_created": sync_log.records_created,
        "records_updated": sync_log.records_updated
    }

@router.post("/{integration_id}/disconnect")
async def disconnect_integration(integration_id: str, current_user: User = Depends(get_current_active_user)):
    org_id = current_user.organization_id.to_ref().id if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    success = await IntegrationService.disconnect_integration(integration_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"status": "success", "message": "Disconnected successfully"}
