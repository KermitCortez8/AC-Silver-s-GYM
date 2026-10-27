# Módulo: clients_routes.
# Gestiona el registro público y administrativo de clientes.
# Inicia Stripe Checkout y recibe confirmaciones firmadas del pago.
# Protege las operaciones internas con permisos de usuario.

from __future__ import annotations

from presentation.error_handlers import http_error


from starlette.concurrency import run_in_threadpool

from fastapi import APIRouter, Depends, Header, Query, Request, status

from presentation.dependencies import Settings, get_settings
from presentation.dependencies import (
    get_clients_service,
    get_current_user,
    require_admin_or_staff,
)
from domain.models.gym import (
    ClienteInput,
    RegistroAdminClienteInput,
    RegistroPublicoClienteInput,
)
from domain.models.auth import UserProfile
from domain.services.gym_domain_service import PedidoCanceladoConPagoError
from application.services.clients_service import ClientsService
from domain.errors import EntityNotFound
from presentation.dependencies import get_client_payments_service


router = APIRouter(tags=["clientes"])


def _payment_response(operation):
    try:
        return operation()
    except EntityNotFound as error:
        raise http_error(error, validation_status=404) from error
    except PedidoCanceladoConPagoError as error:
        raise http_error(error, validation_status=409) from error
    except ValueError as error:
        raise http_error(error, validation_status=400) from error
    except RuntimeError as error:
        raise http_error(error, validation_status=503) from error


@router.get("/pagos/membresias")
def list_pagos_membresias(
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    return clients_service.list_membership_payments()


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
        raise http_error(error, validation_status=status.HTTP_404_NOT_FOUND) from error


@router.post("/clientes")
# Actualiza el registro correspondiente.
def upsert_cliente(
    payload: ClienteInput,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return clients_service.upsert_client(
            payload.model_dump()
        )

    except ValueError as error:
        raise http_error(error, validation_status=status.HTTP_400_BAD_REQUEST) from error


@router.post("/registro-publico")
# Procesa esta operación.
def registro_publico(payload: RegistroPublicoClienteInput, payments=Depends(get_client_payments_service)):
    return _payment_response(lambda: payments.register_public(payload.model_dump()))


@router.post(
    "/clientes/registro-admin",
    status_code=status.HTTP_201_CREATED,
)
def registro_admin(payload: RegistroAdminClienteInput, payments=Depends(get_client_payments_service), _current_user=Depends(require_admin_or_staff)):
    return _payment_response(lambda: payments.register_admin(payload.model_dump()))


@router.post("/clientes/{id_cliente}/pago-stripe")
def pago_stripe_admin(id_cliente: int, payments=Depends(get_client_payments_service), _current_user=Depends(require_admin_or_staff)):
    return _payment_response(lambda: payments.start_admin_checkout(id_cliente))


@router.post(
    "/pagos/stripe/webhook",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="", alias="Stripe-Signature"),
                         payments=Depends(get_client_payments_service)):
    payload = await request.body()
    return await run_in_threadpool(_payment_response, lambda: payments.process_webhook(payload, stripe_signature))


@router.post(
    "/pagos/stripe/confirmar-retorno",
    status_code=status.HTTP_200_OK,
)
def confirmar_retorno_stripe(session_id: str = Query(min_length=1), payments=Depends(get_client_payments_service)):
    return _payment_response(lambda: payments.confirm_return(session_id))


@router.post("/clientes/{id_cliente}/activar-membresia")
# Procesa esta operación.
def activar_membresia_cliente(id_cliente: int, payments=Depends(get_client_payments_service), _current_user=Depends(require_admin_or_staff)):
    return _payment_response(lambda: payments.activate(id_cliente))


@router.post(
    "/clientes/{id_cliente}/confirmar-pago-manual"
)
def confirmar_pago_manual(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        saved = clients_service.confirm_manual_payment(
            id_cliente
        )

        return {
            "message": "Pago confirmado manualmente",
            "data": saved,
        }

    except ValueError as error:
        raise http_error(error, validation_status=status.HTTP_400_BAD_REQUEST) from error


@router.post(
    "/clientes/{id_cliente}/notificar-activacion"
)
def retry_activation_notification(id_cliente: int, payments=Depends(get_client_payments_service), _current_user=Depends(require_admin_or_staff)):
    return _payment_response(lambda: payments.retry_activation_notification(id_cliente))


@router.delete(
    "/clientes/{id_cliente}",
    status_code=status.HTTP_204_NO_CONTENT,
)
# Elimina el registro indicado.
def delete_cliente(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    clients_service.delete_client(
        f"SGCLI{id_cliente:03d}"
    )
