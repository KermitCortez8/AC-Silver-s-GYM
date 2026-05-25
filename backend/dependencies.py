from __future__ import annotations

from functools import lru_cache

from config import get_settings
from services.gym_service import GymService


@lru_cache
def get_gym_service() -> GymService:
	settings = get_settings()
	return GymService(settings.db_file)

__all__ = ["get_gym_service"]
