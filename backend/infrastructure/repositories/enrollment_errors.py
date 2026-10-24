"""Traduce los códigos y mensajes de las RPC antiguas en errores de dominio."""
from domain.errors import EntityNotFound, EnrollmentConflict, MembershipRequired
from infrastructure.http_transport import database_code, error_payload


def raise_schedule_enrollment_error(error):
    code = database_code(error)
    message = str(error_payload(error).get("message") or error).lower()
    # Las RPC históricas emiten P0001 con estos mensajes. La compatibilidad
    # termina aquí: las capas interiores y HTTP reciben tipos estables.
    if code == "23505" or "23505" in message or "ya esta matriculado" in message:
        raise EnrollmentConflict("El cliente ya esta matriculado en este horario") from error
    if "sin cupos" in message:
        raise EnrollmentConflict("Horario sin cupos disponibles") from error
    if "sin membresia activa" in message:
        raise MembershipRequired("Cliente sin membresia activa") from error
    if code == "23503" or "23503" in message or "horario no disponible" in message:
        raise EntityNotFound("Horario no disponible") from error
    raise error
