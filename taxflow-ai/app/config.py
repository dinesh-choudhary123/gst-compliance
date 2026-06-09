"""Central configuration for TaxFlow AI."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # App
    APP_NAME: str = "TaxFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CLIENT_DATA_DIR: Path = BASE_DIR / "client_data"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2:latest"
    OLLAMA_TEMPERATURE: float = 0.1
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_MAX_TOKENS: int = 4096

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'taxflow.db'}"
    ENCRYPTION_KEY: Optional[str] = None  # Auto-generated if not set

    # Auth
    SECRET_KEY: str = "taxflow-ai-local-secret-change-in-production"
    SESSION_EXPIRE_HOURS: int = 24

    # Document Processing
    MAX_UPLOAD_SIZE_MB: int = 50
    SUPPORTED_EXTENSIONS: list[str] = [
        ".pdf", ".csv", ".xlsx", ".xls", ".json", ".xml", ".txt", ".jpg", ".png"
    ]

    # Gradio
    GRADIO_SERVER_PORT: int = 7860
    GRADIO_SHARE: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.CLIENT_DATA_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
