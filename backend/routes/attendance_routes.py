from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import CheckinAsistenciaDniInput, CheckinAsistenciaInput
from services.gym_service import GymService

router = APIRouter(prefix="/asistencia", tags=["asistencia"])


# GET /asistencia: lista todos los registros de asistencia.
@router.get("")
def list_asistencia(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.asistencia()


# POST /asistencia/checkin: marca asistencia usando el id del cliente.
@router.post("/checkin")
def checkin(payload: CheckinAsistenciaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_asistencia(payload.id_cliente)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# POST /asistencia/checkin-dni: marca asistencia usando el DNI del cliente.
@router.post("/checkin-dni")
def checkin_dni(payload: CheckinAsistenciaDniInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_asistencia_por_dni(payload.dni)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
