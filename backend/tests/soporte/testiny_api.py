"""API real con repositorio en memoria y perfiles QA; sin proveedores externos."""
from types import SimpleNamespace
from copy import deepcopy

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from domain.models.auth import UserProfile
from infrastructure.config import Settings
from infrastructure.services.local_gym_service import LocalGymService
from presentation import dependencies as deps
from presentation.error_handlers import install_error_handlers
from presentation.routes import clients_routes, gym_routes, inventory_routes, memberships_routes, store_routes, trainer_routes, users_routes


def business_state(api):
    """Excluye contadores internos de asignación; compara todos los recursos de negocio."""
    return deepcopy({key: value for key, value in api.gym.state.items() if not key.startswith("_")})


@pytest.fixture
def documented_api():
    gym = LocalGymService()
    gym.state["usuario"] = [{"id_usuario": "SGADM001", "nombre": "Admin QA", "rol": "admin",
                              "correo": "admin@example.com", "telefono": "999999999", "dni": "99999999", "estado": "ACTIVO"}]
    gym.state["clientes"] = [{"id_cliente": i, "id_usuario": f"SGCLI{i:03}", "nombre": f"Cliente QA {i}",
                              "dni": str(i) * 8, "correo": f"cliente{i}@example.com", "estado": "ACTIVO"}
                             for i in (1, 2)]
    gym.state["membresia"] = [{"id_membresia": i, "id_cliente": i, "estado": "ACTIVO", "estado_pago": "PAGADO",
                               "fecha_inicio": "2020-01-01", "fecha_fin": "2099-12-31"} for i in (1, 2)]
    actor = [UserProfile(id="SGADM001", id_usuario="SGADM001", name="Admin QA", email="admin@example.com", role="admin")]

    def login(role, client_id=1):
        identity = f"SGCLI{client_id:03}" if role == "user" else "SGADM001"
        actor[0] = UserProfile(id=identity, id_usuario=identity, name="Actor QA", email="actor@example.com",
                               role=role, id_cliente=client_id if role == "user" else None)

    app = FastAPI()
    install_error_handlers(app)
    app.dependency_overrides[deps.get_gym_service] = lambda: gym
    app.dependency_overrides[deps.get_current_user] = lambda: actor[0]
    app.dependency_overrides[deps.get_optional_actor_id] = lambda: actor[0].id_usuario
    app.dependency_overrides[deps.get_settings] = lambda: Settings(auth_secret_key="synthetic-test-key-" * 3)
    for module in (clients_routes, gym_routes, inventory_routes, memberships_routes, store_routes, trainer_routes, users_routes):
        app.include_router(module.router, prefix="/api")
    with TestClient(app) as client:
        yield SimpleNamespace(gym=gym, client=client, login=login)
