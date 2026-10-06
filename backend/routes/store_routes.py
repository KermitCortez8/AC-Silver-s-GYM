# Módulo: store_routes.
# Gestiona productos, pedidos y pagos de la tienda.
# Valida el contenido de cada pedido antes de guardarlo.
# Conecta las operaciones comerciales con el inventario.
from __future__ import annotations

from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from config import Settings, get_settings
from dependencies import get_clients_service, get_current_user, get_gym_service, get_optional_actor_id
from models.gym import (
    PedidoTiendaCheckoutInput,
    PedidoTiendaInput,
    PedidoTiendaUpdateInput,
    ProductoTiendaInput,
)
from models.auth import UserProfile
from services.clients_service import ClientsService
from services.gym_domain_service import GymDomainService, PedidoCanceladoConPagoError
from services.supabase_storage_service import SupabaseStorageService
from services.store_checkout_service import (
    cancelar_checkout_tienda,
    cerrar_sesion_si_pago_pendiente,
    iniciar_checkout_tienda,
)

router = APIRouter(prefix="/tienda", tags=["tienda"])
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


# Procesa esta operación.
def _safe_image_name(filename: str) -> str:
    raw_name = Path(filename or "producto.jpg").stem
    extension = Path(filename or "").suffix.lower() or ".jpg"
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no permitido")

    safe_name = re.sub(r"[^a-zA-Z0-9]+", "-", raw_name).strip("-").lower() or "producto"
    return f"{safe_name}-{uuid4().hex[:12]}{extension}"


# Obtiene los datos necesarios.
def _get_storage_service() -> SupabaseStorageService | None:
    settings = get_settings()
    if not settings.has_supabase_credentials:
        return None

    return SupabaseStorageService(
        settings.supabase_url,
        settings.supabase_key,
        settings.store_images_bucket,
    )


# Procesa esta operación.
def _local_upload_dir() -> Path:
    settings = get_settings()
    upload_dir = Path(settings.store_images_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


# Procesa esta operación.
def _local_image_url(filename: str) -> str:
    return f"/api/uploads/store-images/{filename}"

# Traduce los errores del dominio y de Stripe a respuestas HTTP.
def _http_error(error: Exception) -> HTTPException:
    message = str(error)
    if isinstance(error, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
    if isinstance(error, PedidoCanceladoConPagoError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
    if isinstance(error, RuntimeError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)
    code = status.HTTP_404_NOT_FOUND if "no encontrado" in message.lower() else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=message)

@router.get("")
# Obtiene los datos necesarios.
def list_productos(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.productos_tienda()


@router.get("/pedidos")
# Obtiene los datos necesarios.
def list_pedidos(gym_service: GymDomainService = Depends(get_gym_service)):
    return gym_service.pedidos_tienda()


@router.post("/pedidos", status_code=status.HTTP_201_CREATED)
# Crea el registro correspondiente (Yape, Plin y transferencia; la tarjeta usa /pedidos/checkout).
def create_pedido(payload: PedidoTiendaInput, gym_service: GymDomainService = Depends(get_gym_service)):
    if "tarjeta" in str(payload.metodo_pago or "").strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago con tarjeta se realiza desde la pasarela de pago",
        )
    try:
        return gym_service.crear_pedido_tienda(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

@router.post("/pedidos/checkout", status_code=status.HTTP_201_CREATED)
# Crea el pedido con tarjeta (stock reservado) y la sesión de Stripe; devuelve payment.checkout_url.
def create_pedido_checkout(
    payload: PedidoTiendaCheckoutInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        return iniciar_checkout_tienda(gym_service, clients_service, settings, current_user, payload.model_dump())
    except (ValueError, RuntimeError, PermissionError) as error:
        raise _http_error(error) from error


@router.post("/pedidos/{id_pedido}/cancelar-pago")
# El cliente canceló en Stripe: cancela el pedido, devuelve el stock y entrega los productos para rearmar el carrito.
def cancelar_pago_pedido(
    id_pedido: int,
    gym_service: GymDomainService = Depends(get_gym_service),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        return cancelar_checkout_tienda(gym_service, clients_service, settings, current_user, id_pedido)
    except (ValueError, RuntimeError, PermissionError) as error:
        raise _http_error(error) from error

@router.put("/pedidos/{id_pedido}")
# Actualiza el registro correspondiente.
def update_pedido(
    id_pedido: int,
    payload: PedidoTiendaUpdateInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    settings: Settings = Depends(get_settings),
    actor_id: str | None = Depends(get_optional_actor_id),
):
    try:
        if payload.estado_pedido == "CANCELADO":
            cerrar_sesion_si_pago_pendiente(gym_service, settings, id_pedido)
        return gym_service.actualizar_pedido_tienda(id_pedido, payload.model_dump(), actor=actor_id)
    except (ValueError, RuntimeError, PermissionError) as error:
        raise _http_error(error) from error


@router.post("")
# Actualiza el registro correspondiente.
def upsert_producto(
    payload: ProductoTiendaInput,
    gym_service: GymDomainService = Depends(get_gym_service),
    actor_id: str | None = Depends(get_optional_actor_id),
):
    try:
        return gym_service.upsert_producto_tienda(payload.model_dump(), actor=actor_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        
@router.get("/imagenes")
# Obtiene los datos necesarios.
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
# Procesa esta operación.
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
# Elimina el registro indicado.
def delete_producto(id_producto: int, gym_service: GymDomainService = Depends(get_gym_service)):
    gym_service.delete_producto_tienda(id_producto)
