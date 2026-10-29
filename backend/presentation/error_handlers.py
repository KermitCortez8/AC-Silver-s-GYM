"""Traducción común de errores de negocio, validación y servicios externos."""
import logging

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from application.errors import PersistenceUnavailable, SchemaNotReady
from domain.errors import AttendanceConflict, EnrollmentConflict, EntityNotFound, MembershipRequired
from domain.services.gym_values import PedidoCanceladoConPagoError

logger = logging.getLogger(__name__)


def http_error(error, *, validation_status=400):
    """Preserve domain status codes without exposing provider exceptions."""
    if isinstance(error, ValidationError):
        logger.warning("Datos internos inválidos (%s)", type(error).__name__)
        return HTTPException(500, "No se pudo completar la operación. Contacta con administración.")
    if isinstance(error, SchemaNotReady):
        return HTTPException(503, str(error))
    if isinstance(error, PersistenceUnavailable):
        return HTTPException(503, "No se pudo conectar con la base de datos. Inténtalo de nuevo en unos momentos.")
    if isinstance(error, EntityNotFound):
        return HTTPException(404, str(error))
    if isinstance(error, PersistenceUnavailable) and getattr(error, "code", None) == "23503":
        # Llave foránea: el registro tiene historial que lo referencia; no es un fallo de conexión.
        return HTTPException(409, "No se puede completar: el registro tiene historial relacionado (ventas o movimientos).")
    if isinstance(error, (MembershipRequired, PermissionError)):
        return HTTPException(403, str(error))
    if isinstance(error, (AttendanceConflict, EnrollmentConflict, PedidoCanceladoConPagoError)):
        return HTTPException(409, str(error))
    if isinstance(error, (RuntimeError, OSError)):
        logger.warning("Servicio no disponible (%s)", type(error).__name__)
        return HTTPException(503, "El servicio no está disponible temporalmente. Inténtalo de nuevo en unos momentos.")
    return HTTPException(validation_status, str(error))


def _validation_detail(error):
    # Do not echo input values (passwords/tokens) or non-serializable validator contexts.
    return [{"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
            for item in error.errors()]


def install_error_handlers(app):
    async def known_error(_request, error):
        translated = http_error(error)
        return JSONResponse(status_code=translated.status_code, content={"detail": translated.detail})

    for error_type in (ValueError, PermissionError, RuntimeError, OSError):
        app.add_exception_handler(error_type, known_error)

    async def invalid_input(_request, error):
        return JSONResponse(status_code=422, content={"detail": _validation_detail(error)})

    app.add_exception_handler(RequestValidationError, invalid_input)
    app.add_exception_handler(ValidationError, known_error)

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={
            "detail": "No se pudo completar la operación. Inténtalo de nuevo o contacta con administración.",
        })
