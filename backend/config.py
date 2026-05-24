from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AC Silver's GYM API"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
    ]
    db_file: Path = Path(__file__).resolve().parent / "db" / "state.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
