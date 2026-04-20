"""Application configuration loaded from environment variables and .env file."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings resolved from the environment.

    Attributes:
        app_name: Human-readable application name surfaced in OpenAPI docs.
        db_path: Filesystem path to the SQLite database file.
        log_level: Python logging level name (DEBUG, INFO, WARNING, ERROR).
        log_format: Structlog output format — ``"json"`` for production,
            ``"console"`` for local development.
        cors_origins: List of allowed CORS origins. Empty list disables CORS.
        debug: Enable FastAPI debug mode (detailed error pages, auto-reload).
    """

    app_name: str = Field(default="To Hatch")
    db_path: str = Field(default="hatch.db")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    cors_origins: list[str] = Field(default_factory=list)
    debug: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TO_HATCH_",
        case_sensitive=False,
    )


settings = Settings()
