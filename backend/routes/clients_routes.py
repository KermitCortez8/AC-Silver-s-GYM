from __future__ import annotations

from fastapi import APIRouter, Depends, status

from dependencies import get_clients_service
from models.gym import ClienteInput
from services.clients_service import ClientsService

router = APIRouter(tags=["clientes"])


@router.get("/clientes")
def list_clientes(clients_service: ClientsService = Depends(get_clients_service)):
    return clients_service.list_clients()


@router.post("/clientes")
def upsert_cliente(payload: ClienteInput, clients_service: ClientsService = Depends(get_clients_service)):
    return clients_service.upsert_client(payload.model_dump())


@router.delete("/clientes/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(id_cliente: int, clients_service: ClientsService = Depends(get_clients_service)):
    clients_service.delete_client(f"SGCLI{id_cliente:03d}")
