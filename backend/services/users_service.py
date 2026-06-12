from __future__ import annotations

from typing import Any

from services.gym_service import GymService


class UsersService:
    """Servicio fino para el flujo de Usuario."""

    def __init__(self, gym_service: GymService) -> None:
        self.gym = gym_service

    def list_users(self) -> list[dict[str, Any]]:
        return self.gym.usuarios_normalized()

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

    def delete_user(self, id_usuario: str) -> None:
        self.gym.delete_usuario(id_usuario)
