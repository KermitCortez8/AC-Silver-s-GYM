"""HTTP failure matrix using fake services only; no external credentials or writes."""
from copy import deepcopy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from application.errors import PersistenceUnavailable, SchemaNotReady
from domain.errors import EnrollmentConflict, EntityNotFound, MembershipRequired
from domain.models.auth import UserProfile
from infrastructure.services.local_gym_service import LocalGymService
from presentation import dependencies as deps
from presentation.error_handlers import install_error_handlers
from presentation.routes import (
    attendance_routes, auth_routes, clients_routes, gym_routes, inventory_routes,
    memberships_routes, promotions_routes, store_routes, trainer_routes, users_routes,
)


class FailingService:
    def __init__(self, error):
        self.error = error

    def __getattr__(self, _name):
        def fail(*_args, **_kwargs):
            raise self.error
        return fail


def api(error, monkeypatch):
    app = FastAPI()
    install_error_handlers(app)
    service = FailingService(error)
    for dependency in (deps.get_gym_service, deps.get_clients_service, deps.get_users_service,
                       deps.get_identity_service, deps.get_store_images_service, deps.get_client_payments_service):
        app.dependency_overrides[dependency] = lambda: service
    app.dependency_overrides[deps.get_current_user] = lambda: UserProfile(
        id="SGADM001", id_usuario="SGADM001", role="admin", name="Admin", email="admin@example.com")
    app.dependency_overrides[attendance_routes.service] = lambda: service
    monkeypatch.setattr(auth_routes, "AuthService", lambda _gym: service)
    for module in (attendance_routes, auth_routes, clients_routes, gym_routes, inventory_routes,
                   memberships_routes, promotions_routes, store_routes, trainer_routes, users_routes):
        app.include_router(module.router, prefix="/api")
    return TestClient(app, raise_server_exceptions=False)


ROUTES = [
    ("GET", "/api/usuarios", None),
    ("POST", "/api/usuarios", {"nombre": "Ana", "correo": "ana@gmail.com", "rol": "staff"}),
    ("DELETE", "/api/usuarios/SGSTA001", None),
    ("GET", "/api/clientes", None),
    ("DELETE", "/api/clientes/1", None),
    ("GET", "/api/pagos/membresias", None),
    ("GET", "/api/planes-membresia", None),
    ("POST", "/api/planes-membresia", {"nombre_plan": "MENSUAL", "duracion": "30 dias", "precio": 50}),
    ("GET", "/api/promociones", None),
    ("POST", "/api/promociones", {"nombre": "Verano"}),
    ("GET", "/api/inventario", None),
    ("POST", "/api/inventario", {"nombre_item": "Agua", "tipo": "Tienda", "cantidad_stock": 1}),
    ("GET", "/api/tienda", None),
    ("GET", "/api/tienda/pedidos", None),
    ("DELETE", "/api/tienda/1", None),
    ("GET", "/api/gym/summary", None),
    ("GET", "/api/gym/configuracion", None),
    ("POST", "/api/gym/configuracion", {"capacidad_total": 30, "capacidad_por_hora": 10}),
    ("GET", "/api/gym/horarios-servicio", None),
    ("POST", "/api/gym/rutinas", {"nombre_rutina": "Fuerza", "zonas_musculares": "Piernas"}),
    ("GET", "/api/trainer/overview", None),
    ("POST", "/api/trainer/rutinas", {"nombre_rutina": "Fuerza", "zonas_musculares": "Piernas"}),
    ("GET", "/api/trainer/clientes-rutinas?dni=12345678", None),
    ("GET", "/api/asistencia/resumen", None),
    ("POST", "/api/auth/password", {"correo": "ana@example.com", "password": "example"}),
    ("POST", "/api/auth/google/profile", {"credential": "example"}),
    ("POST", "/api/clientes/1/activar-membresia", None),
    ("GET", "/api/tienda/imagenes", None),
]


@pytest.mark.parametrize("method,path,payload", ROUTES)
@pytest.mark.parametrize("error", [PersistenceUnavailable("provider-private-token"), RuntimeError("provider-private-token")])
def test_all_modules_report_unavailable_services_without_leaking_details(method, path, payload, error, monkeypatch):
    response = api(error, monkeypatch).request(method, path, json=payload)
    assert response.status_code == 503, response.text
    assert "provider-private-token" not in response.text
    assert isinstance(response.json()["detail"], str)


@pytest.mark.parametrize("error,expected", [
    (EntityNotFound("No existe"), 404),
    (EnrollmentConflict("Ya se ocupó el cupo"), 409),
    (MembershipRequired("Membresía inactiva"), 403),
    (PermissionError("Sin permiso"), 403),
    (ValueError("Dato inválido"), 400),
])
@pytest.mark.parametrize("method,path,payload", [
    ("POST", "/api/gym/rutinas", {"nombre_rutina": "Fuerza", "zonas_musculares": "Piernas"}),
    ("POST", "/api/trainer/rutinas", {"nombre_rutina": "Fuerza", "zonas_musculares": "Piernas"}),
    ("POST", "/api/inventario", {"nombre_item": "Agua", "tipo": "Tienda", "cantidad_stock": 1}),
])
def test_domain_errors_keep_their_status_across_routes(error, expected, method, path, payload, monkeypatch):
    response = api(error, monkeypatch).request(method, path, json=payload)
    assert response.status_code == expected, response.text


def test_missing_migration_is_actionable_and_unexpected_errors_are_private(monkeypatch):
    response = api(SchemaNotReady("015_atomic_gym_transactions.sql"), monkeypatch).get("/api/tienda")
    assert response.status_code == 503
    assert "015_atomic_gym_transactions.sql" in response.json()["detail"]
    response = api(KeyError("private-internal-state"), monkeypatch).get("/api/clientes")
    assert response.status_code == 500
    assert "private-internal-state" not in response.text


def test_validation_errors_are_json_without_echoing_credentials_or_validator_context(monkeypatch):
    client = api(RuntimeError("Should not be called"), monkeypatch)
    response = client.post("/api/auth/google/profile", json={"credential": {"secret": "never-echo-this"}})
    assert response.status_code == 422
    assert "never-echo-this" not in response.text
    assert all(set(item) == {"loc", "type", "msg"} for item in response.json()["detail"])
    response = client.post("/api/usuarios", json={"nombre": "Ana", "correo": "incorrecto", "rol": "staff", "password": "never-echo-this"})
    assert response.status_code == 422
    assert "never-echo-this" not in response.text
    assert "ctx" not in response.text


def test_invalid_internal_models_are_server_errors_without_echoing_values(monkeypatch):
    try:
        UserProfile(id="private-id", name="Ana", email="ana@example.com", role="private-invalid-role")
    except ValidationError as error:
        response = api(error, monkeypatch).get("/api/usuarios")
    assert response.status_code == 500
    assert "private-invalid-role" not in response.text


def test_trainer_lookup_rejects_invalid_dni_before_calling_the_service(monkeypatch):
    client = api(RuntimeError("Should not be called"), monkeypatch)
    response = client.get("/api/trainer/clientes-rutinas?dni=abc")
    assert response.status_code == 422


@pytest.mark.parametrize("value", [0, -1, 1.5, "1e2", "", True])
def test_invalid_capacity_does_not_silently_become_one_or_partially_change_settings(value):
    service = LocalGymService()
    before = deepcopy(service.configuracion_gimnasio())
    with pytest.raises(ValueError):
        service.actualizar_configuracion_gimnasio({"capacidad_total": 80, "capacidad_por_hora": value})
    assert service.configuracion_gimnasio() == before
