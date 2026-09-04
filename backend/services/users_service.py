# Módulo: users_service.
# Adapta las cuentas internas al formato de la API.
# Gestiona altas, cambios y eliminación del personal.
# Evita exponer hashes de contraseña en las respuestas.
from __future__ import annotations

from typing import Any

from services.gym_domain_service import GymDomainService


class UsersService:
    """Servicio fino para el flujo de Usuario."""

    # Inicializa la clase.
    def __init__(self, gym_service: GymDomainService) -> None:
        self.gym = gym_service

    # Obtiene los datos necesarios.
    def list_users(self) -> list[dict[str, Any]]:
        return self.gym.usuarios_normalized()

    # Actualiza el registro correspondiente.
    def upsert_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        saved = self.gym.upsert_usuario(payload)
        return {
            "id_usuario": saved.get("id_usuario"),
            "nombre": saved.get("nombre", ""),
            "correo": saved.get("correo", ""),
            "telefono": saved.get("telefono", ""),
            "dni": saved.get("dni", ""),
            "rol": saved.get("rol", "staff"),
            "has_password": bool(saved.get("password_hash")),
        }

    # Elimina el registro indicado.
    def delete_user(self, id_usuario: str) -> None:
        self.gym.delete_usuario(id_usuario)
