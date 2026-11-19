"""El servidor visual debe permanecer aislado y conservar autenticación real."""
import os
from unittest import mock

from fastapi.testclient import TestClient
import pytest

from infrastructure.config import get_settings
from infrastructure.security import create_local_token
from tests.soporte.browser_server import create_app


ADMIN = {"correo": "admin@example.test", "password": "Prueba-Navegador-2026!"}
STAFF = dict(nombre="Personal QA", correo="personal@gmail.com", password="clave-personal-qa",
             dni="23456789", telefono="987654321", rol="staff")


def login(api, credentials):
    response = api.post("/api/auth/password", json=credentials)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_staff(api, admin):
    response = api.post("/api/usuarios", headers=admin, json=STAFF)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def browser_api():
    with mock.patch.dict(os.environ, {"GYM_BROWSER_TESTS": "1", "GYM_QA_KEY": "qa-local-only"}):
        try:
            with TestClient(create_app()) as client:
                yield client
        finally:
            get_settings.cache_clear()


def test_servidor_qa_no_arranca_sin_activacion_explicita():
    with mock.patch.dict(os.environ, {"GYM_BROWSER_TESTS": "0"}):
        with pytest.raises(RuntimeError, match="exclusivo"):
            create_app()


def test_autenticacion_y_persistencia_de_memoria_en_las_rutas_reales(browser_api):
    assert browser_api.get("/api/inventario").status_code == 401
    invalid = browser_api.post("/api/auth/password", json={"correo": "admin@example.test", "password": "incorrecta"})
    assert invalid.status_code == 401
    response = browser_api.post("/api/auth/password", json={
        "correo": "admin@example.test", "password": "Prueba-Navegador-2026!",
    })
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['token']}"}
    assert browser_api.get("/api/auth/me", headers=headers).json()["role"] == "admin"
    saved = browser_api.post("/api/inventario", headers=headers, json={
        "nombre_item": "Escoba QA", "tipo": "Limpieza", "cantidad_stock": 10,
    })
    assert saved.status_code == 200
    loaded = browser_api.get("/api/inventario", headers=headers).json()
    assert len(loaded) == 1 and loaded[0]["cantidad_stock"] == 10


def test_reset_exige_clave_local_y_restaura_datos_sinteticos(browser_api):
    assert browser_api.post("/__qa/reset").status_code == 403
    assert browser_api.post("/__qa/reset", headers={"X-QA-Key": "qa-local-only"}).status_code == 200
    assert browser_api.get("/__qa/health").json() == {"status": "ok", "repository": "memory", "synthetic": True}


def test_tc186_backend_qa_saludable_y_catalogo_publico_de_solo_lectura(browser_api):
    admin = login(browser_api, ADMIN)
    before = {path: browser_api.get(path, headers=admin).json() for path in ("/api/clientes", "/api/pagos/membresias")}
    assert browser_api.get("/__qa/health").json() == {"status": "ok", "repository": "memory", "synthetic": True}
    offer = browser_api.get("/api/planes-membresia")
    assert offer.status_code == 200
    assert any(plan["activo"] and plan["nombre_plan"] and plan["precio"] > 0 for plan in offer.json())
    assert {path: browser_api.get(path, headers=admin).json() for path in before} == before


def test_tc003_credenciales_invalidas_no_crean_sesion_y_se_puede_reintentar(browser_api):
    for credentials, status in (
        ({}, 401), ({**ADMIN, "password": "incorrecta"}, 401),
        ({**ADMIN, "correo": "ausente@example.test"}, 401),
    ):
        denied = browser_api.post("/api/auth/password", json=credentials)
        assert denied.status_code == status
        assert "token" not in denied.json()
        assert browser_api.get("/api/auth/me").status_code == 401
    assert browser_api.get("/api/auth/me", headers=login(browser_api, ADMIN)).json()["role"] == "admin"


def test_tc006_tc007_alta_y_consulta_separan_personal_de_clientes(browser_api):
    admin = login(browser_api, ADMIN)
    clients = browser_api.get("/api/clientes", headers=admin).json()
    saved = create_staff(browser_api, admin)
    people = browser_api.get("/api/usuarios", headers=admin).json()
    [staff] = [person for person in people if person["correo"] == STAFF["correo"]]
    assert staff == saved and staff["rol"] == "staff"
    assert browser_api.get("/api/auth/me", headers=login(browser_api, STAFF)).status_code == 200
    assert all(staff[field] == STAFF[field] for field in ("nombre", "correo", "dni", "telefono"))
    assert all(person["rol"] in ("admin", "staff", "trainer") for person in people)
    assert all(not {"password", "password_hash"} & person.keys() for person in people)
    assert STAFF["password"] not in str(people)
    assert browser_api.get("/api/clientes", headers=admin).json() == clients
    assert browser_api.get("/api/usuarios", headers=admin).json() == people


def test_tc005_tc008_el_rol_guardado_gobierna_la_sesion_y_conserva_la_clave(browser_api):
    admin = login(browser_api, ADMIN)
    staff = create_staff(browser_api, admin)
    before = login(browser_api, STAFF)
    assert browser_api.get("/api/usuarios", headers=before).status_code == 200
    response = browser_api.post("/api/usuarios", headers=admin, json={
        **staff, "nombre": "Entrenador QA", "rol": "trainer", "password": "",
    })
    assert response.status_code == 200, response.text
    updated = response.json()
    assert not {"password", "password_hash"} & updated.keys()
    people = browser_api.get("/api/usuarios", headers=admin).json()
    assert updated in people and updated["nombre"] == "Entrenador QA" and updated["rol"] == "trainer"
    current = login(browser_api, STAFF)
    assert browser_api.get("/api/auth/me", headers=current).json()["role"] == "trainer"
    assert browser_api.get("/api/usuarios", headers=current).status_code == 403
    assert browser_api.get("/api/auth/me", headers=before).json()["role"] == "trainer"
    assert browser_api.get("/api/usuarios", headers=admin).json() == people


def test_tc009_borrar_personal_revoca_tambien_el_token_previo(browser_api):
    admin = login(browser_api, ADMIN)
    user = create_staff(browser_api, admin)
    previous = login(browser_api, STAFF)
    assert browser_api.get("/api/usuarios", headers=previous).status_code == 200
    assert browser_api.delete(f"/api/usuarios/{user['id_usuario']}", headers=admin).status_code == 204
    assert user["id_usuario"] not in {u["id_usuario"] for u in browser_api.get("/api/usuarios", headers=admin).json()}
    assert browser_api.post("/api/auth/password", json=STAFF).status_code == 401
    assert browser_api.get("/api/usuarios", headers=previous).status_code == 401


@pytest.mark.parametrize("variant", ["alterado", "vencido"])
def test_tc126_token_invalido_no_entrega_ni_modifica_datos(browser_api, variant):
    admin = login(browser_api, ADMIN)
    staff = create_staff(browser_api, admin)
    previous = login(browser_api, STAFF)
    people = browser_api.get("/api/usuarios", headers=admin).json()
    token = previous["Authorization"].split()[1]
    if variant == "alterado":
        header, payload, signature = token.split(".")
        first = "A" if signature[0] != "A" else "B"
        token = f"{header}.{payload}.{first}{signature[1:]}"
    else:
        token = create_local_token({"id": staff["id_usuario"], "email": staff["correo"], "role": "staff"},
                                   expires_seconds=-120)
    headers = {"Authorization": f"Bearer {token}"}
    denied = browser_api.get("/api/usuarios", headers=headers)
    assert denied.status_code == 401 and STAFF["correo"] not in denied.text
    assert browser_api.delete(f"/api/usuarios/{staff['id_usuario']}", headers=headers).status_code == 401
    assert browser_api.get("/api/usuarios", headers=admin).json() == people
