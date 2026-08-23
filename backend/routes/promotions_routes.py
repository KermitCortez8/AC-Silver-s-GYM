from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_gym_service, require_admin_or_staff
from models.gym import PromocionInput
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/promociones", tags=["promociones"])


@router.get("")
def list_promociones(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.promociones()


@router.post("")
def upsert_promocion(
    payload: PromocionInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        return gym_service.upsert_promocion(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/{id_promocion}")
def update_promocion(
    id_promocion: int,
    payload: PromocionInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    data = payload.model_dump()
    data["id_promocion"] = id_promocion
    try:
        return gym_service.upsert_promocion(data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{id_promocion}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promocion(
    id_promocion: int,
    gym_service: GymDomainService = Depends(get_gym_service),
    _current_user=Depends(require_admin_or_staff),
):
    try:
        gym_service.delete_promocion(id_promocion)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
