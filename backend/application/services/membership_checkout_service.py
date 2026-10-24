"""Verificación y confirmación de pagos de membresías, con pasarela inyectada."""
from application.services.clients_service import ClientsService


def _value(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)

def _is_store_checkout(checkout) -> bool:
    return (
        str(
            _value(
                _value(checkout, "metadata", {}) or {},
                "purpose",
                "",
            )
            or ""
        )
        == "store"
    )

def confirm_verified_checkout(
    session_id: str,
    clients_service: ClientsService,
    settings,
    checkout=None,
    *, gateway, notify,
) -> dict:
    """Consulta Stripe y persiste únicamente una sesión completa y pagada."""


    if checkout is None:
        checkout = gateway.get_checkout_session(session_id)

    expected_live_mode = (
        str(getattr(settings, "stripe_mode", "test") or "test").lower()
        == "live"
    )

    if bool(_value(checkout, "livemode", False)) != expected_live_mode:
        raise ValueError(
            "La sesión de Stripe no corresponde al modo configurado"
        )

    payment_status = str(
        _value(checkout, "payment_status", "") or ""
    ).lower()

    checkout_status = str(
        _value(checkout, "status", "") or ""
    ).lower()

    if payment_status != "paid" or checkout_status != "complete":
        return {
            "confirmed": False,
            "payment_status": payment_status
            or checkout_status
            or "unknown",
        }

    if str(_value(checkout, "mode", "") or "").lower() != "payment":
        raise ValueError(
            "La sesión de Stripe no corresponde a un pago"
        )

    external_reference = str(
        _value(checkout, "client_reference_id", "") or ""
    )

    prefix, separator, raw_client_id = external_reference.partition(":")

    if (
        prefix != "membership"
        or not separator
        or not raw_client_id.isdigit()
    ):
        raise ValueError(
            "Referencia externa de pago inválida"
        )

    metadata = _value(checkout, "metadata", {}) or {}

    metadata_client_id = str(
        _value(metadata, "client_id", "") or ""
    )

    raw_membership_id = str(
        _value(metadata, "membership_id", "") or ""
    )

    if (
        str(_value(metadata, "purpose", "") or "") != "membership"
        or metadata_client_id != raw_client_id
        or not raw_membership_id.isdigit()
        or int(raw_membership_id) <= 0
    ):
        raise ValueError(
            "Los metadatos de la sesión de Stripe no coinciden con la membresía"
        )

    currency = str(
        _value(checkout, "currency", "") or ""
    ).lower()

    amount_total = int(
        _value(checkout, "amount_total", 0) or 0
    )

    if currency != "pen" or amount_total <= 0:
        raise ValueError(
            "La moneda o el importe del pago no es válido"
        )

    verified_session_id = str(
        _value(checkout, "id", "") or session_id
    )

    saved = clients_service.confirm_public_payment(
        int(raw_client_id),
        {
            "id_membresia": int(raw_membership_id),
            "monto_pago": amount_total / 100,
            "metodo_pago": "stripe",
            "referencia_pago": verified_session_id,
        },
    )

    notification = notify(
        settings,
        clients_service,
        saved,
        "payment",
    )

    return {
        "confirmed": True,
        "payment_status": "paid",
        "id_cliente": int(raw_client_id),
        "membership_status": str(
            (saved.get("membresia") or {}).get("estado")
            or "EN_TRAMITE"
        ),
        "message": (
            "Su cuenta ha sido inicializada. "
            "A la espera de activación de membresía."
        ),
        "notification": notification,
    }

