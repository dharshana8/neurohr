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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to NeuroHR X API"}

from app.api import auth, users, workforce, attrition, platform_admin
from app.api.integrations.router import router as integrations_router
from app.recruitment.router import router as recruitment_router
from app.api.intelligence.router import router as intelligence_router
from app.api.ai.router import router as ai_router
from app.api.sentiment.router import router as sentiment_router

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(workforce.router, prefix=f"{settings.API_V1_STR}/workforce", tags=["workforce"])
app.include_router(attrition.router, prefix=f"{settings.API_V1_STR}/attrition", tags=["attrition"])
app.include_router(recruitment_router, prefix=f"{settings.API_V1_STR}/recruitment", tags=["recruitment"])
app.include_router(integrations_router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
app.include_router(platform_admin.router, prefix=f"{settings.API_V1_STR}/platform-admin", tags=["platform-admin"])
app.include_router(intelligence_router, prefix=f"{settings.API_V1_STR}/intelligence", tags=["intelligence"])
app.include_router(intelligence_router, prefix=f"{settings.API_V1_STR}", tags=["intelligence-v1-direct"])
app.include_router(intelligence_router, prefix="/api", tags=["intelligence-api-direct"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai-direct"])
app.include_router(sentiment_router, prefix=f"{settings.API_V1_STR}", tags=["sentiment-v1-direct"])
app.include_router(sentiment_router, prefix="/api", tags=["sentiment-api-direct"])
app.include_router(sentiment_router, prefix=f"{settings.API_V1_STR}/intelligence", tags=["sentiment-intelligence"])
