# Módulo: inventory_routes.
# Expone productos, existencias y movimientos de inventario.
# Valida los permisos antes de cambiar el stock.
# Mantiene las operaciones de almacén en rutas dedicadas.
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from dependencies import get_gym_service, get_optional_actor_id
from models.gym import InventarioInput, MovimientoInventarioInput, MovimientoInventarioUpdateInput
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/inventario", tags=["inventario"])


# GET /inventario: lista el inventario completo.
@router.get("")
# Obtiene los datos necesarios.
def list_inventario(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.inventario()


# POST /inventario: crea o actualiza un ítem de inventario.
@router.post("")
# Actualiza el registro correspondiente.
def upsert_inventario(
    payload: InventarioInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    actor_id: str | None = Depends(get_optional_actor_id),
):
    try:
        return gym_service.upsert_inventario(payload.model_dump(), actor=actor_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# DELETE /inventario/{id_item}: elimina el ítem; si tiene historial o producto en tienda lo descontinúa.
@router.delete("/{id_item}")
# Elimina el registro indicado.
def delete_inventario(id_item: int, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        item = gym_service.delete_inventario(id_item)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if item is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return {"accion": "descontinuado", "item": item}


# GET /inventario/movimientos: lista los movimientos registrados.
@router.get("/movimientos")
# Obtiene los datos necesarios.
def list_movimientos(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.movimientos_inventario()


# POST /inventario/movimientos: registra una entrada, salida o ajuste de stock.
@router.post("/movimientos")
# Procesa esta operación.
def registrar_movimiento(payload: MovimientoInventarioInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.registrar_movimiento_inventario(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


# PUT /inventario/movimientos/{id_mov}: corrige un movimiento y recalcula el stock.
@router.put("/movimientos/{id_mov}")
# Actualiza el registro correspondiente.
def actualizar_movimiento(id_mov: int, payload: MovimientoInventarioUpdateInput, gym_service: GymDomainService = Depends(get_gym_service)):
    try:
        return gym_service.actualizar_movimiento_inventario(id_mov, payload.model_dump(exclude_none=True))
    except ValueError as error:
        status_code = status.HTTP_404_NOT_FOUND if "no encontrado" in str(error).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(error)) from error
