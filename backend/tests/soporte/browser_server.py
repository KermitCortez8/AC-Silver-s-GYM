"""Servidor exclusivo de Playwright: API real, cuentas sintéticas y memoria volátil.

No se importa desde app.main ni incorpora endpoints QA a producción.
"""
from pathlib import Path
import os
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def create_app():
    if os.environ.get("GYM_BROWSER_TESTS") != "1" or not os.environ.get("GYM_QA_KEY"):
        raise RuntimeError("Servidor exclusivo de las pruebas de navegador")
    # No cargar secretos ni proveedores del entorno de la aplicación.
    os.environ["AUTH_SECRET_KEY"] = "browser-only-synthetic-session-secret-0123456789abcdef"
    from fastapi import FastAPI, Header, HTTPException
    from infrastructure.config import get_settings
    from infrastructure.services.local_gym_service import LocalGymService
    from presentation import dependencies as deps
    from presentation.error_handlers import install_error_handlers
    from presentation.routes import (
        auth_routes, gym_routes, inventory_routes, store_routes, attendance_routes,
        clients_routes, memberships_routes, promotions_routes, trainer_routes, users_routes,
    )

    get_settings.cache_clear()
    app = FastAPI(title="API aislada de pruebas visuales")
    install_error_handlers(app)
    gym = LocalGymService()

    def reset():
        initial = LocalGymService()
        gym.state = initial.state
        gym.state["usuario"] = [gym._normalize_usuario_record({
            "id_usuario": "SGADM001", "nombre": "Admin QA", "rol": "admin",
            "correo": "admin@example.test", "estado": "ACTIVO", "dni": "99999999",
            "password_hash": gym.passwords.hash("Prueba-Navegador-2026!"),
        })]
        for key in ("inventario", "inventario_unidades", "mov_inv", "productos_tienda", "pedidos_tienda"):
            gym.state[key] = []

    reset()
    app.dependency_overrides[deps.get_gym_service] = lambda: gym
    for module in (auth_routes, gym_routes, inventory_routes, store_routes, attendance_routes,
                   clients_routes, memberships_routes, promotions_routes, trainer_routes, users_routes):
        app.include_router(module.router, prefix="/api")

    @app.get("/__qa/health")
    def health():
        return {"status": "ok", "repository": "memory", "synthetic": True}

    @app.post("/__qa/reset")
    def reset_test(x_qa_key: str = Header(default="")):
        if not secrets.compare_digest(x_qa_key, os.environ["GYM_QA_KEY"]):
            raise HTTPException(status_code=403, detail="Entorno de prueba aislado")
        reset()
        return {"status": "reset"}

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8011, log_level="warning")
