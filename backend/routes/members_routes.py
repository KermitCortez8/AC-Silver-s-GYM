from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import (
    ClienteInput,
    MembresiaInput,
    PlanMembresiaInput,
    RegistrarClienteMembresiaInput,
    UsuarioInput,
)
from services.gym_service import GymService

router = APIRouter(tags=["usuarios-clientes-membresia"])


# GET /usuarios: lista los usuarios del sistema.
@router.get("/usuarios")
def list_usuarios(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.usuarios()


# POST /usuarios: crea o actualiza un usuario.
@router.post("/usuarios")
def upsert_usuario(payload: UsuarioInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_usuario(payload.model_dump())


# DELETE /usuarios/{id_usuario}: elimina un usuario por id.
@router.delete("/usuarios/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(id_usuario: int, gym_service: GymService = Depends(get_gym_service)):
    gym_service.delete_usuario(id_usuario)


# GET /clientes: lista los clientes registrados.
@router.get("/clientes")
def list_clientes(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.clientes()


# POST /clientes: crea o actualiza un cliente.
@router.post("/clientes")
def upsert_cliente(payload: ClienteInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_cliente(payload.model_dump())


# DELETE /clientes/{id_cliente}: elimina un cliente y sus datos relacionados.
@router.delete("/clientes/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(id_cliente: int, gym_service: GymService = Depends(get_gym_service)):
    gym_service.delete_cliente(id_cliente)


# GET /planes-membresia: lista los planes disponibles.
@router.get("/planes-membresia")
def list_planes_membresia(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.planes_membresia()


# POST /planes-membresia: crea o actualiza un plan de membresía.
@router.post("/planes-membresia")
def upsert_plan_membresia(payload: PlanMembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_plan_membresia(payload.model_dump())


# GET /membresias: lista todas las membresías.
@router.get("/membresias")
def list_membresias(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.membresias()


# POST /membresias: crea una membresía para un cliente.
@router.post("/membresias")
def crear_membresia(payload: MembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.crear_membresia(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# GET /clientes/{id_cliente}/membresias: muestra el historial de membresías del cliente.
@router.get("/clientes/{id_cliente}/membresias")
def membresias_por_cliente(id_cliente: int, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.membresias_por_cliente(id_cliente)


# POST /registro-cliente-membresia: registra cliente y membresía en un solo paso.
@router.post("/registro-cliente-membresia")
def registrar_cliente_membresia(payload: RegistrarClienteMembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_cliente_con_membresia(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
