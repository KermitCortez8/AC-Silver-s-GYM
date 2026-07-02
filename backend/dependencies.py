from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from config import get_settings
from models.auth import UserProfile
from services.auth_service import AuthService
from services.clients_service import ClientsService
from services.supabase_gym_service import SupabaseGymService
from services.users_service import UsersService
from utils.security import decode_token_payload


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


def get_current_user(
    authorization: str | None = Header(default=None),
    gym_service: SupabaseGymService = Depends(get_gym_service),
) -> UserProfile:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_token_payload(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return AuthService(gym_service).user_from_payload(payload)


def require_roles(*roles: str):
    allowed_roles = {str(role).strip().lower() for role in roles}

    def _dependency(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if str(current_user.role).strip().lower() not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
        return current_user

    return _dependency


def require_admin_or_staff(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if current_user.role not in {"admin", "staff"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
    return current_user


def require_internal_viewer(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if current_user.role not in {"admin", "staff", "trainer"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
    return current_user


__all__ = [
    "get_gym_service",
    "get_clients_service",
    "get_users_service",
    "get_current_user",
    "require_roles",
    "require_admin_or_staff",
    "require_internal_viewer",
]
