from __future__ import annotations

from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from config import get_settings
from dependencies import get_gym_service
from models.gym import PedidoTiendaInput, ProductoTiendaInput
from services.gym_domain_service import GymDomainService
from services.supabase_storage_service import SupabaseStorageService

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


def _get_storage_service() -> SupabaseStorageService | None:
    settings = get_settings()
    if not settings.has_supabase_credentials:
        return None

    return SupabaseStorageService(
        settings.supabase_url,
        settings.supabase_key,
        settings.store_images_bucket,
    )


def _local_upload_dir() -> Path:
    settings = get_settings()
    upload_dir = Path(settings.store_images_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _local_image_url(filename: str) -> str:
    return f"/api/uploads/store-images/{filename}"


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

        
@router.get("/imagenes")
def list_producto_imagenes():
    storage = _get_storage_service()
    if storage is not None:
        try:
            return storage.list_images()
        except RuntimeError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    upload_dir = _local_upload_dir()
    images: list[dict[str, str]] = []

    for image_path in sorted(upload_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            continue

        images.append(
            {
                "name": image_path.name,
                "path": image_path.name,
                "url": _local_image_url(image_path.name),
            }
        )

    return images


@router.post("/imagenes", status_code=status.HTTP_201_CREATED)
async def upload_producto_imagen(file: UploadFile = File(...)):
    if not str(file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecciona un archivo de imagen")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen esta vacia")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen supera 5 MB")

    filename = _safe_image_name(file.filename or "producto.jpg")
    storage = _get_storage_service()

    if storage is not None:
        try:
            return storage.upload(filename, data, str(file.content_type or "image/jpeg"))
        except RuntimeError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    upload_dir = _local_upload_dir()
    (upload_dir / filename).write_bytes(data)

    return {
        "name": filename,
        "path": filename,
        "url": _local_image_url(filename),
    }


@router.delete("/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(id_producto: int, gym_service: GymDomainService = Depends(get_gym_service)):
    gym_service.delete_producto_tienda(id_producto)
