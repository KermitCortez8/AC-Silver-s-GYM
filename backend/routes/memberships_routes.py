from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import MembresiaInput, RegistrarClienteMembresiaInput
from services.gym_service import GymService

router = APIRouter(tags=["membresias"])


@router.get("/membresias")
def list_membresias(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.membresias()


@router.post("/membresias")
def crear_membresia(payload: MembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.crear_membresia(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/clientes/{id_cliente}/membresias")
def membresias_por_cliente(id_cliente: int, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.membresias_por_cliente(id_cliente)


@router.post("/registro-cliente-membresia")
def registrar_cliente_membresia(payload: RegistrarClienteMembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_cliente_con_membresia(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
