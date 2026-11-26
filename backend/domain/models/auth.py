# Módulo: auth.
# Define los datos de entrada y salida para autenticación.
# Limita los roles permitidos en los perfiles de usuario.
# Mantiene estable el contrato de las rutas de acceso.
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from domain.form_limits import DNI_LENGTH, SHORT_TEXT_LIMIT, PHONE_LENGTH


class MembershipProfile(BaseModel):
    plan: str = ""
    fecha_inicio: str
    fecha_fin: str
    estado_pago: str


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
    estado: str = ""
    fecha_registro: str = ""
    google_vinculado: bool = False
    tiene_contrasena: bool = False
    membresia: MembershipProfile | None = None


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(default="", max_length=SHORT_TEXT_LIMIT)
    telefono: str = Field(default="", max_length=PHONE_LENGTH)
    correo: str = Field(default="", max_length=SHORT_TEXT_LIMIT)
    dni: str = Field(default="", max_length=DNI_LENGTH)
    password_nueva: SecretStr = Field(default=SecretStr(""), max_length=256)
    password_actual: SecretStr = Field(default=SecretStr(""), max_length=16384)
    google_credential: SecretStr = Field(default=SecretStr(""), max_length=16384)


class AuthGoogleRequest(BaseModel):
    credential: str = Field(min_length=1, max_length=16384)
    password: str = ""


class GoogleProfile(BaseModel):
    email: str
    name: str
    picture: str = ""


class AuthPasswordRequest(BaseModel):
    correo: str = ""
    password: str = ""


class PasswordRecoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correo: str = Field(max_length=SHORT_TEXT_LIMIT)


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: SecretStr = Field(max_length=2048)
    password_nueva: SecretStr = Field(max_length=256)


class AuthResponse(BaseModel):
    user: UserProfile
    token: str
    expiresIn: int
    source: Literal["backend"] = "backend"
