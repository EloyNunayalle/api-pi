from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # ============================================================
    # PostgreSQL (psycopg2)
    # ============================================================
    POSTGRES_HOST: str
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SCHEMA: str = Field(default="public")

    # URL completa (usada en algunos casos)
    DATABASE_URL: str

    # ============================================================
    # FastAPI
    # ============================================================
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)

    # CORS
    ALLOWED_ORIGINS: list[str] = Field(default=["*"])

    # ============================================================
    # Azure OpenAI (solo generativa, GPT-4o-mini)
    # ============================================================
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT: str = Field(default="gpt-4o-mini")

    # ============================================================
    # VALIDADORES
    # ============================================================
    @field_validator("POSTGRES_PORT", "API_PORT", mode="before")
    @classmethod
    def validate_port_integers(cls, v: Any) -> int:
        if v in (None, ""):
            return 5432
        try:
            return int(v)
        except Exception:
            return 5432

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Any) -> str:
        if not v:
            raise ValueError("DATABASE_URL es requerido en el archivo .env")
        return str(v)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_boolean(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower().strip() in ("true", "1", "yes", "on")
        return bool(v)

    class Config:
        env_file = str(ENV_FILE)


settings = Settings()
