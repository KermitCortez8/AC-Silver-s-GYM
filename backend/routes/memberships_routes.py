from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import MembresiaInput, PlanMembresiaInput, RegistrarClienteMembresiaInput
from services.gym_service import GymService

router = APIRouter(tags=["membresias"])


@router.get("/planes-membresia")
def list_planes_membresia(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.planes_membresia()


@router.post("/planes-membresia")
def upsert_plan_membresia(payload: PlanMembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_plan_membresia(payload.model_dump())


@router.put("/planes-membresia/{id_pm}")
def update_plan_membresia(id_pm: int, payload: PlanMembresiaInput, gym_service: GymService = Depends(get_gym_service)):
    data = payload.model_dump()
    data["id_pm"] = id_pm
    return gym_service.upsert_plan_membresia(data)


@router.delete("/planes-membresia/{id_pm}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_membresia(id_pm: int, gym_service: GymService = Depends(get_gym_service)):
    try:
        gym_service.delete_plan_membresia(id_pm)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


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
