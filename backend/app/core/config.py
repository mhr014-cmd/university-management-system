"""
Application configuration / environment settings.

Single source of truth for environment-driven config, per
docs/System_Architecture.md Section 11 (Secrets management via environment
configuration, never committed to source control).
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database — required, no default. Missing this fails startup (Configuration Validation).
    database_url: str = Field(alias="DATABASE_URL")

    # JWT / Auth — required now so config validation is complete ahead of Milestone 2;
    # no authentication logic is implemented in this milestone.
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # API
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # CORS — comma-separated list of allowed origins.
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — use as a FastAPI dependency or module-level import."""
    return Settings()  # type: ignore[call-arg]  # values sourced from environment/.env
