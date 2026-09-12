from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroHR X"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "change_this_to_a_secure_random_string_in_production_89234"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "neurohr"

    # xAI Grok API Configuration
    XAI_API_KEY: str = ""
    XAI_MODEL: str = "grok-4.6"
    XAI_BASE_URL: str = "https://api.x.ai/v1"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
