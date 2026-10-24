"""Casos de uso de registro, checkout y confirmación, independientes de HTTP."""
import logging

from application.services.membership_checkout_service import confirm_verified_checkout, _value, _is_store_checkout
from application.services.store_checkout_service import cancelar_por_sesion_expirada, confirmar_sesion_tienda
from domain.errors import EntityNotFound
from domain.services.gym_domain_service import PedidoCanceladoConPagoError

logger = logging.getLogger(__name__)


class ClientPaymentsService:
    def __init__(self, clients, gym, settings, *, gateway_factory, notify):
        self.clients, self.gym, self.settings = clients, gym, settings
        self.gateway_factory, self.notify = gateway_factory, notify

    def gateway(self):
        return self.gateway_factory(self.settings)

    def register_public(self, payload):
        if not self.settings.has_supabase_credentials:
            raise RuntimeError("Supabase debe estar configurado para registrar pagos de membresía")
        gateway = self.gateway()
        if not gateway.configured:
            raise RuntimeError("Stripe no está configurado en backend/.env")
        gateway.validate_configuration()
        result = self.clients.register_public_client(payload)
        try:
            payment = gateway.create_membership_checkout(result)
        except RuntimeError as error:
            payment = {"configured": True, "message": str(error)}
        return {**result, "payment": payment}

    def register_admin(self, payload):
        gateway = self.gateway()
        pay = payload.get("pagar_con_stripe", False)
        if pay:
            gateway.validate_configuration()
        result = self.clients.register_admin_client(payload)
        payment = None
        if pay:
            try:
                payment = gateway.create_membership_checkout(result, admin=True)
            except (RuntimeError, ValueError) as error:
                # El registro persiste y el pago puede retomarse sin duplicarlo.
                payment = {"configured": gateway.configured, "message": str(error)}
        return {**result, "payment": payment}

    def start_admin_checkout(self, client_id):
        result = self.clients.get_admin_payment_registration(client_id)
        gateway = self.gateway()
        gateway.validate_configuration()
        return gateway.create_membership_checkout(result, admin=True)

    def confirm_membership(self, session_id, checkout=None):
        return confirm_verified_checkout(session_id, self.clients, self.settings, checkout,
                                         gateway=self.gateway(), notify=self.notify)

    def confirm_return(self, session_id):
        checkout = self.gateway().get_checkout_session(session_id)
        if _is_store_checkout(checkout):
            return confirmar_sesion_tienda(checkout, self.gym, self.settings)
        return self.confirm_membership(session_id, checkout)

    def process_webhook(self, payload, signature):
        gateway = self.gateway()
        event = gateway.construct_webhook_event(payload, signature)
        event_type = str(_value(event, "type", "") or "")
        if event_type not in {"checkout.session.completed", "checkout.session.async_payment_succeeded", "checkout.session.expired"}:
            return {"received": True}
        checkout = _value(_value(event, "data", {}) or {}, "object", {}) or {}
        session_id = str(_value(checkout, "id", "") or "")
        if not session_id:
            raise ValueError("El webhook de Stripe no contiene una sesión")
        if _is_store_checkout(checkout):
            if event_type == "checkout.session.expired":
                cancelar_por_sesion_expirada(checkout, self.gym)
            else:
                try:
                    confirmar_sesion_tienda(gateway.get_checkout_session(session_id), self.gym, self.settings)
                except PedidoCanceladoConPagoError as error:
                    # Reintentar no reembolsa automáticamente este cobro.
                    logger.error("REEMBOLSO MANUAL REQUERIDO (sesión %s): %s", session_id, error)
        elif event_type != "checkout.session.expired":
            result = self.confirm_membership(session_id)
            if (result.get("notification") or {}).get("status") == "error":
                raise RuntimeError("Pago confirmado; no se pudo guardar la notificación de correo")
        return {"received": True}

    def activate(self, client_id):
        saved = self.clients.activate_client_membership(client_id)
        notification = self.notify(self.settings, self.clients, saved, "activation")
        return {**saved, "notification": notification}

    def retry_activation_notification(self, client_id):
        client = self.gym.get_cliente(client_id)
        membership = self.gym.latest_membership(client_id)
        if not client or not membership:
            raise EntityNotFound("Cliente o membresía no encontrados")
        if any(str(row.get("estado") or "").upper() not in {"ACTIVO", "ACTIVA"} for row in (client, membership)):
            raise ValueError("La cuenta debe estar activa para enviar este correo")
        return self.notify(self.settings, self.clients, {"cliente": client, "membresia": membership}, "activation")
