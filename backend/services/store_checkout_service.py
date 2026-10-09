# Módulo: store_checkout_service.
# Orquesta el pago con tarjeta (Stripe Checkout) de los pedidos de la tienda.
# Reserva el stock al iniciar el pago, confirma el cobro y libera el stock si el pago no se completa.
# Lo usan las rutas de la tienda y el webhook de Stripe.
from __future__ import annotations

import logging
from typing import Any

from services.gym_domain_service import (
    ESTADO_PAGO_PAGADO,
    ESTADO_PEDIDO_CANCELADO,
    GymDomainService,
    PedidoCanceladoConPagoError,
)
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

# Un pedido sin sesión de Stripe nunca podrá cobrarse: pasado este tiempo se cancela y se devuelve el stock.
MINUTOS_PEDIDO_SIN_SESION = 10


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _gateway(settings: Any) -> StripeService:
    gateway = StripeService(settings)
    if not gateway.configured:
        raise RuntimeError("Stripe no está configurado en backend/.env")
    gateway.validate_configuration()
    return gateway


# Con Supabase, recarga el estado si la caché ya venció (los pedidos pueden venir de otra petición).
def _refrescar(gym: GymDomainService, resources=None) -> None:
    ensure_fresh = getattr(gym, "ensure_fresh", None)
    if callable(ensure_fresh):
        if resources is None:
            ensure_fresh()
        else:
            ensure_fresh(resources=resources)


def _cliente_de(clients_service: Any, usuario: Any) -> dict[str, Any] | None:
    try:
        return clients_service.get_client_for_user(usuario)
    except ValueError:
        return None


def _esta_pagado(pedido: dict[str, Any]) -> bool:
    return str(pedido.get("estado_pago") or ESTADO_PAGO_PAGADO).strip().upper() == ESTADO_PAGO_PAGADO


def _esta_cancelado(pedido: dict[str, Any]) -> bool:
    return str(pedido.get("estado_pedido") or "").strip().upper() == ESTADO_PEDIDO_CANCELADO


def _metadata(checkout: Any) -> Any:
    return _value(checkout, "metadata", {}) or {}


def _estado_sesion(checkout: Any) -> str:
    return str(_value(checkout, "status", "") or "").lower()


def _usuario_id(usuario: Any) -> str:
    return str(getattr(usuario, "id", "") or "")


def _sesion_es_de(session: Any, usuario: Any) -> bool:
    user_id = _usuario_id(usuario)
    return bool(user_id) and str(_value(_metadata(session), "user_id", "") or "") == user_id


# El pedido es del usuario si coincide su cliente; sin cliente, si la sesión de Stripe lleva su id de usuario.
def _es_dueno(pedido: dict[str, Any], session: Any, usuario: Any, cliente: dict[str, Any] | None) -> bool:
    id_cliente = int(pedido.get("id_cliente") or 0)
    if id_cliente:
        return bool(cliente) and id_cliente == int(cliente.get("id_cliente", 0) or 0)
    if session is None:
        return False
    return _sesion_es_de(session, usuario) and str(_value(_metadata(session), "pedido_id", "") or "") == str(
        pedido.get("id_pedido")
    )


def _items_pedido(pedido: dict[str, Any]) -> list[dict[str, int]]:
    return [
        {"id_producto": int(item.get("id_producto") or 0), "cantidad": int(item.get("cantidad") or 1)}
        for item in pedido.get("items") or []
    ]


# ---------------------------------------------------------------------------
# Confirmación del cobro
# ---------------------------------------------------------------------------
def confirmar_sesion_tienda(checkout: Any, gym: GymDomainService, settings: Any) -> dict[str, Any]:
    """Marca el pedido como PAGADO solo si Stripe confirma una sesión completa, pagada y coherente con el pedido."""
    expected_live_mode = str(getattr(settings, "stripe_mode", "test") or "test").lower() == "live"
    if bool(_value(checkout, "livemode", False)) != expected_live_mode:
        raise ValueError("La sesión de Stripe no corresponde al modo configurado")
    payment_status = str(_value(checkout, "payment_status", "") or "").lower()
    checkout_status = _estado_sesion(checkout)
    if payment_status != "paid" or checkout_status != "complete":
        return {"confirmed": False, "payment_status": payment_status or checkout_status or "unknown"}
    if str(_value(checkout, "mode", "") or "").lower() != "payment":
        raise ValueError("La sesión de Stripe no corresponde a un pago")

    external_reference = str(_value(checkout, "client_reference_id", "") or "")
    prefix, separator, raw_id = external_reference.partition(":")
    if prefix != "store" or not separator or not raw_id.isdigit():
        raise ValueError("Referencia externa de pago inválida")
    metadata = _metadata(checkout)
    if (
        str(_value(metadata, "purpose", "") or "") != "store"
        or str(_value(metadata, "pedido_id", "") or "") != raw_id
    ):
        raise ValueError("Los metadatos de la sesión de Stripe no coinciden con el pedido")

    currency = str(_value(checkout, "currency", "") or "").lower()
    amount_total = int(_value(checkout, "amount_total", 0) or 0)
    if currency != "pen" or amount_total <= 0:
        raise ValueError("La moneda o el importe del pago no es válido")

    pedido = gym.confirmar_pago_pedido_tienda(
        int(raw_id),
        {
            "monto_pago": amount_total / 100,
            "metodo_pago": "tarjeta",
            "referencia_pago": str(_value(checkout, "id", "") or ""),
        },
    )
    return {
        "confirmed": True,
        "payment_status": "paid",
        "id_pedido": int(raw_id),
        "total": float(pedido.get("total") or 0),
        "estado_pago": str(pedido.get("estado_pago") or ""),
    }


# ---------------------------------------------------------------------------
# Liberación de reservas
# ---------------------------------------------------------------------------
def _resolver_pedido_segun_sesion(gym: GymDomainService, settings: Any, id_pedido: int, session: Any) -> None:
    estado = _estado_sesion(session)
    if estado == "complete":
        confirmar_sesion_tienda(session, gym, settings)
    elif estado == "expired":
        gym.cancelar_pedido_pago_pendiente(
            id_pedido, "Sesión de pago expirada: pedido cancelado y stock devuelto"
        )


def procesar_pedidos_pendientes(
    gym: GymDomainService,
    gateway: StripeService,
    settings: Any,
    usuario: Any = None,
) -> None:
    """Revisa los pedidos con pago pendiente preguntando a Stripe por cada sesión.

    - Sesión pagada: confirma el pedido.
    - Sesión expirada: cancela el pedido y devuelve el stock.
    - Sesión abierta de `usuario`: la cierra y cancela el pedido (el usuario está empezando un pago nuevo).
    - Pedido sin sesión y con más de MINUTOS_PEDIDO_SIN_SESION minutos: lo cancela.
    Un fallo con un pedido no impide revisar los demás.
    """
    _refrescar(gym)
    for pedido in gym.pedidos_pago_pendiente():
        id_pedido = int(pedido.get("id_pedido", 0) or 0)
        session_id = str(pedido.get("referencia_pago") or "").strip()
        try:
            if not session_id:
                minutos = gym.minutos_desde_creacion(pedido)
                if minutos is not None and minutos >= MINUTOS_PEDIDO_SIN_SESION:
                    gym.cancelar_pedido_pago_pendiente(
                        id_pedido, "Pedido sin sesión de pago: cancelado y stock devuelto"
                    )
                continue
            session = gateway.get_checkout_session(session_id)
            if _estado_sesion(session) == "open" and usuario is not None and _sesion_es_de(session, usuario):
                session = gateway.expire_checkout_session(session_id)
            _resolver_pedido_segun_sesion(gym, settings, id_pedido, session)
        except PedidoCanceladoConPagoError as error:
            logger.error("REEMBOLSO MANUAL REQUERIDO (pedido %s): %s", id_pedido, error)
        except (ValueError, RuntimeError) as error:
            logger.warning("No se pudo revisar el pedido pendiente %s: %s", id_pedido, error)


def cancelar_por_sesion_expirada(checkout: Any, gym: GymDomainService) -> None:
    """Webhook checkout.session.expired: cancela el pedido y devuelve el stock."""
    session_id = str(_value(checkout, "id", "") or "")
    raw_id = str(_value(_metadata(checkout), "pedido_id", "") or "")
    if not session_id or not raw_id.isdigit():
        return
    _refrescar(gym)
    pedido = gym.get_pedido_tienda(int(raw_id))
    if not pedido or str(pedido.get("referencia_pago") or "").strip() != session_id or _esta_pagado(pedido):
        return
    gym.cancelar_pedido_pago_pendiente(int(raw_id), "Sesión de pago expirada: pedido cancelado y stock devuelto")


def cerrar_sesion_si_pago_pendiente(gym: GymDomainService, settings: Any, id_pedido: int) -> None:
    """Antes de que un admin cancele un pedido sin cobrar, cierra su sesión de Stripe para que nadie lo pague después."""
    _refrescar(gym, resources=("pedidos_tienda", "inventario", "productos_tienda", "mov_inv", "usuario"))
    pedido = gym.get_pedido_tienda(id_pedido)
    if not pedido or _esta_pagado(pedido) or _esta_cancelado(pedido):
        return
    session_id = str(pedido.get("referencia_pago") or "").strip()
    if not session_id:
        return
    session = _gateway(settings).expire_checkout_session(session_id)
    estado = _estado_sesion(session)
    if estado == "complete":
        confirmar_sesion_tienda(session, gym, settings)
        raise ValueError("El pedido se acaba de pagar con tarjeta; actualiza la lista de pedidos")
    if estado == "open":
        raise RuntimeError("No se pudo cerrar la sesión de pago en Stripe. Inténtalo de nuevo.")


# ---------------------------------------------------------------------------
# Inicio y cancelación del checkout
# ---------------------------------------------------------------------------
def iniciar_checkout_tienda(
    gym: GymDomainService,
    clients_service: Any,
    settings: Any,
    usuario: Any,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Crea el pedido pendiente (reservando stock) y la sesión de Stripe. Devuelve la URL del checkout."""
    gateway = _gateway(settings)
    # Libera reservas vencidas y cierra los pagos abiertos anteriores de este usuario antes de reservar stock nuevo.
    procesar_pedidos_pendientes(gym, gateway, settings, usuario=usuario)

    cliente = _cliente_de(clients_service, usuario)
    cliente = cliente or {}
    nombre = (
        str(payload.get("cliente_nombre") or "").strip()
        or str(cliente.get("nombre") or "").strip()
        or str(getattr(usuario, "name", "") or "").strip()
        or "Cliente"
    )
    correo = (
        str(payload.get("cliente_correo") or "").strip()
        or str(cliente.get("correo") or "").strip()
        or str(getattr(usuario, "email", "") or "").strip()
    )
    if "@" not in correo:
        correo = ""
    dni = (
        str(payload.get("cliente_dni") or "").strip()
        or str(cliente.get("dni") or "").strip()
        or str(getattr(usuario, "dni", "") or "").strip()
    )

    # El id_cliente sale del token, nunca de lo que envía el navegador.
    pedido = gym.crear_pedido_tienda_pago_pendiente(
        {
            "id_cliente": cliente.get("id_cliente"),
            "cliente_nombre": nombre,
            "cliente_correo": correo,
            "cliente_dni": dni,
            "items": payload.get("items") or [],
        }
    )
    id_pedido = int(pedido["id_pedido"])

    session_id = ""
    try:
        payment = gateway.create_store_checkout(pedido, customer_email=correo, user_id=_usuario_id(usuario))
        session_id = str(payment.get("session_id") or "")
        if not session_id or not payment.get("checkout_url"):
            raise RuntimeError("Stripe no devolvió una sesión de pago válida")
        gym.registrar_sesion_pago_pedido(id_pedido, session_id)
    except Exception as error:
        logger.warning("No se pudo iniciar el pago del pedido %s: %s", id_pedido, error)
        if session_id:
            try:
                gateway.expire_checkout_session(session_id)
            except Exception:
                logger.exception("No se pudo cerrar la sesión %s tras el fallo", session_id)
        try:
            gym.cancelar_pedido_pago_pendiente(id_pedido, "No se pudo iniciar el pago: pedido cancelado y stock devuelto")
        except Exception:
            logger.exception("No se pudo cancelar el pedido %s tras el fallo", id_pedido)
        if isinstance(error, (ValueError, RuntimeError)):
            raise
        raise RuntimeError("No se pudo iniciar el pago con tarjeta") from error

    return {"pedido": gym.get_pedido_tienda(id_pedido) or pedido, "payment": payment}


def cancelar_checkout_tienda(
    gym: GymDomainService,
    clients_service: Any,
    settings: Any,
    usuario: Any,
    id_pedido: int,
) -> dict[str, Any]:
    """El cliente canceló en Stripe: cierra la sesión, cancela el pedido y devuelve los productos para rearmar el carrito."""
    gateway = _gateway(settings)
    _refrescar(gym)
    pedido = gym.get_pedido_tienda(id_pedido)
    if not pedido:
        raise ValueError("Pedido no encontrado")

    session_id = str(pedido.get("referencia_pago") or "").strip()
    session = gateway.get_checkout_session(session_id) if session_id and not _esta_pagado(pedido) else None
    if not _es_dueno(pedido, session, usuario, _cliente_de(clients_service, usuario)):
        raise PermissionError("El pedido no pertenece al usuario")

    if _esta_pagado(pedido):
        return {"cancelled": False, "paid": True, "id_pedido": int(id_pedido), "items": []}

    if session is not None:
        session = gateway.expire_checkout_session(session_id)
        estado = _estado_sesion(session)
        if estado == "complete":
            # El cliente pagó justo antes de cancelar: se respeta el pago.
            confirmar_sesion_tienda(session, gym, settings)
            return {"cancelled": False, "paid": True, "id_pedido": int(id_pedido), "items": []}
        if estado == "open":
            raise RuntimeError("No se pudo cerrar la sesión de pago en Stripe. Inténtalo de nuevo.")

    ya_cancelado = _esta_cancelado(pedido)
    cancelado = gym.cancelar_pedido_pago_pendiente(
        int(id_pedido), "Pago cancelado por el cliente: pedido cancelado y stock devuelto"
    )
    return {
        "cancelled": True,
        "paid": False,
        "already_cancelled": ya_cancelado,
        "id_pedido": int(id_pedido),
        "items": _items_pedido(cancelado),
    }
