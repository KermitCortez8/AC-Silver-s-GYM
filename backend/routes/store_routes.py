from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import PedidoTiendaInput, ProductoTiendaInput
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/tienda", tags=["tienda"])


@router.get("")
def list_productos(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.productos_tienda()


@router.get("/pedidos")
def list_pedidos(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.pedidos_tienda()


@router.post("/pedidos", status_code=status.HTTP_201_CREATED)
def create_pedido(payload: PedidoTiendaInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.crear_pedido_tienda(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("")
def upsert_producto(payload: ProductoTiendaInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.upsert_producto_tienda(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(id_producto: int, gym_service: GymDomainService = Depends(get_gym_service)):
    gym_service.delete_producto_tienda(id_producto)
