import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import init_db

async def create_superadmin(email: str = "admin@neurohr.com", password: str = "admin"):
    await init_db()

    existing_admin = await User.find_one(User.email == email)
    if existing_admin:
        existing_admin.role = "PLATFORM_ADMIN"
        existing_admin.password_hash = get_password_hash(password)
        existing_admin.is_active = True
        await existing_admin.save()
        print(f"SuperAdmin {email} updated to PLATFORM_ADMIN with updated password.")
        return

    admin_user = User(
        email=email,
        password_hash=get_password_hash(password),
        role="PLATFORM_ADMIN",
        is_active=True
    )
    
    await admin_user.insert()
    print(f"SuperAdmin created successfully! Email: {email}, Password: {password}")

if __name__ == "__main__":
    cli_email = sys.argv[1] if len(sys.argv) > 1 else "admin@neurohr.com"
    cli_password = sys.argv[2] if len(sys.argv) > 2 else "admin"
    asyncio.run(create_superadmin(cli_email, cli_password))
