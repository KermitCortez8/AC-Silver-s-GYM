from __future__ import annotations

from fastapi import APIRouter, Depends, status

from dependencies import get_users_service
from models.gym import UsuarioInput
from services.users_service import UsersService

router = APIRouter(tags=["usuarios"])


@router.get("/usuarios")
def list_usuarios(users_service: UsersService = Depends(get_users_service)):
    return users_service.list_users()


@router.post("/usuarios")
def upsert_usuario(payload: UsuarioInput, users_service: UsersService = Depends(get_users_service)):
    return users_service.upsert_user(payload.model_dump())


@router.delete("/usuarios/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(id_usuario: str, users_service: UsersService = Depends(get_users_service)):
    users_service.delete_user(id_usuario)
