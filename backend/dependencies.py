# Módulo: dependencies.
# Reúne operaciones relacionadas con esta parte del backend.
# Conserva aquí las validaciones propias de este flujo.
# Los accesos externos se mantienen separados de las reglas de negocio.
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from config import get_settings
from models.auth import UserProfile
from services.auth_service import AuthService
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService
from services.users_service import UsersService
from utils.security import decode_token_payload


@lru_cache(maxsize=1)
# Obtiene los datos necesarios.
def _get_supabase_gym_service(supabase_url: str, supabase_key: str) -> SupabaseGymService:
    return SupabaseGymService(supabase_url, supabase_key)


@lru_cache(maxsize=1)
# Obtiene los datos necesarios.
def _get_local_gym_service() -> LocalGymService:
    return LocalGymService()


# Obtiene los datos necesarios.
def get_gym_service() -> SupabaseGymService:
    settings = get_settings()
    if not settings.has_supabase_credentials:
        return _get_local_gym_service()
    candidate_keys = [
        key
        for key in (settings.supabase_key, settings.supabase_anon_key)
        if key and settings.supabase_url
    ]
    seen: set[str] = set()
    for key in candidate_keys:
        if key in seen:
            continue
        seen.add(key)
        try:
            service = _get_supabase_gym_service(settings.supabase_url, key)
            service.ensure_fresh()
            return service
        except RuntimeError:
            continue
    return _get_local_gym_service()


# Obtiene los datos necesarios.
def get_clients_service() -> ClientsService:
    return ClientsService(get_gym_service())


# Obtiene los datos necesarios.
def get_users_service() -> UsersService:
    return UsersService(get_gym_service())


# Obtiene los datos necesarios.
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


# Procesa esta operación.
def require_roles(*roles: str):
    allowed_roles = {str(role).strip().lower() for role in roles}

    # Procesa esta operación.
    def _dependency(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if str(current_user.role).strip().lower() not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
        return current_user

    return _dependency


# Procesa esta operación.
def require_admin_or_staff(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if current_user.role not in {"admin", "staff"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")
    return current_user


# Procesa esta operación.
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
