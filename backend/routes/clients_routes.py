# Módulo: clients_routes.
# Gestiona el registro público y administrativo de clientes.
# Inicia el checkout y recibe confirmaciones de Mercado Pago.
# Protege las operaciones internas con permisos de usuario.
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from config import Settings, get_settings
from dependencies import get_clients_service, get_current_user, require_admin_or_staff
from models.gym import ClienteInput, RegistroPublicoClienteInput
from models.auth import UserProfile
from services.clients_service import ClientsService
from services.mercado_pago_service import MercadoPagoService

router = APIRouter(tags=["clientes"])


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
    gateway = MercadoPagoService(settings)
    if not gateway.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mercado Pago no está configurado en backend/.env",
        )
    try:
        result = clients_service.register_public_client(payload.model_dump())
        try:
            payment = gateway.create_membership_checkout(result)
        except RuntimeError as error:
            payment = {"configured": True, "message": str(error)}
        return {**result, "payment": payment}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/pagos/mercado-pago/webhook", status_code=status.HTTP_200_OK)
# Procesa esta operación.
async def mercado_pago_webhook(
    request: Request,
    data_id: str = Query(default="", alias="data.id"),
    x_signature: str = Header(default=""),
    x_request_id: str = Header(default=""),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
):
    body = await request.json()
    payment_id = str(data_id or (body.get("data") or {}).get("id") or "")
    if not payment_id or str(body.get("type") or "payment") != "payment":
        return {"received": True}

    gateway = MercadoPagoService(settings)
    try:
        gateway.validate_webhook(x_signature, x_request_id, payment_id)
        payment = gateway.get_payment(payment_id)
        if payment.get("status") == "approved":
            external_reference = str(payment.get("external_reference") or "")
            prefix, separator, raw_client_id = external_reference.partition(":")
            if prefix != "membership" or not separator or not raw_client_id.isdigit():
                raise ValueError("Referencia externa de pago inválida")
            if str(payment.get("currency_id") or "") != "PEN" or not clients_service.payment_amount_matches(
                int(raw_client_id), float(payment.get("transaction_amount", 0) or 0)
            ):
                raise ValueError("El importe del pago no coincide con la membresía")
            clients_service.confirm_public_payment(
                int(raw_client_id),
                {"metodo_pago": "mercado_pago", "referencia_pago": str(payment.get("id") or payment_id)},
            )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    return {"received": True}

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
