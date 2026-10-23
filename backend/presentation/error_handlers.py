"""Traduce fallos de los puertos también cuando ocurren dentro de una consulta."""
from fastapi.responses import JSONResponse

from application.errors import PersistenceUnavailable, SchemaNotReady


def install_error_handlers(app):
    @app.exception_handler(PersistenceUnavailable)
    async def persistence_unavailable(_request, error):
        message = str(error) if isinstance(error, SchemaNotReady) else (
            "No se pudo conectar con la base de datos. Inténtalo de nuevo en unos momentos.")
        return JSONResponse(status_code=503, content={"detail": message})
