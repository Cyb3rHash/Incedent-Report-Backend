from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


def _get_env(name: str, default: str | None = None) -> str | None:
    # Small helper to keep config parsing consistent.
    return os.getenv(name, default)


def _parse_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    """Typed configuration for the service.

    Contract:
      - DATABASE_URL is optional. If missing, the server can still start, but any endpoint
        requiring database access must return a clear error response.
      - ALLOWED_ORIGINS is optional CSV.
      - LOG_LEVEL is optional and used by logging config.

    Errors:
      - Does not raise for missing DATABASE_URL (DB is optional at startup).
    """

    app_name: str
    app_version: str
    database_url: Optional[str]
    allowed_origins: List[str]
    log_level: str

    @staticmethod
    def from_env() -> "Settings":
        database_url = _get_env("DATABASE_URL")

        return Settings(
            app_name=_get_env("APP_NAME", "Incident Report Backend") or "Incident Report Backend",
            app_version=_get_env("APP_VERSION", "0.1.0") or "0.1.0",
            database_url=database_url,
            allowed_origins=_parse_csv(_get_env("ALLOWED_ORIGINS")),
            log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
        )


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Get Settings loaded from environment variables.

    Contract:
      - Reads environment exactly once per call and returns a typed Settings object.
      - Intended to be called at the FastAPI boundary (startup/main) and then passed down.

    Returns:
      Settings: Typed configuration.
    """
    return Settings.from_env()
