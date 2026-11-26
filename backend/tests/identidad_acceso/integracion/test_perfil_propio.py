from copy import deepcopy
import time
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import jwt
import pytest

from application.services.gym_service import GymService
from infrastructure.authentication import PasswordService, SignedSessionProvider
from infrastructure.config import Settings
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from infrastructure.security import get_auth_secret, verify_session_token
from presentation.dependencies import get_gym_service
from presentation.error_handlers import install_error_handlers
from presentation.routes.auth_routes import router


@pytest.fixture
def api_perfiles(monkeypatch):
    monkeypatch.setattr(
        "infrastructure.security.get_settings",
        lambda: Settings(auth_secret_key="prueba-perfil-propio-" * 3),
    )
    repository = MemoryGymRepository()
    passwords = PasswordService()
    current_hash = passwords.hash("Clave actual QA")
    repository.state["usuario"] = [
        {
            "id_usuario": identity, "nombre": role, "rol": role, "estado": "ACTIVO",
            "correo": f"{role}@example.com", "email": f"{role}@example.com",
            "dni": "98765432", "telefono": "987654321",
            "password_hash": current_hash, "google_sub": f"google-{role}",
        }
        for identity, role in (("SGADM001", "admin"), ("SGTRA002", "trainer"), ("SGSTA003", "staff"))
    ]
    repository.state["clientes"] = [
        {
            "id_cliente": index, "id_usuario": f"SGCLI{index:03}", "nombre": f"Cliente {index}",
            "correo": f"cliente{index}@example.com", "dni": str(index) * 8, "telefono": "987654321",
            "password_hash": current_hash, "google_sub": f"google-{index}", "estado": "ACTIVO", "plan": "MENSUAL",
            "fecha_registro": "2020-01-01",
        }
        for index in (1, 2)
    ]
    repository.state["membresia"] = [{
        "id_membresia": 1, "id_cliente": 1, "estado": "ACTIVA", "estado_pago": "PAGADO",
        "fecha_inicio": "2020-01-01", "fecha_fin": "2099-01-01",
    }]
    sessions = SignedSessionProvider()
    def google_claims(credential):
        return {"sub": "google-2" if credential == "otra" else "google-1",
                "iat": int(time.time()) - (600 if credential == "anterior" else 0)}

    gym = GymService(repository, passwords, identity=SimpleNamespace(verify=google_claims), sessions=sessions)
    app = FastAPI()
    install_error_handlers(app)
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.include_router(router, prefix="/api")

    def header(identity, client_id=None, *, age=0):
        token = sessions.issue({"id_usuario": identity, "id_cliente": client_id, "picture": "https://example.com/avatar"})
        if age:
            claims = verify_session_token(token)
            claims["iat"] -= age
            claims["exp"] -= age
            token = jwt.encode(claims, get_auth_secret(), algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        yield client, repository.state, header


@pytest.mark.parametrize("identity,role,client_id", [
    ("SGADM001", "admin", None), ("SGTRA002", "trainer", None),
    ("SGSTA003", "staff", None), ("SGCLI001", "user", 1),
])
def test_actualiza_solo_los_campos_del_perfil_de_la_sesion(api_perfiles, identity, role, client_id):
    client, state, header = api_perfiles
    headers = header(identity, client_id)
    before = deepcopy({key: state[key] for key in ("usuario", "clientes", "membresia")})
    result = client.patch("/api/auth/me", headers=headers, json={"nombre": " Perfil actualizado "})
    assert result.status_code == 200, result.json()
    profile = result.json()
    assert (profile["id_usuario"], profile["role"], profile["name"], profile["telefono"]) == (
        identity, role, "Perfil actualizado", "987654321",
    )
    assert "password_hash" not in profile and "google_sub" not in profile
    assert profile["picture"] == "https://example.com/avatar"
    assert profile["estado"] == "ACTIVO" and profile["google_vinculado"] and profile["tiene_contrasena"]
    assert profile["fecha_registro"] == ("2020-01-01" if client_id else "")
    assert profile["membresia"] == ({
        "plan": "MENSUAL", "fecha_inicio": "2020-01-01", "fecha_fin": "2099-01-01", "estado_pago": "PAGADO",
    } if client_id else None)
    result = client.patch("/api/auth/me", headers=headers, json={"telefono": ""})
    assert result.status_code == 200, result.json()
    assert client.get("/api/auth/me", headers=headers).json() == result.json()
    table = "clientes" if client_id else "usuario"
    own = next(row for row in before[table] if row["id_usuario"] == identity)
    own.update(nombre="Perfil actualizado", telefono="")
    assert {key: state[key] for key in before} == before


def test_rechaza_ediciones_sin_sesion_o_datos_fuera_del_perfil(api_perfiles):
    client, state, header = api_perfiles
    path = "/api/auth/me"
    assert client.patch(path, json={"nombre": "Otro"}).status_code == 401
    headers = header("SGCLI001", 1)
    before = deepcopy(state["clientes"])
    for field, value in (
        ("id_cliente", 2), ("id_usuario", "SGADM001"), ("rol", "admin"),
        ("estado", "ACTIVO"), ("password_hash", "cambio-prohibido"),
    ):
        assert client.patch(path, headers=headers, json={"nombre": "Otro", field: value}).status_code == 422
    assert client.patch(path, headers=headers, json={}).status_code == 400
    assert client.patch(path, headers=headers, json={"nombre": "Otro", "telefono": "12"}).status_code == 400
    assert state["clientes"] == before

    state["membresia"][0]["fecha_fin"] = "2020-02-01"
    assert client.patch(path, headers=headers, json={"nombre": "Otro"}).status_code == 403
    state["usuario"][1]["estado"] = "INACTIVO"
    assert client.patch(path, headers=header("SGTRA002"), json={"nombre": "Otro"}).status_code == 401


def test_ficha_del_cliente_muestra_su_vigencia_actual_aunque_haya_otro_pago_pendiente(api_perfiles):
    client, state, header = api_perfiles
    state["membresia"].extend([
        {**state["membresia"][0], "id_membresia": 2, "estado": "PENDIENTE_PAGO",
         "estado_pago": "PENDIENTE", "fecha_fin": "2099-06-01"},
        {**state["membresia"][0], "id_membresia": 3, "id_cliente": 2, "fecha_fin": "2099-12-01"},
    ])
    response = client.get("/api/auth/me", headers=header("SGCLI001", 1))
    assert response.status_code == 200, response.json()
    assert response.json()["membresia"]["fecha_fin"] == "2099-01-01"


@pytest.mark.parametrize("identity,role,client_id", [
    ("SGADM001", "admin", None), ("SGTRA002", "trainer", None),
    ("SGSTA003", "staff", None), ("SGCLI001", "user", 1),
])
def test_cuenta_confirma_identidad_y_actualiza_correo_dni_y_password(api_perfiles, identity, role, client_id):
    client, state, header = api_perfiles
    headers = header(identity, client_id, age=901)
    path = "/api/auth/me"
    payload = {"correo": "Perfil.Nuevo@Example.com", "dni": "78912345", "password_nueva": "Contraseña nueva QA",
               "telefono": "912345678", "nombre": "Perfil QA"}
    table = "clientes" if client_id else "usuario"
    original_email = "cliente1@example.com" if client_id else f"{role}@example.com"
    before = deepcopy(state[table])
    for proof in ({"password_actual": "Incorrecta"}, {"google_credential": "reciente"}):
        assert client.patch(path, headers=headers, json={**payload, **proof}).status_code == 403
        assert state[table] == before
    response = client.patch(path, headers=headers, json={**payload, "password_actual": "Clave actual QA"})
    assert response.status_code == 200, response.json()
    profile = response.json()
    assert (profile["id_usuario"], profile["role"], profile["email"], profile["dni"]) == (
        identity, role, "perfil.nuevo@example.com", "78912345",
    )
    assert not {"password_actual", "password_nueva", "password_hash"} & profile.keys()
    assert client.get(path, headers=headers).json() == profile
    login = "/api/auth/password"
    assert client.post(login, json={"correo": profile["email"], "password": "Clave actual QA"}).status_code == 401
    assert client.post(login, json={"correo": original_email, "password": "Contraseña nueva QA"}).status_code == 401
    new_login = client.post(login, json={"correo": profile["email"], "password": "Contraseña nueva QA"})
    assert new_login.status_code == 200 and new_login.json()["user"]["id_usuario"] == identity


def test_perfil_impide_usar_contactos_de_otra_cuenta_o_preregistro(api_perfiles):
    client, state, header = api_perfiles
    state["preregistros"] = [{"estado": "PENDIENTE", "correo": "pendiente@example.com", "dni": "88776655"}]
    headers = header("SGCLI001", 1)
    path = "/api/auth/me"
    before = deepcopy(state["clientes"])
    for fields in (
        {"correo": "ADMIN@example.com"}, {"dni": "98765432"}, {"dni": "22222222"},
        {"correo": "pendiente@example.com"}, {"dni": "88776655"}, {"dni": ""}, {"password_nueva": "12345"},
    ):
        response = client.patch(path, headers=headers, json={"password_actual": "Clave actual QA", **fields})
        assert response.status_code == 400, response.json()
        assert state["clientes"] == before


def test_cuenta_google_puede_configurar_password_al_confirmar_su_identidad(api_perfiles):
    client, state, header = api_perfiles
    state["clientes"][0]["password_hash"] = ""
    headers = header("SGCLI001", 1, age=901)
    path = "/api/auth/me"
    payload = {"password_nueva": "Clave inicial QA"}
    for credential in ("otra", "anterior"):
        response = client.patch(path, headers=headers, json={**payload, "google_credential": credential})
        assert response.status_code == 403, response.json()
        assert state["clientes"][0]["password_hash"] == ""
    response = client.patch(path, headers=headers, json={**payload, "google_credential": "reciente"})
    assert response.status_code == 200, response.json()
    assert response.json()["tiene_contrasena"] and response.json()["google_vinculado"]
    assert client.post("/api/auth/password", json={"correo": "cliente1@example.com", "password": "Clave inicial QA"}).status_code == 200


@pytest.mark.parametrize("identity,client_id", [("SGADM001", None), ("SGCLI001", 1)])
def test_sesion_vigente_permite_guardar_una_password_nueva_sin_reautenticar(api_perfiles, identity, client_id):
    client, state, header = api_perfiles
    path = "/api/auth/me"
    table = "clientes" if client_id else "usuario"
    before = deepcopy(state[table])
    payload = {"password_nueva": "Clave renovada QA", "correo": "nuevo@example.com", "dni": "78345612"}
    expired = header(identity, client_id, age=3601)
    assert client.patch(path, headers=expired, json=payload).status_code == 401
    assert state[table] == before
    active = header(identity, client_id, age=3300)
    response = client.patch(path, headers=active, json=payload)
    assert response.status_code == 200, response.json()
    assert response.json()["tiene_contrasena"] and response.json()["email"] == "nuevo@example.com"
    assert client.post("/api/auth/password", json={"correo": "nuevo@example.com", "password": "Clave renovada QA"}).status_code == 200
