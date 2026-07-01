"""
Centralized application configuration.
All settings are read from environment variables (with sane local defaults)
so the same codebase works across dev / staging / prod without code changes.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    PROJECT_NAME: str = "SecureTask API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # --- Database ---
    # Defaults to a local SQLite file so the project runs with zero external
    # dependencies out of the box. Point DATABASE_URL at Postgres/MySQL in
    # production (see README).
    DATABASE_URL: str = "sqlite:///./securetask.db"

    # --- Security / JWT ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key_please_rotate"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
