from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "AI Service Desk 🛠️"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/support.db"
    GROQ_API_KEY: Optional[str] = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: Optional[str] = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
