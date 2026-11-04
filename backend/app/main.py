from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import auth, workforce, hris, erp, ai, evaluation, intelligence, talent, attrition, platform_admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}", tags=["User Profile"]) # for /users/me
app.include_router(workforce.router, prefix=f"{settings.API_V1_STR}/workforce", tags=["Workforce Management"])
app.include_router(hris.router, prefix=f"{settings.API_V1_STR}/hris", tags=["HRIS Portal"])
app.include_router(erp.router, prefix=f"{settings.API_V1_STR}/erp", tags=["ERP Portal"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Copilot"])
app.include_router(evaluation.router, prefix=f"{settings.API_V1_STR}/ai/evaluation", tags=["AI Testing & Evaluation Lab"])
app.include_router(intelligence.router, prefix=f"{settings.API_V1_STR}/intelligence", tags=["Workforce Intelligence"])
app.include_router(attrition.router, prefix=f"{settings.API_V1_STR}/attrition", tags=["Attrition AI"])
app.include_router(attrition.router, prefix=f"{settings.API_V1_STR}/ai/explain", tags=["AI Explainability"])
app.include_router(platform_admin.router, prefix=f"{settings.API_V1_STR}/platform-admin", tags=["Platform SuperAdmin"])
app.include_router(talent.router, prefix=f"{settings.API_V1_STR}", tags=["Talent & Recruitment"]) # for /jobs, /candidates

@app.get("/")
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": "2.4.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

