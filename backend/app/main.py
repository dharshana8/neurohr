from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Cleanup on shutdown if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to NeuroHR X API"}

from app.api import auth, users, workforce, attrition
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(workforce.router, prefix=f"{settings.API_V1_STR}/workforce", tags=["workforce"])
app.include_router(attrition.router, prefix=f"{settings.API_V1_STR}/attrition", tags=["attrition"])

