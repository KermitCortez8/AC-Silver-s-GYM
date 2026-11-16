"""Verificación de rol persistido del caso de integración TC-159."""
from application.services.auth_service import AuthService
from tests.soporte.testiny_api import documented_api  # noqa: F401


def test_tc159_nueva_sesion_resuelve_rol_guardado_y_respuesta_no_expone_hash(documented_api):
    api = documented_api
    response = api.client.post("/api/usuarios", json={"nombre": "Entrenador QA", "correo": "trainer@example.com",
        "dni": "33333333", "telefono": "999999999", "rol": "trainer", "password": "clave-qa-sintetica"})
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["rol"] == "trainer" and saved["has_password"] is True
    assert "password" not in saved and "password_hash" not in saved
    profile = AuthService(api.gym).user_from_payload({"sub": saved["id_usuario"], "role": "admin"})
    assert profile.role == "trainer" and profile.id_usuario == saved["id_usuario"]
    loaded = api.client.get("/api/usuarios").json()
    assert any(row["id_usuario"] == saved["id_usuario"] and row["rol"] == "trainer" for row in loaded)
    assert "password_hash" not in str(loaded)
