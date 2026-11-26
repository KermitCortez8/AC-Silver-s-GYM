from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import time
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI
from fastapi.testclient import TestClient
import jwt
import pytest

from application.services.gym_service import GymService
from application.services.password_recovery import PasswordRecoveryLimit
from infrastructure.authentication import PasswordService, SignedSessionProvider
from infrastructure.config import Settings, get_settings
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from presentation.dependencies import get_gym_service
from presentation.error_handlers import install_error_handlers
from presentation.routes.auth_routes import get_password_recovery_limit, router

REQUEST = "/api/auth/recuperar-contrasena"
RESET = "/api/auth/restablecer-contrasena"
CLIENT = {"correo": "cliente@example.com", "dni": "12345678", "telefono": "987654321"}
ADMIN = {"correo": "admin@example.com", "dni": "23456789", "telefono": "998877665"}


@pytest.fixture
def recovery(monkeypatch):
    settings = Settings(
        auth_secret_key="prueba-recuperacion-" * 3, resend_api_key="correo-qa",
        email_from="gym@example.com", frontend_public_url="https://gym.example",
    )
    passwords, sessions = PasswordService(), SignedSessionProvider()
    original = passwords.hash("Clave anterior QA")
    repository = MemoryGymRepository()
    repository.state["clientes"] = [{
        **CLIENT, "id_usuario": "SGCLI001", "id_cliente": 1, "nombre": "Cliente QA",
        "estado": "ACTIVO", "password_hash": original,
    }]
    repository.state["usuario"] = [{
        **ADMIN, "id_usuario": "SGADM001", "nombre": "Admin QA", "rol": "admin",
        "estado": "ACTIVO", "password_hash": original,
    }]
    repository.state["membresia"] = [{
        "id_cliente": 1, "id_membresia": 1, "fecha_inicio": "2020-01-01",
        "fecha_fin": "2099-01-01", "estado": "ACTIVA", "estado_pago": "PAGADO",
    }]
    gym = GymService(repository, passwords, sessions=sessions)
    deliveries = {}

    class Email:
        def send(self, payload, event_key):
            deliveries.setdefault(event_key, payload)
            return "correo-simulado"

    monkeypatch.setattr("app.bootstrap.ResendEmailService", lambda _: Email())
    monkeypatch.setattr("infrastructure.security.get_settings", lambda: settings)
    app = FastAPI()
    install_error_handlers(app)
    limiter = PasswordRecoveryLimit()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_password_recovery_limit] = lambda: limiter
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.include_router(router, prefix="/api")
    with TestClient(app) as client:
        yield client, deliveries, repository.state, settings


def link_token(deliveries):
    mail = list(deliveries.values())[-1]
    url = next(line for line in mail["text"].splitlines() if line.startswith("https://"))
    parts = urlsplit(url)
    assert parts.netloc == "gym.example" and parts.path == "/restablecer-contrasena"
    assert not parts.query
    return parse_qs(parts.fragment)["token"][0]


def test_solicitud_acepta_solo_el_correo_y_responde_igual_si_no_esta_registrado(recovery):
    api, deliveries, state, _ = recovery
    before = deepcopy(state)
    unknown = api.post(REQUEST, json={"correo": "otro@example.com"})
    assert api.post(REQUEST, json=CLIENT).status_code == 422
    assert deliveries == {}
    normal = api.post(REQUEST, json={"correo": "CLIENTE@EXAMPLE.COM"})
    assert normal.status_code == unknown.status_code == 202
    assert normal.json() == unknown.json()
    assert len(deliveries) == 1 and next(iter(deliveries.values()))["to"] == [CLIENT["correo"]]
    assert link_token(deliveries) not in normal.text
    assert state == before


def test_correo_compartido_por_dos_cuentas_activas_no_genera_un_enlace_ambiguo(recovery):
    api, deliveries, state, _ = recovery
    state["usuario"][0]["correo"] = CLIENT["correo"]
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 202
    assert not deliveries
    state["usuario"][0]["estado"] = "INACTIVO"
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 202
    assert len(deliveries) == 1


@pytest.mark.parametrize("email", [CLIENT["correo"], ADMIN["correo"]])
def test_enlace_se_usa_una_vez_y_permite_ingresar_con_password_nueva(recovery, email):
    api, deliveries, state, _ = recovery
    assert api.post(REQUEST, json={"correo": email}).status_code == 202
    token = link_token(deliveries)
    memberships = deepcopy(state["membresia"])
    password = {"token": token, "password_nueva": "Clave renovada QA"}
    assert api.post(RESET, json={**password, "password_nueva": "12345"}).status_code == 400
    assert api.post(RESET, json=password).status_code == 204
    assert api.post(RESET, json=password).status_code == 400
    assert state["membresia"] == memberships
    login = {"correo": email, "password": "Clave renovada QA"}
    assert api.post("/api/auth/password", json=login).status_code == 200
    assert api.post("/api/auth/password", json={**login, "password": "Clave anterior QA"}).status_code == 401


def test_enlace_expirado_y_token_de_sesion_son_rechazados(recovery):
    api, deliveries, state, settings = recovery
    assert api.post(REQUEST, json={"correo": ADMIN["correo"]}).status_code == 202
    token = link_token(deliveries)
    claims = jwt.decode(token, settings.auth_secret_key, algorithms=["HS256"], audience="gym-password-recovery")
    claims["exp"] = int(time.time()) - 1
    expired = jwt.encode(claims, settings.auth_secret_key, algorithm="HS256")
    session = api.post("/api/auth/password", json={"correo": ADMIN["correo"], "password": "Clave anterior QA"}).json()["token"]
    assert api.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    before = deepcopy(state["usuario"])
    for invalid in (expired, session, "enlace-invalido"):
        assert api.post(RESET, json={"token": invalid, "password_nueva": "Clave nueva QA"}).status_code == 400
    assert state["usuario"] == before


def test_cambios_en_cuenta_y_reintentos_concurrentes_consumen_el_enlace(recovery):
    api, deliveries, state, _ = recovery
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 202
    original = link_token(deliveries)
    state["clientes"][0]["telefono"] = "987654322"
    assert api.post(RESET, json={"token": original, "password_nueva": "Clave inicial QA"}).status_code == 400
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 202
    token = link_token(deliveries)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = pool.map(lambda password: api.post(RESET, json={"token": token, "password_nueva": password}).status_code,
                           ("Clave nueva QA 1", "Clave nueva QA 2"))
        assert sorted(results) == [204, 400]


def test_limite_de_solicitudes_y_configuracion_de_correo(recovery):
    api, deliveries, _, settings = recovery
    settings.resend_api_key = ""
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 503
    settings.resend_api_key = "correo-qa"
    for _ in range(7):
        assert api.post(REQUEST, json={"correo": "otro@example.com"}).status_code == 202
    assert api.post(REQUEST, json={"correo": CLIENT["correo"]}).status_code == 429
    assert deliveries == {}
