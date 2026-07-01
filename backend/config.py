from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


class Settings(BaseModel):
    app_name: str = "AC Silver's GYM API"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
    ]
    supabase_url: str = ""
    supabase_key: str = ""
    store_images_dir: str = ""

    @property
    def has_supabase_credentials(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)


@lru_cache
def get_settings() -> Settings:
    backend_dir = Path(__file__).resolve().parent
    _load_env_file(backend_dir / ".env")
    _load_env_file(backend_dir.parent / ".env")

    cors_origins = [
        origin.strip()
        for origin in (os.getenv("CORS_ORIGINS") or "http://localhost:5173,http://localhost:5174").split(",")
        if origin.strip()
    ]

    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
        or ""
    )

    return Settings(
        host=(os.getenv("BACKEND_HOST") or "0.0.0.0").strip(),
        port=int(os.getenv("BACKEND_PORT") or "8000"),
        cors_origins=cors_origins,
        supabase_url=(os.getenv("SUPABASE_URL") or "").strip().rstrip("/"),
        supabase_key=supabase_key.strip(),
        store_images_dir=(os.getenv("STORE_IMAGES_DIR") or str(backend_dir / "db" / "store-images")).strip(),
    )
