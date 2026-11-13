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

    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Legacy/Fallback Aliases
    XAI_API_KEY: str = ""
    XAI_MODEL: str = "gemini-2.0-flash"
    XAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
