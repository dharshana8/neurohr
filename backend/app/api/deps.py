from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await User.get(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
            )
        return current_user
    return role_checker

require_platform_admin = require_role(["PLATFORM_ADMIN"])
require_organization_admin = require_role(["ORGANIZATION_ADMIN"])
require_hr_manager = require_role(["ORGANIZATION_ADMIN", "HR_MANAGER"])
require_recruiter = require_role(["ORGANIZATION_ADMIN", "HR_MANAGER", "RECRUITER"])
require_hr_analyst = require_role(["ORGANIZATION_ADMIN", "HR_MANAGER", "HR_ANALYST"])
require_recruitment_write = require_role(["ORGANIZATION_ADMIN", "HR_MANAGER", "RECRUITER"])
require_recruitment_read = require_role(["ORGANIZATION_ADMIN", "HR_MANAGER", "RECRUITER", "HR_ANALYST"])
