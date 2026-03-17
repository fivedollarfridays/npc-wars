"""Server configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _get_cors_origins() -> str:
    return os.environ.get("NPCWARS_CORS_ORIGINS", "http://localhost:8000,http://localhost:3000")


@dataclass
class Settings:
    """Server configuration from environment variables."""

    redis_url: str = field(default_factory=lambda: os.environ.get("REDIS_URL", "redis://localhost:6379"))
    results_dir: str = field(default_factory=lambda: os.environ.get("RESULTS_DIR", "results"))
    db_path: str = field(default_factory=lambda: os.environ.get("DB_PATH", "data/npcwars.db"))
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8000")))
    cors_origins: str = field(default_factory=_get_cors_origins)

    def __repr__(self) -> str:
        return (
            f"Settings(redis_url={self.redis_url!r}, results_dir={self.results_dir!r}, "
            f"db_path={self.db_path!r}, port={self.port})"
        )
