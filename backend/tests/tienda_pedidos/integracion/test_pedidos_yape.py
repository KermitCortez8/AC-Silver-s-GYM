"""Batería Y: pago con Yape por QR que confirma el recepcionista."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from application.services.store_checkout_service import procesar_pedidos_pendientes
from infrastructure.services.local_gym_service import LocalGymService
from tests.soporte.testiny_api import documented_api  # noqa: F401

ADMIN = "SGADM001"


def _service() -> LocalGymService:
    service = LocalGymService()
    service.state["usuario"] = [
        service._normalize_usuario_record({"id_usuario": ADMIN, "nombre": "Admin", "correo": "admin@gym.test", "rol": "admin"})
    ]
    return service


def _producto(service: LocalGymService, stock: int = 5) -> dict[str, Any]:
    return service.upsert_producto_tienda({"nombre_producto": "Agua", "precio_venta": 2, "cantidad_stock": stock})


def _comprar(service: LocalGymService, producto: dict[str, Any], metodo: str, cantidad: int = 2, **extra: Any) -> dict[str, Any]:
    return service.crear_pedido_tienda({"cliente_nombre": "Ana", "metodo_pago": metodo,
                                        "items": [{"id_producto": producto["id_producto"], "cantidad": cantidad}], **extra})


def _stock(service: LocalGymService, producto: dict[str, Any]) -> int:
    return service.get_producto_tienda(producto["id_producto"])["cantidad_stock"]


@pytest.mark.parametrize("metodo", ["yape", "Yape"])
def test_y01_compra_con_yape_queda_pendiente_y_reserva_stock(metodo) -> None:
    service = _service()
    producto = _producto(service, stock=5)
    pedido = _comprar(service, producto, metodo)
    assert (pedido["metodo_pago"], pedido["estado_pago"], pedido["estado_pedido"]) == ("yape", "PENDIENTE", "PENDIENTE")
    assert pedido["referencia_pago"] == ""
    assert _stock(service, producto) == 3


@pytest.mark.parametrize("metodo", ["plin", "transferencia"])
def test_y02_plin_y_transferencia_siguen_pagados_y_confirmados(metodo) -> None:
    service = _service()
    pedido = _comprar(service, _producto(service), metodo, referencia_pago="OP-1")
    assert (pedido["estado_pago"], pedido["estado_pedido"]) == ("PAGADO", "CONFIRMADO")


def test_y03_recepcion_confirma_el_yape_y_queda_pagado() -> None:
    service = _service()
    producto = _producto(service)
    pedido = _comprar(service, producto, "yape", referencia_pago="12345678")
    assert pedido["referencia_pago"] == "12345678"
    confirmado = service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CONFIRMADO", "observacion_admin": "Yape verificado"})
    assert (confirmado["estado_pago"], confirmado["estado_pedido"]) == ("PAGADO", "CONFIRMADO")
    entregado = service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "ENTREGADO"})
    assert entregado["estado_pedido"] == "ENTREGADO"


def test_y04_no_se_entrega_un_yape_sin_confirmar() -> None:
    service = _service()
    pedido = _comprar(service, _producto(service), "yape")
    with pytest.raises(ValueError, match="sin pago confirmado"):
        service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "ENTREGADO"})
    assert service.get_pedido_tienda(pedido["id_pedido"])["estado_pago"] == "PENDIENTE"


def test_y05_cancelar_un_yape_pendiente_devuelve_el_stock_una_vez() -> None:
    service = _service()
    producto = _producto(service, stock=5)
    pedido = _comprar(service, producto, "yape")
    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO"})
    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO"})
    assert service.get_pedido_tienda(pedido["id_pedido"])["estado_pedido"] == "CANCELADO"
    assert _stock(service, producto) == 5


def test_y06_la_conciliacion_de_stripe_no_cancela_los_yape() -> None:
    service = _service()
    producto = _producto(service, stock=10)
    yape = _comprar(service, producto, "yape")
    tarjeta = service.crear_pedido_tienda_pago_pendiente({"items": [{"id_producto": producto["id_producto"], "cantidad": 1}]})
    hace_rato = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    for pedido in service.state["pedidos_tienda"]:
        pedido["creado_en"] = hace_rato

    assert [p["id_pedido"] for p in service.pedidos_pago_pendiente()] == [tarjeta["id_pedido"]]
    procesar_pedidos_pendientes(service, SimpleNamespace(), SimpleNamespace())

    assert service.get_pedido_tienda(tarjeta["id_pedido"])["estado_pedido"] == "CANCELADO"
    assert service.get_pedido_tienda(yape["id_pedido"])["estado_pedido"] == "PENDIENTE"
    assert _stock(service, producto) == 8  # Solo volvió la unidad de la tarjeta.


def test_y07_el_cliente_no_puede_marcar_pagado_un_yape(documented_api) -> None:
    api = documented_api
    producto = api.client.post("/api/tienda", json={"nombre_producto": "Agua", "precio_venta": 2, "categoria": "Bebidas",
                                                    "cantidad_stock": 5}).json()
    api.login("user")
    respuesta = api.client.post("/api/tienda/pedidos", json={
        "id_cliente": 1, "cliente_nombre": "Cliente QA 1", "cliente_correo": "cliente1@example.com", "cliente_dni": "11111111",
        "metodo_pago": "Yape", "estado_pago": "PAGADO", "estado_pedido": "CONFIRMADO",
        "items": [{"id_producto": producto["id_producto"], "cantidad": 1}],
    })
    assert respuesta.status_code == 201, respuesta.text
    assert (respuesta.json()["estado_pago"], respuesta.json()["estado_pedido"]) == ("PENDIENTE", "PENDIENTE")
