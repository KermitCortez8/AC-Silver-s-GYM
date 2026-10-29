# Módulo: trainer_routes.
# Expone rutinas y seguimiento para entrenadores.
# Comprueba permisos antes de modificar planes de trabajo.
# Organiza el progreso registrado para cada cliente.
from __future__ import annotations

from presentation.error_handlers import http_error

from fastapi import APIRouter, Depends, Query, status

from presentation.dependencies import get_gym_service, require_internal_viewer
from domain.errors import MembershipRequired
from domain.models.gym import CatalogoRutinaInput, MatriculaRutinaInput, RutinaProgresoInput
from application.services.gym_service import GymService

router = APIRouter(prefix="/trainer", tags=["trainer"])


@router.get("/overview")
# Procesa esta operación.
def trainer_overview(
    gym_service: GymService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    return gym_service.trainer_overview()


@router.post("/rutinas")
# Actualiza el registro correspondiente.
def upsert_trainer_rutina(
    payload: CatalogoRutinaInput,
    gym_service: GymService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.upsert_rutina(payload.model_dump())
    except (ValueError, RuntimeError, OSError, PermissionError) as error:
        raise http_error(error, validation_status=status.HTTP_400_BAD_REQUEST) from error


@router.post("/matriculas/{id_matricula}/rutina")
# Procesa esta operación.
def assign_trainer_rutina(
    id_matricula: int,
    payload: MatriculaRutinaInput,
    gym_service: GymService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.asignar_rutina_matricula(id_matricula, payload.id_rutina)
    except (ValueError, RuntimeError, OSError, PermissionError) as error:
        detail = str(error)
        if isinstance(error, MembershipRequired):
            detail = "El cliente no cuenta con una membresía activa para asignarle rutinas."
        translated = http_error(error)
        if isinstance(error, MembershipRequired):
            translated.detail = detail
        raise translated from error


@router.get("/clientes-rutinas")
# Procesa esta operación.
def trainer_cliente_rutinas(
    dni: str = Query(pattern=r"^[0-9]{8}$"),
    gym_service: GymService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    try:
        return gym_service.trainer_rutinas_cliente(dni)
    except (ValueError, RuntimeError, OSError, PermissionError) as error:
        raise http_error(error) from error


@router.post("/matriculas/{id_matricula}/progreso")
# Procesa esta operación.
def trainer_rutina_progreso(
    id_matricula: int,
    payload: RutinaProgresoInput,
    gym_service: GymService = Depends(get_gym_service),
    current_user=Depends(require_internal_viewer),
):
    try:
        data = payload.model_dump()
        data["id_usuario"] = current_user.id_usuario or current_user.id
        return gym_service.registrar_progreso_rutina(id_matricula, data)
    except (ValueError, RuntimeError, OSError, PermissionError) as error:
        detail = str(error)
        if isinstance(error, MembershipRequired):
            detail = "El cliente no cuenta con una membresía activa para registrar progresos."
        translated = http_error(error)
        if isinstance(error, MembershipRequired):
            translated.detail = detail
        raise translated from error
