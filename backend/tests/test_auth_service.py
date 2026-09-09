from __future__ import annotations

import pytest

from models.auth import AuthGoogleRequest, AuthPasswordRequest
from services.auth_service import AuthService


class FakeGymService:
    """Doble de prueba: solo implementa lo que AuthService usa (sin Supabase real)."""

    def __init__(self, usuario=None, cliente=None, auth_usuario=None, auth_cliente=None):
        self._usuario = usuario
        self._cliente = cliente
        self._auth_usuario = auth_usuario
        self._auth_cliente = auth_cliente

    def get_usuario_by_email(self, email):
        return self._usuario

    def get_cliente_by_email(self, email):
        return self._cliente

    def authenticate_usuario_password(self, correo, password):
        return self._auth_usuario

    def authenticate_cliente_password(self, correo, password):
        return self._auth_cliente


def test_google_auth_rejects_credential_without_email():
    service = AuthService(FakeGymService())
    payload = AuthGoogleRequest(credential="cred-sin-perfil", profile={"name": "Sin Email"})
    with pytest.raises(ValueError):
        service.google_auth(payload)


def test_google_auth_maps_existing_usuario():
    usuario = {"id_usuario": "U1", "correo": "admin@acsilversgym.com", "telefono": "999888777", "rol": "admin"}
    service = AuthService(FakeGymService(usuario=usuario))
    payload = AuthGoogleRequest(credential="cred-google", profile={"email": "admin@acsilversgym.com", "name": "Admin"})

    result = service.google_auth(payload)

    assert result.user.id == "U1"
    assert result.user.email == "admin@acsilversgym.com"
    assert result.user.role == "admin"
    assert result.expiresIn == 3600


def test_google_auth_maps_existing_cliente_when_no_usuario():
    cliente = {"id_cliente": 7, "correo": "cliente@example.com", "nombre": "Cliente Uno", "dni": "12345678"}
    service = AuthService(FakeGymService(usuario=None, cliente=cliente))
    payload = AuthGoogleRequest(credential="cred-google", profile={"email": "cliente@example.com", "name": "Cliente"})

    result = service.google_auth(payload)

    assert result.user.id == "SGCLI007"
    assert result.user.role == "user"
    assert result.user.dni == "12345678"


def test_google_auth_falls_back_to_domain_role_when_not_registered():
    service = AuthService(FakeGymService(usuario=None, cliente=None))
    payload = AuthGoogleRequest(credential="cred-google", profile={"email": "nuevo@urp.edu.pe", "name": "Nuevo"})

    result = service.google_auth(payload)

    assert result.user.role == "admin"


def test_password_auth_requires_correo_and_password():
    service = AuthService(FakeGymService())
    with pytest.raises(ValueError):
        service.password_auth(AuthPasswordRequest(correo="", password=""))


def test_password_auth_succeeds_for_usuario():
    usuario = {"id_usuario": "U2", "correo": "staff@acsilversgym.com", "nombre": "Staff Uno", "rol": "staff"}
    service = AuthService(FakeGymService(auth_usuario=usuario))

    result = service.password_auth(AuthPasswordRequest(correo="staff@acsilversgym.com", password="clave123"))

    assert result.user.id == "U2"
    assert result.user.role == "staff"
    assert result.token


def test_password_auth_succeeds_for_cliente_when_no_usuario_match():
    cliente = {"id_cliente": 3, "correo": "cliente2@example.com", "nombre": "Cliente Dos"}
    service = AuthService(FakeGymService(auth_usuario=None, auth_cliente=cliente))

    result = service.password_auth(AuthPasswordRequest(correo="cliente2@example.com", password="clave123"))

    assert result.user.id == "SGCLI003"
    assert result.user.role == "user"


def test_password_auth_rejects_wrong_credentials():
    service = AuthService(FakeGymService(auth_usuario=None, auth_cliente=None))
    with pytest.raises(ValueError):
        service.password_auth(AuthPasswordRequest(correo="quien@example.com", password="incorrecta"))


def test_user_from_payload_maps_existing_usuario():
    usuario = {"id_usuario": "U3", "correo": "admin2@acsilversgym.com", "telefono": "1", "rol": "trainer", "dni": "87654321"}
    service = AuthService(FakeGymService(usuario=usuario))

    profile = service.user_from_payload({"email": "admin2@acsilversgym.com", "name": "Admin Dos"})

    assert profile.id == "U3"
    assert profile.role == "trainer"
    assert profile.dni == "87654321"


def test_user_from_payload_maps_existing_cliente_when_no_usuario():
    cliente = {"id_cliente": 9, "correo": "cliente3@example.com", "nombre": "Cliente Tres"}
    service = AuthService(FakeGymService(usuario=None, cliente=cliente))

    profile = service.user_from_payload({"email": "cliente3@example.com", "name": "Cliente Tres"})

    assert profile.id == "SGCLI009"
    assert profile.role == "user"


def test_user_from_payload_returns_default_profile_when_not_registered():
    service = AuthService(FakeGymService(usuario=None, cliente=None))

    profile = service.user_from_payload({"email": "desconocido@example.com", "name": "Desconocido"})

    assert profile.email == "desconocido@example.com"
    assert profile.role == "user"
