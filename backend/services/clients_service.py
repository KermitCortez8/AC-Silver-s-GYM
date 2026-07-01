from __future__ import annotations

from typing import Any

from services.gym_domain_service import GymDomainService


class ClientsService:
    """Servicio fino para manejar la entidad Cliente con la forma requerida por la UI.

    Internamente reutiliza GymDomainService para reglas de negocio.
    """

    def __init__(self, gym_service: GymDomainService) -> None:
        self.gym = gym_service

    def list_clients(self) -> list[dict[str, Any]]:
        return self.gym.clientes_normalized()

    def get_client(self, id_usuario: str) -> dict[str, Any] | None:
        normalized = str(id_usuario or "").strip().upper()
        return next((c for c in self.list_clients() if str(c.get("id_usuario") or "").strip().upper() == normalized), None)

    def upsert_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        item = {}
        item["id_usuario"] = str(payload.get("id_usuario") or "").strip()
        item["nombre"] = str(payload.get("nombre") or "").strip()
        item["correo"] = str(payload.get("correo") or payload.get("email") or "").strip()
        item["telefono"] = str(payload.get("telefono") or "").strip()
        item["dni"] = str(payload.get("dni") or "").strip()
        item["password"] = str(payload.get("password") or payload.get("contrasena") or "").strip()
        item["plan"] = str(payload.get("plan") or "MENSUAL").strip() or "MENSUAL"
        item["promocion"] = str(payload.get("promocion") or "SIN PROMOCION").strip() or "SIN PROMOCION"
        item["estado"] = str(payload.get("estado") or "ACTIVO").strip().upper() or "ACTIVO"

        saved = self.gym.upsert_cliente(item)

        # Build normalized shape to return
        normalized = {
            "id_cliente": int(saved.get("id_cliente", 0) or 0),
            "id_usuario": str(saved.get("id_usuario") or f"SGCLI{int(saved.get('id_cliente', 0)):03d}"),
            "nombre": str(saved.get("nombre") or payload.get("nombre") or "").strip(),
            "correo": str(saved.get("correo") or payload.get("correo") or payload.get("email") or "").strip(),
            "telefono": str(saved.get("telefono") or payload.get("telefono") or "").strip(),
            "dni": str(saved.get("dni") or payload.get("dni") or "").strip(),
            "plan": str(saved.get("plan") or payload.get("plan") or "").strip(),
            "promocion": str(saved.get("promocion") or payload.get("promocion") or "").strip(),
            "estado": str(saved.get("estado") or payload.get("estado") or "ACTIVO").strip().upper() or "ACTIVO",
            "has_password": bool(saved.get("password_hash")),
        }
        return normalized

    def _safe_registration_result(self, result: dict[str, Any]) -> dict[str, Any]:
        cliente = {**(result.get("cliente") or {})}
        cliente.pop("password_hash", None)
        if "cliente" in result:
            cliente["has_password"] = bool((result.get("cliente") or {}).get("password_hash"))
        return {**result, "cliente": cliente}

    def register_public_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._safe_registration_result(self.gym.registrar_cliente_publico(payload))

    def confirm_public_payment(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._safe_registration_result(self.gym.confirmar_pago_cliente_publico(id_cliente, payload))

    def activate_client_membership(self, id_cliente: int) -> dict[str, Any]:
        return self._safe_registration_result(self.gym.activar_membresia_cliente(id_cliente))

    def delete_client(self, id_usuario: str) -> None:
        try:
            normalized = str(id_usuario or "").strip().upper()
            if normalized.startswith("SGCLI"):
                id_num = int(normalized.replace("SGCLI", ""))
                self.gym.delete_cliente(int(id_num))
        except Exception:
            # best-effort: ignore
            pass
