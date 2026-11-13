from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroHR X - Enterprise HRIS & ERP Intelligence"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "neurohr-enterprise-super-secret-jwt-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Real MongoDB Database Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "neurohr"

    # xAI Grok API Configuration
    XAI_API_KEY: str = ""
    XAI_MODEL: str = "grok-4.6"
    XAI_BASE_URL: str = "https://api.x.ai/v1"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
