# Módulo: clients_service.
# Adapta clientes y membresías al formato usado por la interfaz.
# Controla registros pendientes y confirmaciones de pago.
# Oculta contraseñas antes de devolver información pública.
from __future__ import annotations

from typing import Any

from services.gym_domain_service import GymDomainService


class ClientsService:
    """Servicio fino para manejar la entidad Cliente con la forma requerida por la UI.

    Internamente reutiliza GymDomainService para reglas de negocio.
    """

    # Inicializa la clase.
    def __init__(self, gym_service: GymDomainService) -> None:
        self.gym = gym_service

    # Obtiene los datos necesarios.
    def list_clients(self) -> list[dict[str, Any]]:
        return self.gym.clientes_normalized()

    # Obtiene los datos necesarios.
    def get_client(self, id_usuario: str) -> dict[str, Any] | None:
        normalized = str(id_usuario or "").strip().upper()
        return next((c for c in self.list_clients() if str(c.get("id_usuario") or "").strip().upper() == normalized), None)

    # Obtiene los datos necesarios.
    def get_client_for_user(self, user: Any) -> dict[str, Any]:
        id_cliente = int(getattr(user, "id_cliente", 0) or 0)
        email = str(getattr(user, "email", "") or getattr(user, "correo", "") or "").strip().lower()
        dni = str(getattr(user, "dni", "") or "").strip()

        client = None
        if id_cliente:
            client = next((c for c in self.list_clients() if int(c.get("id_cliente", 0) or 0) == id_cliente), None)
        if not client and email:
            client = next((c for c in self.list_clients() if str(c.get("correo") or "").strip().lower() == email), None)
        if not client and dni:
            client = next((c for c in self.list_clients() if str(c.get("dni") or "").strip() == dni), None)
        if not client:
            raise ValueError("Cliente no encontrado")
        return client

    # Actualiza el registro correspondiente.
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

    # Procesa esta operación.
    def _safe_registration_result(self, result: dict[str, Any]) -> dict[str, Any]:
        cliente = {**(result.get("cliente") or {})}
        cliente.pop("password_hash", None)
        if "cliente" in result:
            cliente["has_password"] = bool((result.get("cliente") or {}).get("password_hash"))
        return {**result, "cliente": cliente}

    # Crea el registro correspondiente.
    def register_public_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        correo = str(payload.get("correo") or payload.get("google_email") or "").strip().lower()
        dni = str(payload.get("dni") or "").strip()
        existing = self.gym.get_cliente_by_email(correo) if correo else None
        if existing and str(existing.get("dni") or "").strip() == dni:
            self.gym.ensure_fresh()
            state = self.gym.state
            membership = self.gym._latest_membership_for_cliente(state, int(existing.get("id_cliente", 0) or 0))
            if membership and str(membership.get("estado_pago") or "").upper() == "PENDIENTE":
                plan = self.gym.get_plan_membresia(int(membership.get("id_pm", 0) or 0)) or {}
                return self._safe_registration_result({"cliente": existing, "membresia": membership, "plan": plan})
        return self._safe_registration_result(self.gym.registrar_cliente_publico(payload))

    # Procesa esta operación.
    def confirm_public_payment(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._safe_registration_result(self.gym.confirmar_pago_cliente_publico(id_cliente, payload))

    # Procesa esta operación.
    def payment_amount_matches(self, id_cliente: int, amount: float, id_membresia: int | None = None) -> bool:
        self.gym.ensure_fresh()
        state = self.gym.state
        if id_membresia is not None:
            membership = next(
                (
                    row
                    for row in state.get("membresia", [])
                    if int(row.get("id_cliente", 0) or 0) == int(id_cliente)
                    and int(row.get("id_membresia", 0) or 0) == int(id_membresia)
                ),
                None,
            )
        else:
            membership = self.gym._latest_membership_for_cliente(state, int(id_cliente))
        if not membership:
            return False
        expected = float(membership.get("monto_pago", 0) or 0)
        if expected <= 0:
            plan = self.gym.get_plan_membresia(int(membership.get("id_pm", 0) or 0))
            expected = float((plan or {}).get("precio", 0) or 0)
        return expected > 0 and abs(expected - float(amount)) < 0.01

    # Procesa esta operación.
    def activate_client_membership(self, id_cliente: int) -> dict[str, Any]:
        return self._safe_registration_result(self.gym.activar_membresia_cliente(id_cliente))

    # Elimina el registro indicado.
    def delete_client(self, id_usuario: str) -> None:
        try:
            normalized = str(id_usuario or "").strip().upper()
            if normalized.startswith("SGCLI"):
                id_num = int(normalized.replace("SGCLI", ""))
                self.gym.delete_cliente(int(id_num))
        except Exception:
            # best-effort: ignore
            pass
