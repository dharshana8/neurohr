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

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    organization_id: str

    class Config:
        from_attributes = True
