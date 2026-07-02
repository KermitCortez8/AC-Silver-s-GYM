from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service, require_internal_viewer
from models.gym import CatalogoRutinaInput, MatriculaRutinaInput, RutinaProgresoInput
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/trainer", tags=["trainer"])


@router.get("/overview")
def trainer_overview(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    return gym_service.trainer_overview()


@router.post("/rutinas")
def upsert_trainer_rutina(
    payload: CatalogoRutinaInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.upsert_rutina(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/matriculas/{id_matricula}/rutina")
def assign_trainer_rutina(
    id_matricula: int,
    payload: MatriculaRutinaInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.asignar_rutina_matricula(id_matricula, payload.id_rutina)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/clientes-rutinas")
def trainer_cliente_rutinas(
    dni: str,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.trainer_rutinas_cliente(dni)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/matriculas/{id_matricula}/progreso")
def trainer_rutina_progreso(
    id_matricula: int,
    payload: RutinaProgresoInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.registrar_progreso_rutina(id_matricula, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
