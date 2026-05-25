from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service
from models.gym import InventarioInput, MovimientoInventarioInput
from services.gym_service import GymService

router = APIRouter(prefix="/inventario", tags=["inventario"])


# GET /inventario: lista el inventario completo.
@router.get("")
def list_inventario(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.inventario()


# POST /inventario: crea o actualiza un ítem de inventario.
@router.post("")
def upsert_inventario(payload: InventarioInput, gym_service: GymService = Depends(get_gym_service)):
    return gym_service.upsert_inventario(payload.model_dump())


# DELETE /inventario/{id_item}: elimina un ítem del inventario.
@router.delete("/{id_item}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventario(id_item: int, gym_service: GymService = Depends(get_gym_service)):
    gym_service.delete_inventario(id_item)


# GET /inventario/movimientos: lista los movimientos registrados.
@router.get("/movimientos")
def list_movimientos(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.movimientos_inventario()


# POST /inventario/movimientos: registra una entrada, salida o ajuste de stock.
@router.post("/movimientos")
def registrar_movimiento(payload: MovimientoInventarioInput, gym_service: GymService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_movimiento_inventario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
