from __future__ import annotations

from functools import lru_cache

from config import get_settings
from services.clients_service import ClientsService
from services.gym_service import GymService
from services.users_service import UsersService


@lru_cache
def get_gym_service() -> GymService:
	settings = get_settings()
	return GymService(settings.db_file)


@lru_cache
def get_clients_service() -> ClientsService:
	return ClientsService(get_gym_service())


@lru_cache
def get_users_service() -> UsersService:
	return UsersService(get_gym_service())

__all__ = ["get_gym_service", "get_clients_service", "get_users_service"]
