from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str = None

class RegisterTenantRequest(BaseModel):
    organization_name: str
    admin_email: EmailStr
    admin_password: str

from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
