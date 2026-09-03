# Módulo: clients_routes.
# Gestiona el registro público y administrativo de clientes.
# Inicia Stripe Checkout y recibe confirmaciones firmadas del pago.
# Protege las operaciones internas con permisos de usuario.
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from config import Settings, get_settings
from dependencies import get_clients_service, get_current_user, require_admin_or_staff
from models.gym import ClienteInput, RegistroPublicoClienteInput
from models.auth import UserProfile
from services.clients_service import ClientsService
from services.stripe_service import StripeService

router = APIRouter(tags=["clientes"])


def _value(item, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _confirm_verified_checkout(
    session_id: str,
    clients_service: ClientsService,
    settings: Settings,
) -> dict:
    """Consulta Stripe y persiste únicamente una sesión completa y pagada."""
    gateway = StripeService(settings)
    checkout = gateway.get_checkout_session(session_id)
    expected_live_mode = str(getattr(settings, "stripe_mode", "test") or "test").lower() == "live"
    if bool(_value(checkout, "livemode", False)) != expected_live_mode:
        raise ValueError("La sesión de Stripe no corresponde al modo configurado")
    payment_status = str(_value(checkout, "payment_status", "") or "").lower()
    checkout_status = str(_value(checkout, "status", "") or "").lower()
    if payment_status != "paid" or checkout_status != "complete":
        return {"confirmed": False, "payment_status": payment_status or checkout_status or "unknown"}
    if str(_value(checkout, "mode", "") or "").lower() != "payment":
        raise ValueError("La sesión de Stripe no corresponde a un pago")

    external_reference = str(_value(checkout, "client_reference_id", "") or "")
    prefix, separator, raw_client_id = external_reference.partition(":")
    if prefix != "membership" or not separator or not raw_client_id.isdigit():
        raise ValueError("Referencia externa de pago inválida")

    metadata = _value(checkout, "metadata", {}) or {}
    metadata_client_id = str(_value(metadata, "client_id", "") or "")
    raw_membership_id = str(_value(metadata, "membership_id", "") or "")
    if (
        str(_value(metadata, "purpose", "") or "") != "membership"
        or metadata_client_id != raw_client_id
        or not raw_membership_id.isdigit()
        or int(raw_membership_id) <= 0
    ):
        raise ValueError("Los metadatos de la sesión de Stripe no coinciden con la membresía")

    currency = str(_value(checkout, "currency", "") or "").lower()
    amount_total = int(_value(checkout, "amount_total", 0) or 0)
    if currency != "pen" or amount_total <= 0:
        raise ValueError("La moneda o el importe del pago no es válido")

    verified_session_id = str(_value(checkout, "id", "") or session_id)
    saved = clients_service.confirm_public_payment(
        int(raw_client_id),
        {
            "id_membresia": int(raw_membership_id),
            "monto_pago": amount_total / 100,
            "metodo_pago": "stripe",
            "referencia_pago": verified_session_id,
        },
    )
    return {
        "confirmed": True,
        "payment_status": "paid",
        "id_cliente": int(raw_client_id),
        "membership_status": str((saved.get("membresia") or {}).get("estado") or "EN_TRAMITE"),
        "message": "Su cuenta ha sido inicializada. A la espera de activación de membresía.",
    }


@router.get("/clientes")
# Obtiene los datos necesarios.
def list_clientes(
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    return clients_service.list_clients()


@router.get("/clientes/me")
# Obtiene los datos necesarios.
def get_mi_cliente(
    clients_service: ClientsService = Depends(get_clients_service),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        return clients_service.get_client_for_user(current_user)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/clientes")
# Actualiza el registro correspondiente.
def upsert_cliente(
    payload: ClienteInput,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return clients_service.upsert_client(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/registro-publico")
# Procesa esta operación.
def registro_publico(
    payload: RegistroPublicoClienteInput,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
):
    if not settings.has_supabase_credentials:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase debe estar configurado para registrar pagos de membresía",
        )
    gateway = StripeService(settings)
    if not gateway.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe no está configurado en backend/.env",
        )
    try:
        gateway.validate_configuration()
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    try:
        result = clients_service.register_public_client(payload.model_dump())
        try:
            payment = gateway.create_membership_checkout(result)
        except RuntimeError as error:
            payment = {"configured": True, "message": str(error)}
        return {**result, "payment": payment}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/pagos/stripe/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
):
    payload = await request.body()
    gateway = StripeService(settings)
    try:
        event = gateway.construct_webhook_event(payload, stripe_signature)
        event_type = str(_value(event, "type", "") or "")
        if event_type not in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            return {"received": True}
        event_data = _value(event, "data", {}) or {}
        checkout = _value(event_data, "object", {}) or {}
        session_id = str(_value(checkout, "id", "") or "")
        if not session_id:
            raise ValueError("El webhook de Stripe no contiene una sesión")
        _confirm_verified_checkout(session_id, clients_service, settings)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    return {"received": True}


@router.post("/pagos/stripe/confirmar-retorno", status_code=status.HTTP_200_OK)
def confirmar_retorno_stripe(
    session_id: str = Query(min_length=1),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
):
    """Confirma el pago al volver del checkout sin confiar en los parámetros del navegador."""
    try:
        return _confirm_verified_checkout(session_id, clients_service, settings)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.post("/clientes/{id_cliente}/activar-membresia")
# Procesa esta operación.
def activar_membresia_cliente(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return clients_service.activate_client_membership(id_cliente)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/clientes/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
# Elimina el registro indicado.
def delete_cliente(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    clients_service.delete_client(f"SGCLI{id_cliente:03d}")
