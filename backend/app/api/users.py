from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.auth import UserResponse
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role,
        organization_id=str(current_user.organization_id.id)
    )
