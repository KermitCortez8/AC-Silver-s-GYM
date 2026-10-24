# Módulo: presentation.dependencies.
# Reúne operaciones relacionadas con esta parte del backend.
# Conserva aquí las validaciones propias de este flujo.
# Los accesos externos se mantienen separados de las reglas de negocio.
from __future__ import annotations

from functools import lru_cache
import logging

from fastapi import Depends, Header, HTTPException, Request, status

from infrastructure.config import Settings, get_settings
from domain.models.auth import UserProfile
from application.services.auth_service import AuthService, ClientActivationRequired
from application.services.clients_service import ClientsService
from application.services.gym_service import GymService
from application.errors import SchemaNotReady
from app.bootstrap import create_gym_service, create_identity_service, create_store_images_service
from application.services.users_service import UsersService
from infrastructure.security import verify_session_token

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
# Obtiene los datos necesarios.
def _get_supabase_gym_service(supabase_url: str, supabase_key: str) -> GymService:
    return create_gym_service(supabase_url, supabase_key)


# Obtiene los datos necesarios.
def get_gym_service(request: Request = None) -> GymService:
    settings = get_settings()
    if not settings.has_supabase_credentials:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La conexión con la base de datos no está configurada. Contacta con administración.",
        )
    try:
        return _get_supabase_gym_service(settings.supabase_url, settings.supabase_key)
    except SchemaNotReady as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (RuntimeError, OSError) as error:
        # No se sustituye una credencial rechazada por otra de menores permisos.
        logger.warning("Error al iniciar el repositorio (%s)", type(error).__name__)
        raise HTTPException(status_code=503, detail="No se pudo conectar con la base de datos. Inténtalo de nuevo en unos momentos.") from error


# Obtiene los datos necesarios.
def get_clients_service(gym_service: GymService = Depends(get_gym_service)) -> ClientsService:
    return ClientsService(gym_service)


# Obtiene los datos necesarios.
def get_users_service(gym_service: GymService = Depends(get_gym_service)) -> UsersService:
    return UsersService(gym_service)


# Obtiene los datos necesarios.
def get_current_user(
    authorization: str | None = Header(default=None),
    gym_service: GymService = Depends(get_gym_service),
) -> UserProfile:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Token inválido")
    try:
        payload = verify_session_token(token.strip())
        if not payload:
            raise ValueError("La sesión es inválida o venció. Inicia sesión nuevamente.")
        return AuthService(gym_service).user_from_payload(payload)
    except ClientActivationRequired as error:
        raise HTTPException(status_code=403, detail={"code": error.code, "message": str(error)}) from error
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


# Usuario interno que origina la operación (para MOV_INV.id_usuario); None si no hay sesión válida.
def get_optional_actor_id(
    authorization: str | None = Header(default=None),
    gym_service: GymService = Depends(get_gym_service),
) -> str | None:
    try:
        user = get_current_user(authorization, gym_service)
    except HTTPException:
        return None
    if user.role not in {"admin", "staff", "trainer"}:
        return None
    return user.id_usuario or None


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
    "get_optional_actor_id",
    "require_roles",
    "require_admin_or_staff",
    "require_internal_viewer",
]


def get_identity_service():
    return create_identity_service()


def get_store_images_service():
    return create_store_images_service(get_settings())


def get_client_payments_service(
    clients=Depends(get_clients_service), gym=Depends(get_gym_service), settings=Depends(get_settings),
):
    from app.bootstrap import create_client_payments_service
    return create_client_payments_service(clients, gym, settings)
