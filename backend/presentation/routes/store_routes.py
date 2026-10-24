# Módulo: store_routes.
# Gestiona productos, pedidos y pagos de la tienda.
# Valida el contenido de cada pedido antes de guardarlo.
# Conecta las operaciones comerciales con el inventario.
from __future__ import annotations


from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from presentation.dependencies import Settings, get_settings, get_store_images_service
from presentation.dependencies import get_clients_service, get_current_user, get_gym_service, get_optional_actor_id, require_admin_or_staff
from domain.models.gym import (
    PedidoTiendaCheckoutInput,
    PedidoTiendaInput,
    PedidoTiendaUpdateInput,
    ProductoTiendaInput,
)
from domain.models.auth import UserProfile
from domain.errors import EntityNotFound
from application.services.clients_service import ClientsService
from application.services.gym_service import GymService
from domain.services.gym_domain_service import PedidoCanceladoConPagoError
from application.services.store_images_service import StoreImagesService, MAX_IMAGE_BYTES
from starlette.concurrency import run_in_threadpool
from application.services.store_checkout_service import (
    cancelar_checkout_tienda,
    actualizar_estado_pedido,
    iniciar_checkout_tienda,
)

router = APIRouter(prefix="/tienda", tags=["tienda"])
# Traduce los errores del dominio y de Stripe a respuestas HTTP.
def _http_error(error: Exception) -> HTTPException:
    message = str(error)
    if isinstance(error, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
    if isinstance(error, PedidoCanceladoConPagoError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
    if isinstance(error, RuntimeError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)
    code = status.HTTP_404_NOT_FOUND if isinstance(error, EntityNotFound) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=message)

@router.get("")
# Obtiene los datos necesarios.
def list_productos(gym_service: GymService = Depends(get_gym_service)):
    return gym_service.productos_tienda()


@router.get("/pedidos")
# Obtiene los datos necesarios.
def list_pedidos(gym_service: GymService = Depends(get_gym_service), user=Depends(get_current_user)):
    orders = gym_service.pedidos_tienda()
    if user.role in {"admin", "staff"}:
        return orders
    return [order for order in orders if user.id_cliente and order.get("id_cliente") == user.id_cliente]


@router.post("/pedidos", status_code=status.HTTP_201_CREATED)
# Crea el registro correspondiente (Yape, Plin y transferencia; la tarjeta usa /pedidos/checkout).
def create_pedido(payload: PedidoTiendaInput, gym_service: GymService = Depends(get_gym_service),
                  user=Depends(get_current_user)):
    if "tarjeta" in str(payload.metodo_pago or "").strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago con tarjeta se realiza desde la pasarela de pago",
        )
    try:
        data = payload.model_dump()
        if user.role not in {"admin", "staff"}:
            if not user.id_cliente:
                raise HTTPException(status_code=403, detail="La sesión no está vinculada a un cliente")
            data["id_cliente"] = user.id_cliente
        return gym_service.crear_pedido_tienda(data)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

@router.post("/pedidos/checkout", status_code=status.HTTP_201_CREATED)
# Crea el pedido con tarjeta (stock reservado) y la sesión de Stripe; devuelve payment.checkout_url.
def create_pedido_checkout(
    payload: PedidoTiendaCheckoutInput,
    gym_service: GymService = Depends(get_gym_service),
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
    gym_service: GymService = Depends(get_gym_service),
    clients_service: ClientsService = Depends(get_clients_service),
    settings: Settings = Depends(get_settings),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        return cancelar_checkout_tienda(gym_service, clients_service, settings, current_user, id_pedido)
    except (ValueError, RuntimeError, PermissionError) as error:
        raise _http_error(error) from error

@router.put("/pedidos/{id_pedido}", dependencies=[Depends(require_admin_or_staff)])
# Actualiza el registro correspondiente.
def update_pedido(
    id_pedido: int,
    payload: PedidoTiendaUpdateInput,
    gym_service: GymService = Depends(get_gym_service),
    settings: Settings = Depends(get_settings),
    actor_id: str | None = Depends(get_optional_actor_id),
):
    try:
        return actualizar_estado_pedido(gym_service, settings, id_pedido, payload.model_dump(), actor=actor_id)
    except (ValueError, RuntimeError, PermissionError) as error:
        raise _http_error(error) from error


@router.post("", dependencies=[Depends(require_admin_or_staff)])
# Actualiza el registro correspondiente.
def upsert_producto(
    payload: ProductoTiendaInput,
    gym_service: GymService = Depends(get_gym_service),
    actor_id: str | None = Depends(get_optional_actor_id),
):
    try:
        return gym_service.upsert_producto_tienda(payload.model_dump(), actor=actor_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        
@router.get("/imagenes")
# Obtiene los datos necesarios.
def list_producto_imagenes(images: StoreImagesService = Depends(get_store_images_service)):
    try:
        return images.list_images()
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.post("/imagenes", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_or_staff)])
async def upload_producto_imagen(file: UploadFile = File(...), images: StoreImagesService = Depends(get_store_images_service)):
    if not str(file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecciona un archivo de imagen")
    data = await file.read(MAX_IMAGE_BYTES + 1)
    try:
        return await run_in_threadpool(images.upload, file.filename, data, file.content_type)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.delete("/{id_producto}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_or_staff)])
# Elimina el registro indicado.
def delete_producto(id_producto: int, gym_service: GymService = Depends(get_gym_service)):
    gym_service.delete_producto_tienda(id_producto)
