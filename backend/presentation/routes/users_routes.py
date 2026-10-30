# Módulo: users_routes.
# Gestiona las cuentas del personal del gimnasio.
# Permite crear, actualizar y eliminar usuarios internos.
# Restringe estas acciones a administradores y personal autorizado.
from __future__ import annotations

from presentation.error_handlers import http_error

from fastapi import APIRouter, Depends, status

from presentation.dependencies import get_users_service, require_admin_or_staff
from domain.models.gym import UsuarioInput
from application.services.users_service import UsersService

router = APIRouter(tags=["usuarios"])


@router.get("/usuarios")
# Obtiene los datos necesarios.
def list_usuarios(
    users_service: UsersService = Depends(get_users_service),
    _current_user=Depends(require_admin_or_staff),
):
    return users_service.list_users()


@router.post("/usuarios")
# Actualiza el registro correspondiente.
def upsert_usuario(
    payload: UsuarioInput,
    users_service: UsersService = Depends(get_users_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return users_service.upsert_user(payload.model_dump())
    except ValueError as error:
        raise http_error(error, validation_status=status.HTTP_400_BAD_REQUEST) from error


@router.delete("/usuarios/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
# Elimina el registro indicado.
def delete_usuario(
    id_usuario: str,
    users_service: UsersService = Depends(get_users_service),
    _current_user=Depends(require_admin_or_staff),
):
    users_service.delete_user(id_usuario)
