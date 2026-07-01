from __future__ import annotations

from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from config import get_settings
from dependencies import get_gym_service
from models.gym import PedidoTiendaInput, ProductoTiendaInput
from services.gym_domain_service import GymDomainService

router = APIRouter(prefix="/tienda", tags=["tienda"])
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _safe_image_name(filename: str) -> str:
    raw_name = Path(filename or "producto.jpg").stem
    extension = Path(filename or "").suffix.lower() or ".jpg"
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no permitido")

    safe_name = re.sub(r"[^a-zA-Z0-9]+", "-", raw_name).strip("-").lower() or "producto"
    return f"{safe_name}-{uuid4().hex[:12]}{extension}"


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


@router.post("/imagenes", status_code=status.HTTP_201_CREATED)
async def upload_producto_imagen(file: UploadFile = File(...)):
    if not str(file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecciona un archivo de imagen")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen esta vacia")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen supera 5 MB")

    settings = get_settings()
    upload_dir = Path(settings.store_images_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = _safe_image_name(file.filename or "producto.jpg")
    (upload_dir / filename).write_bytes(data)

    return {
        "name": filename,
        "path": filename,
        "url": f"/api/uploads/store-images/{filename}",
    }


@router.delete("/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(id_producto: int, gym_service: GymDomainService = Depends(get_gym_service)):
    gym_service.delete_producto_tienda(id_producto)
