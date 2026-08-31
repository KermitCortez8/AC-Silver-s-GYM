# Módulo: auth.
# Define los datos de entrada y salida para autenticación.
# Limita los roles permitidos en los perfiles de usuario.
# Mantiene estable el contrato de las rutas de acceso.
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    id_usuario: str = ""
    id_cliente: int | None = None
    email: str
    telefono: str = ""
    dni: str = ""
    name: str
    picture: str = ""
    givenName: str = ""
    familyName: str = ""
    role: Literal["admin", "user", "trainer", "staff"] = "user"


class AuthGoogleRequest(BaseModel):
    credential: str
    profile: dict[str, Any] | None = None


class AuthPasswordRequest(BaseModel):
    correo: str = ""
    password: str = ""


class AuthResponse(BaseModel):
    user: UserProfile
    token: str
    expiresIn: int
    source: Literal["backend"] = "backend"
