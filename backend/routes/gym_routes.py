from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import CatalogoRutinaInput, ConfiguracionGimnasioInput, HorarioInput, SummaryResponse, TicketAtencionInput
from services.gym_service import GymService

router = APIRouter(prefix="/gym", tags=["gym-operaciones"])


# GET /gym/summary: resume métricas del gimnasio y alertas de operación.
@router.get("/summary", response_model=SummaryResponse)
def summary(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.summary()




@router.get("/configuracion")
def get_configuracion(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.configuracion_gimnasio()


@router.post("/configuracion")
def update_configuracion(payload: ConfiguracionGimnasioInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.actualizar_configuracion_gimnasio(payload.model_dump())

# GET /gym/tickets: lista los tickets de atención registrados.
@router.get("/tickets")
def list_tickets(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.tickets()


# POST /gym/tickets: crea o actualiza un ticket de atención.
@router.post("/tickets")
def upsert_ticket(payload: TicketAtencionInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_ticket(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# GET /gym/rutinas: muestra el catálogo de rutinas.
@router.get("/rutinas")
def list_rutinas(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.catalogo_rutina()


# POST /gym/rutinas: crea o actualiza una rutina del catálogo.
@router.post("/rutinas")
def upsert_rutina(payload: CatalogoRutinaInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_rutina(payload.model_dump())


# GET /gym/horarios: lista los horarios cargados en el sistema.
@router.get("/horarios")
def list_horarios(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.horarios()


# POST /gym/horarios: crea o actualiza un horario asignado a un cliente y rutina.
@router.post("/horarios")
def upsert_horario(payload: HorarioInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
