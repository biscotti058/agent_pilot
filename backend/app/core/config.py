"""WorkFlow Assistant - configurazione centralizzata."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "WorkFlow Assistant"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://workflow:workflow_dev@postgres:5432/workflow_assistant"
    redis_url: str = "redis://redis:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Sanificazione documenti
    sanitize_company_domains: list[str] = []
    sanitize_company_keywords: list[str] = []

    @field_validator("sanitize_company_domains", "sanitize_company_keywords", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return [part.strip() for part in str(value).split(",") if part.strip()]


settings = Settings()
