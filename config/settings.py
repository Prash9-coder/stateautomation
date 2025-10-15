from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Make API keys optional to allow offline operation
    GROQ_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = ""
    # Default to offline; can be set to "groq" or "gemini"
    LLM_PROVIDER: str = "offline"
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    GEMINI_MODEL: str = "gemini-pro"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER: str = "uploads"
    TEMP_FOLDER: str = "temp"
    AUDIT_LOG_FILE: str = "audit_log.jsonl"

    class Config:
        env_file = ".env"


settings = Settings()