from __future__ import annotations

from copy import deepcopy
import threading
import time
from typing import Any

import pytest

from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService

ADMIN = "SGADM001"


def _service() -> LocalGymService:
    service = LocalGymService()
    service.state["usuario"] = [
        service._normalize_usuario_record({"id_usuario": ADMIN, "nombre": "Admin", "correo": "admin@gym.test", "rol": "admin"})
    ]
    return service


def _nuevo_item_tienda(service: LocalGymService, nombre: str = "Toalla", stock: int = 10) -> dict[str, Any]:
    return service.upsert_inventario(
        {"nombre_item": nombre, "tipo": "Tienda", "cantidad_stock": stock, "estado": "Disponible"},
        actor=ADMIN,
    )


def _producto_de(service: LocalGymService, id_item: int) -> dict[str, Any]:
    return next(p for p in service.productos_tienda() if p["id_item"] == id_item)


def _publicar(service: LocalGymService, id_item: int, precio: float = 25.0) -> dict[str, Any]:
    producto = _producto_de(service, id_item)
    return service.upsert_producto_tienda({**producto, "precio_venta": precio, "categoria": "Accesorios"}, actor=ADMIN)


def _vender(service: LocalGymService, id_producto: int, cantidad: int) -> dict[str, Any]:
    return service.crear_pedido_tienda(
        {"cliente_nombre": "Ana", "items": [{"id_producto": id_producto, "cantidad": cantidad}]}
    )


def _stock(service: LocalGymService, id_item: int) -> int:
    item = service.get_item_inventario(id_item)
    assert item is not None
    return item["cantidad_stock"]


def test_alta_de_item_tienda_registra_entrada_y_crea_producto_oculto() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)

    assert _stock(service, item["id_item"]) == 10
    [mov] = service.movimientos_inventario()
    assert (mov["tipo_movimiento"], mov["cantidad"], mov["id_usuario"]) == ("entrada", 10, ADMIN)

    producto = _producto_de(service, item["id_item"])
    assert producto["cantidad_stock"] == 10
    assert producto["estado"] == "Descatalogado"  # sin precio todavía no se vende


def test_producto_con_precio_se_publica_con_el_stock_del_inventario() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)

    producto = _publicar(service, item["id_item"])

    assert producto["estado"] == "Disponible"
    assert producto["cantidad_stock"] == 10


def test_venta_descuenta_stock_compartido_y_registra_salida() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])

    pedido = _vender(service, producto["id_producto"], 3)

    assert _stock(service, item["id_item"]) == 7
    assert _producto_de(service, item["id_item"])["cantidad_stock"] == 7
    salida = service.movimientos_inventario()[0]
    assert salida["tipo_movimiento"] == "salida"
    assert salida["cantidad"] == 3
    assert salida["descripcion"].startswith(f"Venta pedido #{pedido['id_pedido']}")
    assert salida["id_usuario"] is None


def test_venta_sin_stock_suficiente_no_cambia_nada() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=5)
    producto = _publicar(service, item["id_item"])
    antes = deepcopy(service.state)

    with pytest.raises(ValueError, match="Stock insuficiente"):
        # Dos líneas del mismo producto suman 6 > 5.
        service.crear_pedido_tienda(
            {"items": [{"id_producto": producto["id_producto"], "cantidad": 3}, {"id_producto": producto["id_producto"], "cantidad": 3}]}
        )

    assert service.state["inventario"] == antes["inventario"]
    assert service.state["mov_inv"] == antes["mov_inv"]
    assert service.state["pedidos_tienda"] == []


def test_cancelar_pedido_pendiente_devuelve_stock_como_entrada() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    pedido = _vender(service, producto["id_producto"], 4)

    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO"}, actor=ADMIN)

    assert _stock(service, item["id_item"]) == 10
    devolucion = service.movimientos_inventario()[0]
    assert (devolucion["tipo_movimiento"], devolucion["cantidad"]) == ("entrada", 4)
    assert devolucion["descripcion"] == f"Devolución por cancelación del pedido #{pedido['id_pedido']}"
    assert devolucion["id_usuario"] == ADMIN

    # Guardar de nuevo el pedido cancelado no devuelve stock dos veces.
    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO", "observacion_admin": "nota"})
    assert _stock(service, item["id_item"]) == 10


def test_cancelar_pedido_anterior_al_enlace_no_infla_el_inventario() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    # Pedido registrado antes de enlazar: descontó el stock propio de la tienda, no el de INVENTARIO.
    service.state["pedidos_tienda"] = [
        {"id_pedido": 1, "estado_pedido": "PENDIENTE", "items": [{"id_producto": producto["id_producto"], "cantidad": 2}]}
    ]
    _vender(service, producto["id_producto"], 1)  # pedido #2, ya con salida en MOV_INV

    service.actualizar_pedido_tienda(1, {"estado_pedido": "CANCELADO"})

    assert _stock(service, item["id_item"]) == 9
    assert not any(m["descripcion"].startswith("Devolución") for m in service.movimientos_inventario())


def test_solo_se_cancelan_pedidos_pendientes_y_cancelado_es_final() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    confirmado = _vender(service, producto["id_producto"], 1)
    service.actualizar_pedido_tienda(confirmado["id_pedido"], {"estado_pedido": "CONFIRMADO"})

    with pytest.raises(ValueError, match="PENDIENTE"):
        service.actualizar_pedido_tienda(confirmado["id_pedido"], {"estado_pedido": "CANCELADO"})
    assert _stock(service, item["id_item"]) == 9

    cancelado = _vender(service, producto["id_producto"], 1)
    service.actualizar_pedido_tienda(cancelado["id_pedido"], {"estado_pedido": "CANCELADO"})
    with pytest.raises(ValueError, match="cancelado"):
        service.actualizar_pedido_tienda(cancelado["id_pedido"], {"estado_pedido": "PENDIENTE"})


def test_editar_item_no_modifica_el_stock() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)

    service.upsert_inventario({**item, "nombre_item": "Toalla grande", "cantidad_stock": 99}, actor=ADMIN)

    assert _stock(service, item["id_item"]) == 10
    assert len(service.movimientos_inventario()) == 1


def test_producto_nuevo_desde_tienda_crea_su_item_en_inventario() -> None:
    service = _service()

    producto = service.upsert_producto_tienda(
        {"nombre_producto": "Barra proteica", "categoria": "Snacks", "precio_venta": 3.9, "cantidad_stock": 48},
        actor=ADMIN,
    )

    item = service.get_item_inventario(producto["id_item"])
    assert item is not None
    assert (item["tipo"], item["cantidad_stock"]) == ("Tienda", 48)
    assert producto["categoria"] == "Snacks"
    assert producto["estado"] == "Disponible"
    [mov] = service.movimientos_inventario()
    assert (mov["tipo_movimiento"], mov["cantidad"], mov["id_item"]) == ("entrada", 48, item["id_item"])


def test_solo_items_tienda_y_un_producto_por_item() -> None:
    service = _service()
    equipo = service.upsert_inventario({"nombre_item": "Mancuerna", "tipo": "Equipo de fuerza", "cantidad_stock": 4})
    item = _nuevo_item_tienda(service)

    with pytest.raises(ValueError, match="Tipo 'Tienda'"):
        service.upsert_producto_tienda({"nombre_producto": "Mancuerna", "precio_venta": 10, "id_item": equipo["id_item"]})
    with pytest.raises(ValueError, match="ya está vinculado"):
        service.upsert_producto_tienda({"nombre_producto": "Otra toalla", "precio_venta": 10, "id_item": item["id_item"]})


def test_item_que_deja_de_ser_tienda_se_oculta() -> None:
    service = _service()
    item = _nuevo_item_tienda(service)
    _publicar(service, item["id_item"])

    service.upsert_inventario({**item, "tipo": "Accesorio entrenamiento"})

    assert _producto_de(service, item["id_item"])["estado"] == "Descatalogado"


def test_borrar_item_con_historial_lo_descontinua() -> None:
    service = _service()
    item = _nuevo_item_tienda(service)
    _publicar(service, item["id_item"])

    resultado = service.delete_inventario(item["id_item"])

    assert resultado is not None and resultado["estado"] == "Descontinuado"
    assert service.get_item_inventario(item["id_item"]) is not None
    assert len(service.movimientos_inventario()) == 1
    assert _producto_de(service, item["id_item"])["estado"] == "Descatalogado"


def test_borrar_item_sin_historial_lo_elimina() -> None:
    service = _service()
    item = service.upsert_inventario({"nombre_item": "Banca", "tipo": "Equipo de fuerza", "cantidad_stock": 0})

    assert service.delete_inventario(item["id_item"]) is None
    assert service.get_item_inventario(item["id_item"]) is None


def test_editar_entrada_recalcula_stock_por_la_diferencia() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    entrada = service.movimientos_inventario()[0]

    service.actualizar_movimiento_inventario(entrada["id_mov"], {"cantidad": 12, "descripcion": "Compra corregida"})
    assert _stock(service, item["id_item"]) == 12
    assert _producto_de(service, item["id_item"])["cantidad_stock"] == 12

    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 5})
    manual = service.movimientos_inventario()[0]
    service.actualizar_movimiento_inventario(manual["id_mov"], {"tipo_movimiento": "salida", "cantidad": 2})
    assert _stock(service, item["id_item"]) == 10  # 12 + 5 -> se revierte la entrada y se aplica la salida


def test_editar_movimiento_no_deja_stock_negativo() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=3)
    entrada = service.movimientos_inventario()[0]

    with pytest.raises(ValueError, match="stock negativo"):
        service.actualizar_movimiento_inventario(entrada["id_mov"], {"tipo_movimiento": "salida", "cantidad": 1})
    assert _stock(service, item["id_item"]) == 3


def test_editar_movimiento_puede_cambiar_de_item() -> None:
    service = _service()
    toalla = _nuevo_item_tienda(service, "Toalla", stock=5)
    shaker = _nuevo_item_tienda(service, "Shaker", stock=0)
    service.registrar_movimiento_inventario({"id_item": toalla["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 4})
    mov = service.movimientos_inventario()[0]

    service.actualizar_movimiento_inventario(mov["id_mov"], {"id_item": shaker["id_item"]})

    assert _stock(service, toalla["id_item"]) == 5
    assert _stock(service, shaker["id_item"]) == 4


def test_movimientos_de_pedido_solo_editan_fecha_y_descripcion() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    pedido = _vender(service, producto["id_producto"], 2)
    salida = service.movimientos_inventario()[0]

    with pytest.raises(ValueError, match="fecha y la descripción"):
        service.actualizar_movimiento_inventario(salida["id_mov"], {"cantidad": 5})

    resultado = service.actualizar_movimiento_inventario(salida["id_mov"], {"descripcion": "Entregado en recepcion", "fecha_movimiento": "2026-09-20"})
    assert resultado["movimiento"]["descripcion"] == f"Venta pedido #{pedido['id_pedido']} - Entregado en recepcion"
    assert resultado["movimiento"]["fecha_movimiento"] == "2026-09-20"
    assert _stock(service, item["id_item"]) == 8


def test_ajuste_solo_se_corrige_si_es_el_ultimo_movimiento() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "ajuste", "cantidad": 7})
    ajuste = service.movimientos_inventario()[0]

    service.actualizar_movimiento_inventario(ajuste["id_mov"], {"cantidad": 6})
    assert _stock(service, item["id_item"]) == 6

    with pytest.raises(ValueError, match="otro ajuste"):
        service.actualizar_movimiento_inventario(ajuste["id_mov"], {"tipo_movimiento": "entrada"})

    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 1})
    with pytest.raises(ValueError, match="último movimiento"):
        service.actualizar_movimiento_inventario(ajuste["id_mov"], {"cantidad": 9})
    assert _stock(service, item["id_item"]) == 7


def test_producto_sin_vincular_mantiene_su_stock_hasta_la_migracion() -> None:
    service = _service()
    service.state["productos_tienda"] = [
        {"id_producto": 1, "id_item": None, "nombre_producto": "Antiguo", "precio_venta": 5.0, "cantidad_stock": 4, "stock_minimo": 1}
    ]

    _vender(service, 1, 2)

    assert service.productos_tienda()[0]["cantidad_stock"] == 2
    assert service.movimientos_inventario() == []


# --- Sincronización con Supabase -------------------------------------------------


class FakeSupabase:
    def __init__(self, fail_insert_on: str | None = None) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.fail_insert_on = fail_insert_on

    def insert(self, table: str, body: Any, return_representation: bool = False) -> Any:
        if table == self.fail_insert_on:
            raise RuntimeError(f"Supabase POST {table} fallo")
        self.calls.append(("insert", table, body))

    def update(self, table: str, pk_column: str, pk_value: Any, body: dict[str, Any]) -> None:
        self.calls.append(("update", table, (pk_value, body)))

    def delete(self, table: str, pk_column: str, pk_value: Any) -> None:
        self.calls.append(("delete", table, pk_value))

    def delete_where(self, table: str, column: str, value: Any) -> None:
        self.calls.append(("delete_where", table, value))


def _supabase_service(fake: FakeSupabase) -> SupabaseGymService:
    local = _service()
    item = _nuevo_item_tienda(local, stock=10)
    _publicar(local, item["id_item"])

    service = object.__new__(SupabaseGymService)
    service.supabase = fake  # type: ignore[assignment]
    service.lock = threading.Lock()
    service.remote_columns = {}
    service.missing_remote_tables = set()
    service.state = deepcopy(local.state)
    service._last_refresh_at = time.monotonic() + 3600
    return service


def test_mapeo_remoto_guarda_vinculo_con_inventario() -> None:
    service = object.__new__(SupabaseGymService)

    assert service._product_to_remote({"id_producto": 1, "id_item": 8})["id_item"] == 8
    assert service._map_product({"id_producto": 1, "id_item": 8})["id_item"] == 8
    assert service._map_product({"id_producto": 1, "id_item": None})["id_item"] is None


def test_venta_guarda_stock_compartido_y_salida() -> None:
    fake = FakeSupabase()
    service = _supabase_service(fake)
    producto = service.state["productos_tienda"][0]

    _vender(service, producto["id_producto"], 2)  # type: ignore[arg-type]

    insertadas = {table: body for kind, table, body in fake.calls if kind == "insert"}
    assert insertadas["MOV_INV"]["tipo_movimiento"] == "salida"
    assert insertadas["MOV_INV"]["id_usuario"] is None
    actualizaciones = {table: body for kind, table, (_, body) in [c for c in fake.calls if c[0] == "update"]}
    assert actualizaciones["INVENTARIO"]["Cantidad_Stock_E"] == 8
    assert actualizaciones["TIENDA_PRODUCTOS"]["cantidad_stock"] == 8


def test_fallo_de_supabase_revierte_stock_remoto_y_local() -> None:
    fake = FakeSupabase(fail_insert_on="MOV_INV")
    service = _supabase_service(fake)
    producto = service.state["productos_tienda"][0]
    antes = deepcopy(service.state["inventario"])

    with pytest.raises(RuntimeError):
        _vender(service, producto["id_producto"], 2)  # type: ignore[arg-type]

    assert service.state["inventario"] == antes
    restaurado = [body for kind, table, (_, body) in [c for c in fake.calls if c[0] == "update"] if table == "INVENTARIO"]
    assert restaurado[-1]["Cantidad_Stock_E"] == 10
    # MOV_INV se guarda antes que VENTAS: si falla, la venta nunca llega a Supabase.
    assert not any(kind == "insert" and table == "VENTAS" for kind, table, _ in fake.calls)


def test_ajustar_precio_desde_inventario_actualiza_la_tienda() -> None:
    service = _service()
    item = _nuevo_item_tienda(service)
    producto = _publicar(service, item["id_item"])
    service.upsert_inventario({**item, "precio_venta": 40.50})
    assert _producto_de(service, item["id_item"])["precio_venta"] == 40.50
    pedido = _vender(service, producto["id_producto"], 2)
    assert pedido["items"][0]["precio_unitario"] == 40.50


def test_editar_item_sin_enviar_precio_conserva_el_precio_publicado() -> None:
    service = _service()
    item = _nuevo_item_tienda(service)
    _publicar(service, item["id_item"])
    payload = {**item, "nombre_item": "Toalla deportiva"}
    payload.pop("precio_venta")
    service.upsert_inventario(payload)
    assert _producto_de(service, item["id_item"])["precio_venta"] == 25.0
    assert _producto_de(service, item["id_item"])["estado"] == "Disponible"
    service.upsert_inventario({**payload, "precio_venta": None})
    assert service.get_item_inventario(item["id_item"])["precio_venta"] == 25.0


def test_precio_cero_explicito_oculta_producto() -> None:
    service = _service()
    item = _nuevo_item_tienda(service)
    _publicar(service, item["id_item"])
    service.upsert_inventario({**item, "precio_venta": 0})
    assert _producto_de(service, item["id_item"])["estado"] == "Descatalogado"


def test_precio_desde_inventario_se_guarda_en_supabase_y_se_recupera() -> None:
    fake = FakeSupabase()
    service = _supabase_service(fake)
    item = service.state["inventario"][0]
    service.upsert_inventario({**item, "precio_venta": 40.50})
    updates = [body for kind, table, (_, body) in [c for c in fake.calls if c[0] == "update"] if table == "TIENDA_PRODUCTOS"]
    assert updates[-1]["precio_Venta"] == 40.50
    state = {
        "inventario": [service._map_inventory(service._inventory_to_remote(item))],
        "productos_tienda": [service._map_product(updates[-1])],
    }
    service._restaurar_precios_inventario(state)
    assert state["inventario"][0]["precio_venta"] == 40.50
