from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "AI Service Desk 🛠️"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/support.db"
    GROQ_API_KEY: Optional[str] = ""
    AI_MODEL: str = "openai/gpt-oss-120b"
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: Optional[str] = ""
    SECRET_KEY: str = "super-secret-service-desk-key-change-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
