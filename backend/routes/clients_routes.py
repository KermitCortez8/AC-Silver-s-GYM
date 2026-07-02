from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_clients_service, get_current_user, require_admin_or_staff
from models.gym import ClienteInput, PagoPublicoClienteInput, RegistroPublicoClienteInput
from models.auth import UserProfile
from services.clients_service import ClientsService

router = APIRouter(tags=["clientes"])


@router.get("/clientes")
def list_clientes(
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    return clients_service.list_clients()


@router.get("/clientes/me")
def get_mi_cliente(
    clients_service: ClientsService = Depends(get_clients_service),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        return clients_service.get_client_for_user(current_user)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/clientes")
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
def registro_publico(payload: RegistroPublicoClienteInput, clients_service: ClientsService = Depends(get_clients_service)):
    try:
        return clients_service.register_public_client(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/registro-publico/{id_cliente}/pago")
def confirmar_pago_publico(
    id_cliente: int,
    payload: PagoPublicoClienteInput,
    clients_service: ClientsService = Depends(get_clients_service),
):
    try:
        return clients_service.confirm_public_payment(id_cliente, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/clientes/{id_cliente}/activar-membresia")
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
def delete_cliente(
    id_cliente: int,
    clients_service: ClientsService = Depends(get_clients_service),
    _current_user=Depends(require_admin_or_staff),
):
    clients_service.delete_client(f"SGCLI{id_cliente:03d}")
