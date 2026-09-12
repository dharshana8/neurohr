from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.schemas.auth import UserResponse, UserCreate, UserUpdate
from app.api.deps import get_current_active_user, require_organization_admin
from app.core import security
from beanie import PydanticObjectId

router = APIRouter()

def get_org_id(org_link):
    if not org_link:
        return None
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    org_id = get_org_id(current_user.organization_id)
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role,
        organization_id=str(org_id) if org_id else None
    )

@router.post("/", response_model=UserResponse)
async def create_user(
    req: UserCreate,
    current_admin: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_admin.organization_id)
    if not org_id:
        raise HTTPException(status_code=400, detail="Admin has no organization")

    if await User.find_one(User.email == req.email):
        raise HTTPException(status_code=400, detail="User already exists")

    org_ref = current_admin.organization_id.to_ref() if hasattr(current_admin.organization_id, "to_ref") else current_admin.organization_id

    user = User(
        organization_id=org_ref,
        email=req.email,
        password_hash=security.get_password_hash(req.password),
        role=req.role
    )
    await user.insert()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        organization_id=str(org_id)
    )

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_admin: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_admin.organization_id)
    users = await User.find({"organization_id.$id": org_id}).to_list()
    
    return [
        UserResponse(
            id=str(u.id),
            email=u.email,
            role=u.role,
            organization_id=str(org_id)
        ) for u in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_admin: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_admin.organization_id)
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_org_id = get_org_id(user.organization_id)
    if user_org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
        
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        organization_id=str(org_id)
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: UserUpdate,
    current_admin: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_admin.organization_id)
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_org_id = get_org_id(user.organization_id)
    if user_org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
        
    await user.save()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        organization_id=str(org_id)
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: User = Depends(require_organization_admin)
):
    org_id = get_org_id(current_admin.organization_id)
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_org_id = get_org_id(user.organization_id)
    if user_org_id != org_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
        
    await user.delete()
    return {"message": "User deleted successfully"}
