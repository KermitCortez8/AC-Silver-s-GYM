from __future__ import annotations

from functools import lru_cache

from config import get_settings
from services.clients_service import ClientsService
from services.supabase_gym_service import SupabaseGymService
from services.users_service import UsersService


@lru_cache(maxsize=1)
def _get_supabase_gym_service(supabase_url: str, supabase_key: str) -> SupabaseGymService:
    return SupabaseGymService(supabase_url, supabase_key)


def get_gym_service() -> SupabaseGymService:
    settings = get_settings()
    if not settings.has_supabase_credentials:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY o SUPABASE_ANON_KEY en backend/.env")
    service = _get_supabase_gym_service(settings.supabase_url, settings.supabase_key)
    service.ensure_fresh()
    return service


def get_clients_service() -> ClientsService:
    return ClientsService(get_gym_service())


def get_users_service() -> UsersService:
    return UsersService(get_gym_service())

__all__ = ["get_gym_service", "get_clients_service", "get_users_service"]
