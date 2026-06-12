from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import (
    AsistenciaEntradaInput,
    AsistenciaSalidaInput,
    AsistenciaUpdateInput,
    CheckinAsistenciaDniInput,
    CheckinAsistenciaInput,
)
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
        return gym_service.registrar_asistencia_detallada(payload.dict())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# POST /asistencia/checkin-dni: marca asistencia usando el DNI del cliente.
@router.post("/checkin-dni")
def checkin_dni(payload: CheckinAsistenciaDniInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_asistencia_por_dni(payload.dict())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/entrada")
def registrar_entrada(payload: AsistenciaEntradaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_entrada_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/salida")
def registrar_salida(payload: AsistenciaSalidaInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_salida_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# PUT /asistencia/{id_asistencia}: edita fecha, hora, servicio o cliente del registro.
@router.put("/{id_asistencia}")
def update_asistencia(
    id_asistencia: int,
    payload: AsistenciaUpdateInput,
    gym_service: GymService = Depends(get_gym_service),
):
    try:
        return gym_service.actualizar_asistencia(id_asistencia, payload.model_dump(exclude_unset=True))
    except ValueError as error:
        status_code = status.HTTP_404_NOT_FOUND if "no encontrada" in str(error).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(error)) from error


# DELETE /asistencia/{id_asistencia}: elimina un registro de asistencia.
@router.delete("/{id_asistencia}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asistencia(id_asistencia: int, gym_service: GymService = Depends(get_gym_service)):
    try:
        gym_service.eliminar_asistencia(id_asistencia)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
