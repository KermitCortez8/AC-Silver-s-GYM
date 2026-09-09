# Módulo: gym_routes.
# Agrupa horarios, matrículas y configuración del gimnasio.
# Controla el acceso según el rol de la sesión.
# Entrega respuestas HTTP a partir del servicio de dominio.
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service, require_admin_or_staff, require_internal_viewer, require_roles
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


def _cliente_id_from_session(current_user) -> int:
    try:
        return int(current_user.id_cliente or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def _require_session_cliente_id(current_user) -> int:
    id_cliente = _cliente_id_from_session(current_user)
    if id_cliente <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sesión no está vinculada a un cliente registrado",
        )
    return id_cliente


def _enrollment_error_status(error: ValueError) -> int:
    message = str(error).lower()
    if "ya esta matriculado" in message or "ya está matriculado" in message or "sin cupos" in message:
        return status.HTTP_409_CONFLICT
    if "sin membresia activa" in message or "sin membresía activa" in message:
        return status.HTTP_403_FORBIDDEN
    return status.HTTP_400_BAD_REQUEST


@router.get("/summary", response_model=SummaryResponse)
# Procesa esta operación.
def summary(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    return gym_service.summary()


@router.get("/configuracion")
# Obtiene los datos necesarios.
def get_configuracion(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    return gym_service.configuracion_gimnasio()


@router.post("/configuracion")
# Actualiza el registro correspondiente.
def update_configuracion(
    payload: ConfiguracionGimnasioInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return gym_service.actualizar_configuracion_gimnasio(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/horarios-servicio")
# Obtiene los datos necesarios.
def list_horarios_servicio(
    gym_service: GymDomainService = Depends(get_gym_service),
    current_user=Depends(require_roles("admin", "staff", "user")),
):
    return gym_service.horarios_servicio(solo_activos=current_user.role == "user")


@router.post("/horarios-servicio")
# Actualiza el registro correspondiente.
def upsert_horario_servicio(
    payload: HorarioServicioInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return gym_service.upsert_horario_servicio(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/horarios-servicio/{id_horario_servicio}", status_code=status.HTTP_204_NO_CONTENT)
# Elimina el registro indicado.
def delete_horario_servicio(
    id_horario_servicio: int,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        gym_service.delete_horario_servicio(id_horario_servicio)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/matriculas")
# Obtiene los datos necesarios.
def list_matriculas(
    id_cliente: int | None = None,
    dni: str | None = None,
    gym_service: GymDomainService = Depends(get_gym_service),
    current_user=Depends(require_roles("admin", "staff", "user")),
):
    try:
        if current_user.role == "user":
            return gym_service.matriculas_horario(
                id_cliente=_require_session_cliente_id(current_user),
                solo_activas=True,
            )
        return gym_service.matriculas_horario(id_cliente=id_cliente, dni=dni)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/matriculas")
# Crea el registro correspondiente.
def create_matricula(
    payload: MatriculaHorarioInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    current_user=Depends(require_roles("admin", "staff", "user")),
):
    try:
        enrollment = payload.model_dump()
        if current_user.role == "user":
            enrollment["id_cliente"] = _require_session_cliente_id(current_user)
            enrollment["dni"] = ""
        return gym_service.matricular_cliente_horario(enrollment)
    except ValueError as error:
        raise HTTPException(status_code=_enrollment_error_status(error), detail=str(error)) from error


@router.delete("/matriculas/{id_matricula}", status_code=status.HTTP_204_NO_CONTENT)
# Elimina el registro indicado.
def delete_matricula(
    id_matricula: int,
    gym_service: GymDomainService = Depends(get_gym_service),
    current_user=Depends(require_roles("admin", "staff", "user")),
):
    try:
        id_cliente = _require_session_cliente_id(current_user) if current_user.role == "user" else None
        gym_service.cancelar_matricula_horario(id_matricula, id_cliente=id_cliente)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/tickets")
# Obtiene los datos necesarios.
def list_tickets(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    return gym_service.tickets()


@router.post("/tickets")
# Actualiza el registro correspondiente.
def upsert_ticket(
    payload: TicketAtencionInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return gym_service.upsert_ticket(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/rutinas")
# Obtiene los datos necesarios.
def list_rutinas(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_internal_viewer),
):
    return gym_service.catalogo_rutina()


@router.post("/rutinas")
# Actualiza el registro correspondiente.
def upsert_rutina(
    payload: CatalogoRutinaInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    return gym_service.upsert_rutina(payload.model_dump())


@router.get("/horarios")
# Obtiene los datos necesarios.
def list_horarios(
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    return gym_service.horarios()


@router.post("/horarios")
# Actualiza el registro correspondiente.
def upsert_horario(
    payload: HorarioInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return gym_service.upsert_horario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
