# Módulo: clients_routes.
# Gestiona el registro público y administrativo de clientes.
# Inicia Stripe Checkout y recibe confirmaciones firmadas del pago.
# Protege las operaciones internas con permisos de usuario.

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from presentation.dependencies import Settings, get_settings
from presentation.dependencies import (
    get_clients_service,
    get_current_user,
    get_gym_service,
    require_admin_or_staff,
)
from domain.models.gym import (
    ClienteInput,
    RegistroAdminClienteInput,
    RegistroPublicoClienteInput,
)
from domain.models.auth import UserProfile
from application.services.gym_service import GymService
from domain.services.gym_domain_service import PedidoCanceladoConPagoError
from application.services.clients_service import ClientsService
from app.bootstrap import create_payment_gateway as StripeService
from application.services.membership_checkout_service import confirm_verified_checkout, _value, _is_store_checkout
from app.bootstrap import notify_membership
from application.services.store_checkout_service import (
    cancelar_por_sesion_expirada,
    confirmar_sesion_tienda,
)


router = APIRouter(tags=["clientes"])
logger = logging.getLogger(__name__)




# Indica si la sesión de Stripe corresponde a un pedido de tienda
# (y no a una membresía).


def _confirm_verified_checkout(session_id, clients_service, settings, checkout=None):
    return confirm_verified_checkout(
        session_id, clients_service, settings, checkout,
        gateway=StripeService(settings), notify=notify_membership,
    )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


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
            detail=(
                "Supabase debe estar configurado "
                "para registrar pagos de membresía"
            ),
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
        result = clients_service.register_public_client(
            payload.model_dump()
        )

        try:
            payment = gateway.create_membership_checkout(
                result
            )

        except RuntimeError as error:
            payment = {
                "configured": True,
                "message": str(error),
            }

        return {
            **result,
            "payment": payment,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post(
    "/clientes/registro-admin",
    status_code=status.HTTP_201_CREATED,
)
def registro_admin(
    payload: RegistroAdminClienteInput,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    _current_user=Depends(require_admin_or_staff),
):
    gateway = StripeService(settings)

    try:
        if payload.pagar_con_stripe:
            gateway.validate_configuration()

        result = clients_service.register_admin_client(
            payload.model_dump()
        )

        payment = None

        if payload.pagar_con_stripe:
            try:
                payment = gateway.create_membership_checkout(
                    result,
                    admin=True,
                )

            except (RuntimeError, ValueError) as error:
                # El registro ya existe:
                # permite retomar el pago sin duplicar al cliente.
                payment = {
                    "configured": gateway.configured,
                    "message": str(error),
                }

        return {
            **result,
            "payment": payment,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post("/clientes/{id_cliente}/pago-stripe")
def pago_stripe_admin(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        result = clients_service.get_admin_payment_registration(
            id_cliente
        )

        gateway = StripeService(settings)

        gateway.validate_configuration()

        return gateway.create_membership_checkout(
            result,
            admin=True,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post(
    "/pagos/stripe/webhook",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(
        default="",
        alias="Stripe-Signature",
    ),
    clients_service: ClientsService = Depends(get_clients_service),
    gym_service: GymService = Depends(get_gym_service),
    settings: Settings = Depends(get_settings),
):
    payload = await request.body()

    gateway = StripeService(settings)

    try:
        event = gateway.construct_webhook_event(
            payload,
            stripe_signature,
        )

        event_type = str(
            _value(event, "type", "") or ""
        )

        if event_type not in {
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
            "checkout.session.expired",
        }:
            return {
                "received": True,
            }

        event_data = (
            _value(event, "data", {}) or {}
        )

        checkout = (
            _value(event_data, "object", {}) or {}
        )

        session_id = str(
            _value(checkout, "id", "") or ""
        )

        if not session_id:
            raise ValueError(
                "El webhook de Stripe no contiene una sesión"
            )

        if _is_store_checkout(checkout):
            if event_type == "checkout.session.expired":
                cancelar_por_sesion_expirada(
                    checkout,
                    gym_service,
                )

            else:
                try:
                    confirmar_sesion_tienda(
                        gateway.get_checkout_session(
                            session_id
                        ),
                        gym_service,
                        settings,
                    )

                except PedidoCanceladoConPagoError as error:
                    # Se responde 200:
                    # reintentar no lo arregla.
                    # Hay que reembolsar el pago a mano en Stripe.
                    logger.error(
                        "REEMBOLSO MANUAL REQUERIDO "
                        "(sesión %s): %s",
                        session_id,
                        error,
                    )

            return {
                "received": True,
            }

        if event_type == "checkout.session.expired":
            # Las membresías no usan este evento.
            return {
                "received": True,
            }

        result = _confirm_verified_checkout(
            session_id,
            clients_service,
            settings,
        )

        if (
            (result.get("notification") or {}).get("status")
            == "error"
        ):
            # Stripe reintenta si no se pudo persistir
            # el correo; el pago es idempotente.
            raise RuntimeError(
                "Pago confirmado; "
                "no se pudo guardar la notificación de correo"
            )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    return {
        "received": True,
    }


@router.post(
    "/pagos/stripe/confirmar-retorno",
    status_code=status.HTTP_200_OK,
)
def confirmar_retorno_stripe(
    session_id: str = Query(min_length=1),
    clients_service: ClientsService = Depends(get_clients_service),
    gym_service: GymService = Depends(get_gym_service),
    settings: Settings = Depends(get_settings),
):
    """
    Confirma el pago al volver del checkout
    sin confiar en los parámetros del navegador.
    """

    try:
        checkout = StripeService(
            settings
        ).get_checkout_session(session_id)

        if _is_store_checkout(checkout):
            return confirmar_sesion_tienda(
                checkout,
                gym_service,
                settings,
            )

        return _confirm_verified_checkout(
            session_id,
            clients_service,
            settings,
            checkout,
        )

    except PedidoCanceladoConPagoError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/clientes/{id_cliente}/activar-membresia")
# Procesa esta operación.
def activar_membresia_cliente(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        saved = clients_service.activate_client_membership(
            id_cliente
        )

        notification = notify_membership(
            settings,
            clients_service,
            saved,
            "activation",
        )

        return {
            **saved,
            "notification": notification,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/clientes/{id_cliente}/notificar-activacion"
)
def retry_activation_notification(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    _current_user=Depends(require_admin_or_staff),
):
    """
    Reintenta el correo sin modificar
    el estado ni la vigencia de la cuenta.
    """

    client = clients_service.gym.get_cliente(
        id_cliente
    )

    membership = (
        clients_service.gym.latest_membership(
            id_cliente,
        )
    )

    if not client or not membership:
        raise HTTPException(
            status_code=404,
            detail="Cliente o membresía no encontrados",
        )

    if (
        str(client.get("estado") or "").upper()
        not in {"ACTIVO", "ACTIVA"}
        or str(membership.get("estado") or "").upper()
        not in {"ACTIVO", "ACTIVA"}
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "La cuenta debe estar activa "
                "para enviar este correo"
            ),
        )

    return notify_membership(
        settings,
        clients_service,
        {
            "cliente": client,
            "membresia": membership,
        },
        "activation",
    )


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
