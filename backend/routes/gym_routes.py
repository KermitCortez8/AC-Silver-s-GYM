from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import (
    CatalogoRutinaInput,
    ConfiguracionGimnasioInput,
    HorarioInput,
    HorarioServicioInput,
    MatriculaHorarioInput,
    SummaryResponse,
    TicketAtencionInput,
)
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/gym", tags=["gym-operaciones"])


@router.get("/summary", response_model=SummaryResponse)
def summary(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.summary()


@router.get("/configuracion")
def get_configuracion(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.configuracion_gimnasio()


@router.post("/configuracion")
def update_configuracion(payload: ConfiguracionGimnasioInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.actualizar_configuracion_gimnasio(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/horarios-servicio")
def list_horarios_servicio(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.horarios_servicio()


@router.post("/horarios-servicio")
def upsert_horario_servicio(payload: HorarioServicioInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_horario_servicio(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/horarios-servicio/{id_horario_servicio}", status_code=status.HTTP_204_NO_CONTENT)
def delete_horario_servicio(id_horario_servicio: int, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        gym_service.delete_horario_servicio(id_horario_servicio)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/matriculas")
def list_matriculas(
    id_cliente: int | None = None,
    dni: str | None = None,
    gym_service: GymDomainService = Depends(get_gym_service),
):
    try:
        return gym_service.matriculas_horario(id_cliente=id_cliente, dni=dni)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/matriculas")
def create_matricula(payload: MatriculaHorarioInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.matricular_cliente_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/matriculas/{id_matricula}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matricula(id_matricula: int, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        gym_service.cancelar_matricula_horario(id_matricula)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/tickets")
def list_tickets(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.tickets()


@router.post("/tickets")
def upsert_ticket(payload: TicketAtencionInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_ticket(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/rutinas")
def list_rutinas(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.catalogo_rutina()


@router.post("/rutinas")
def upsert_rutina(payload: CatalogoRutinaInput, gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.upsert_rutina(payload.model_dump())


@router.get("/horarios")
def list_horarios(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.horarios()


@router.post("/horarios")
def upsert_horario(payload: HorarioInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
