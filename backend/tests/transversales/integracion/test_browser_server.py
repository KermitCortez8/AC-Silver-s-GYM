"""El servidor visual debe permanecer aislado y conservar autenticación real."""
import os
from unittest import mock

from fastapi.testclient import TestClient
import pytest

from infrastructure.config import get_settings
from tests.soporte.browser_server import create_app


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
