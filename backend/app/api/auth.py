from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import Token, RegisterTenantRequest

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register-tenant")
async def register_tenant(req: RegisterTenantRequest):
    # Check if admin email already exists
    if await User.find_one(User.email == req.admin_email):
        raise HTTPException(status_code=400, detail="User already exists")

    # Create Organization
    org = Organization(name=req.organization_name)
    await org.insert()

    # Create Admin User
    user = User(
        organization_id=org,
        email=req.admin_email,
        password_hash=security.get_password_hash(req.admin_password),
        role="Admin"
    )
    await user.insert()

    return {"message": "Tenant registered successfully", "organization_id": str(org.id)}
