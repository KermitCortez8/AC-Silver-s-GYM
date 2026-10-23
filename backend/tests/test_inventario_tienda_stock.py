from __future__ import annotations

from copy import deepcopy
import threading
import time
from typing import Any

import pytest
from tests.atomic_fake import AtomicFakeMixin, seed_snapshot

from infrastructure.services.local_gym_service import LocalGymService
from infrastructure.services.supabase_gym_service import SupabaseGymService

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
    return service.upsert_producto_tienda({**producto, "precio_venta": precio, "categoria": "Accesorios"})


def _reponer(service: LocalGymService, id_item: int, cantidad: int) -> dict[str, Any]:
    return service.registrar_movimiento_inventario(
        {"id_item": id_item, "id_usuario": ADMIN, "tipo_movimiento": "salida", "cantidad": cantidad, "destino": "TIENDA"}
    )


def _vender(service: LocalGymService, id_producto: int, cantidad: int) -> dict[str, Any]:
    return service.crear_pedido_tienda(
        {"cliente_nombre": "Ana", "items": [{"id_producto": id_producto, "cantidad": cantidad}]}
    )


def _stock(service: LocalGymService, id_item: int) -> int:
    item = service.get_item_inventario(id_item)
    assert item is not None
    return item["cantidad_stock"]


def _stock_tienda(service: LocalGymService, id_item: int) -> int:
    return _producto_de(service, id_item)["cantidad_stock"]


def test_alta_de_item_tienda_registra_entrada_y_crea_producto_vacio() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)

    assert _stock(service, item["id_item"]) == 10
    [mov] = service.movimientos_inventario()
    assert (mov["tipo_movimiento"], mov["cantidad"], mov["id_usuario"], mov["destino"]) == ("entrada", 10, ADMIN, None)

    producto = _producto_de(service, item["id_item"])
    assert producto["cantidad_stock"] == 0  # la reserva no pasa sola a la tienda
    assert producto["estado"] == "Descatalogado"  # sin precio todavía no se vende


def test_reponer_tienda_pasa_unidades_de_la_reserva_al_producto() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    _publicar(service, item["id_item"])

    resultado = _reponer(service, item["id_item"], 4)

    assert _stock(service, item["id_item"]) == 6
    assert _stock_tienda(service, item["id_item"]) == 4
    assert resultado["stock_tienda"] == 4
    mov = resultado["movimiento"]
    assert (mov["tipo_movimiento"], mov["cantidad"], mov["destino"]) == ("salida", 4, "TIENDA")
    assert _producto_de(service, item["id_item"])["estado"] == "Disponible"


def test_reponer_sin_reserva_suficiente_no_cambia_nada() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=3)
    antes = deepcopy(service.state)

    with pytest.raises(ValueError, match="Stock insuficiente"):
        _reponer(service, item["id_item"], 5)

    assert service.state["inventario"] == antes["inventario"]
    assert service.state["productos_tienda"] == antes["productos_tienda"]
    assert service.state["mov_inv"] == antes["mov_inv"]


def test_reponer_exige_producto_enlazado() -> None:
    service = _service()
    equipo = service.upsert_inventario({"nombre_item": "Mancuerna", "tipo": "Equipo de fuerza", "cantidad_stock": 4})

    with pytest.raises(ValueError, match="producto de Tienda enlazado"):
        _reponer(service, equipo["id_item"], 1)
    assert _stock(service, equipo["id_item"]) == 4


def test_destino_solo_aplica_a_salidas() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)

    entrada = service.registrar_movimiento_inventario(
        {"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 2, "destino": "TIENDA"}
    )
    assert entrada["movimiento"]["destino"] is None
    assert _stock_tienda(service, item["id_item"]) == 0

    with pytest.raises(ValueError, match="Destino inválido"):
        service.registrar_movimiento_inventario(
            {"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "salida", "cantidad": 1, "destino": "VENTA"}
        )


def test_venta_solo_descuenta_el_stock_de_la_tienda() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    _reponer(service, item["id_item"], 5)
    movimientos = len(service.movimientos_inventario())

    _vender(service, producto["id_producto"], 3)

    assert _stock_tienda(service, item["id_item"]) == 2
    assert _stock(service, item["id_item"]) == 5
    assert len(service.movimientos_inventario()) == movimientos


def test_venta_sin_stock_suficiente_no_cambia_nada() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    _reponer(service, item["id_item"], 5)
    antes = deepcopy(service.state)

    with pytest.raises(ValueError, match="Stock insuficiente"):
        # Dos líneas del mismo producto suman 6 > 5.
        service.crear_pedido_tienda(
            {"items": [{"id_producto": producto["id_producto"], "cantidad": 3}, {"id_producto": producto["id_producto"], "cantidad": 3}]}
        )

    assert service.state["productos_tienda"] == antes["productos_tienda"]
    assert service.state["pedidos_tienda"] == []


def test_cancelar_pedido_pendiente_devuelve_stock_a_la_tienda() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    _reponer(service, item["id_item"], 6)
    pedido = _vender(service, producto["id_producto"], 4)
    movimientos = len(service.movimientos_inventario())

    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO"})

    assert _stock_tienda(service, item["id_item"]) == 6
    assert _stock(service, item["id_item"]) == 4
    assert len(service.movimientos_inventario()) == movimientos

    # Guardar de nuevo el pedido cancelado no devuelve stock dos veces.
    service.actualizar_pedido_tienda(pedido["id_pedido"], {"estado_pedido": "CANCELADO", "observacion_admin": "nota"})
    assert _stock_tienda(service, item["id_item"]) == 6


def test_solo_se_cancelan_pedidos_pendientes_y_cancelado_es_final() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    _reponer(service, item["id_item"], 10)
    confirmado = _vender(service, producto["id_producto"], 1)
    service.actualizar_pedido_tienda(confirmado["id_pedido"], {"estado_pedido": "CONFIRMADO"})

    with pytest.raises(ValueError, match="PENDIENTE"):
        service.actualizar_pedido_tienda(confirmado["id_pedido"], {"estado_pedido": "CANCELADO"})
    assert _stock_tienda(service, item["id_item"]) == 9

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


def test_producto_nuevo_desde_tienda_crea_su_reserva_vacia() -> None:
    service = _service()

    producto = service.upsert_producto_tienda(
        {"nombre_producto": "Barra proteica", "categoria": "Snacks", "precio_venta": 3.9, "cantidad_stock": 48}
    )

    item = service.get_item_inventario(producto["id_item"])
    assert item is not None
    assert (item["tipo"], item["cantidad_stock"]) == ("Tienda", 0)
    assert producto["cantidad_stock"] == 48
    assert producto["estado"] == "Disponible"
    assert service.movimientos_inventario() == []


def test_editar_producto_no_cambia_su_stock() -> None:
    service = _service()
    producto = service.upsert_producto_tienda({"nombre_producto": "Shaker", "precio_venta": 15, "cantidad_stock": 8})

    editado = service.upsert_producto_tienda({**producto, "precio_venta": 18, "cantidad_stock": 99})

    assert editado["cantidad_stock"] == 8
    assert editado["precio_venta"] == 18


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
    assert _stock_tienda(service, item["id_item"]) == 0

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


def test_editar_reposicion_corrige_ambos_stocks() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    mov = _reponer(service, item["id_item"], 4)["movimiento"]

    service.actualizar_movimiento_inventario(mov["id_mov"], {"cantidad": 6})
    assert (_stock(service, item["id_item"]), _stock_tienda(service, item["id_item"])) == (4, 6)

    _vender(service, producto["id_producto"], 5)  # en tienda queda 1
    with pytest.raises(ValueError, match="ya vendió"):
        service.actualizar_movimiento_inventario(mov["id_mov"], {"cantidad": 2})
    assert (_stock(service, item["id_item"]), _stock_tienda(service, item["id_item"])) == (4, 1)

    with pytest.raises(ValueError, match="ya vendió"):
        service.actualizar_movimiento_inventario(mov["id_mov"], {"destino": ""})

    # Quitar el destino: la salida sigue en INVENTARIO, pero esas unidades salen de la tienda.
    otra = _reponer(service, item["id_item"], 2)["movimiento"]
    service.actualizar_movimiento_inventario(otra["id_mov"], {"destino": ""})
    assert (_stock(service, item["id_item"]), _stock_tienda(service, item["id_item"])) == (2, 1)


def test_salida_normal_puede_convertirse_en_reposicion() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    _publicar(service, item["id_item"])
    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "salida", "cantidad": 3})
    mov = service.movimientos_inventario()[0]

    resultado = service.actualizar_movimiento_inventario(mov["id_mov"], {"destino": "TIENDA"})

    assert resultado["movimiento"]["destino"] == "TIENDA"
    assert (_stock(service, item["id_item"]), _stock_tienda(service, item["id_item"])) == (7, 3)


def test_movimientos_de_pedido_solo_editan_fecha_y_descripcion() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    # Movimiento registrado cuando el stock estaba compartido (la migración 014 le pone destino VENTA).
    service.state["mov_inv"].insert(
        0,
        {
            "id_mov": 50,
            "id_item": item["id_item"],
            "id_usuario": None,
            "tipo_movimiento": "salida",
            "fecha_movimiento": "2026-09-01",
            "descripcion": "Venta pedido #7 (Ana)",
            "cantidad": 2,
            "destino": "VENTA",
        },
    )

    with pytest.raises(ValueError, match="fecha y la descripción"):
        service.actualizar_movimiento_inventario(50, {"cantidad": 5})
    with pytest.raises(ValueError, match="fecha y la descripción"):
        service.actualizar_movimiento_inventario(50, {"destino": "TIENDA"})

    resultado = service.actualizar_movimiento_inventario(50, {"descripcion": "Entregado en recepcion", "fecha_movimiento": "2026-09-20"})
    assert resultado["movimiento"]["descripcion"] == "Venta pedido #7 - Entregado en recepcion"
    assert resultado["movimiento"]["fecha_movimiento"] == "2026-09-20"
    assert resultado["movimiento"]["destino"] == "VENTA"
    assert _stock(service, item["id_item"]) == 10


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


def test_producto_sin_vincular_vende_con_su_propio_stock() -> None:
    service = _service()
    service.state["productos_tienda"] = [
        {"id_producto": 1, "id_item": None, "nombre_producto": "Antiguo", "precio_venta": 5.0, "cantidad_stock": 4, "stock_minimo": 1}
    ]

    _vender(service, 1, 2)

    assert service.productos_tienda()[0]["cantidad_stock"] == 2
    assert service.movimientos_inventario() == []


# --- Sincronización con Supabase -------------------------------------------------


class FakeSupabase(AtomicFakeMixin):
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


def _supabase_service(fake: FakeSupabase, en_tienda: int = 0) -> SupabaseGymService:
    local = _service()
    item = _nuevo_item_tienda(local, stock=10)
    _publicar(local, item["id_item"])
    if en_tienda:
        _reponer(local, item["id_item"], en_tienda)

    service = object.__new__(SupabaseGymService)
    service.supabase = fake  # type: ignore[assignment]
    service.lock = threading.Lock()
    service.remote_columns = {}
    service.missing_remote_tables = set()
    service.state = deepcopy(local.state)
    service._last_refresh_at = time.monotonic() + 3600
    seed_snapshot(service)
    return service


def _actualizaciones(fake: FakeSupabase, tabla: str) -> list[dict[str, Any]]:
    return [call[2][1] for call in fake.calls if call[0] == "update" and call[1] == tabla]


def test_mapeo_remoto_guarda_vinculo_y_destino() -> None:
    service = object.__new__(SupabaseGymService)

    assert service._product_to_remote({"id_producto": 1, "id_item": 8})["id_item"] == 8
    assert service._map_product({"id_producto": 1, "id_item": 8})["id_item"] == 8
    assert service._map_product({"id_producto": 1, "id_item": None})["id_item"] is None
    assert service._inventory_move_to_remote({"id_mov": 1, "id_item": 2, "tipo_movimiento": "salida", "destino": "tienda"})["destino"] == "TIENDA"
    assert service._map_inventory_move({"id_mov": 1, "id_item": 2, "destino": None})["destino"] is None


def test_reposicion_guarda_inventario_tienda_y_movimiento() -> None:
    fake = FakeSupabase()
    service = _supabase_service(fake)
    item = service.state["inventario"][0]

    _reponer(service, item["id_item"], 3)  # type: ignore[arg-type]

    insertadas = {table: body for kind, table, body in fake.calls if kind == "insert"}
    assert (insertadas["MOV_INV"]["tipo_movimiento"], insertadas["MOV_INV"]["destino"]) == ("salida", "TIENDA")
    assert _actualizaciones(fake, "INVENTARIO")[-1]["Cantidad_Stock_E"] == 7
    assert _actualizaciones(fake, "TIENDA_PRODUCTOS")[-1]["cantidad_stock"] == 3


def test_venta_solo_actualiza_la_tienda_en_supabase() -> None:
    fake = FakeSupabase()
    service = _supabase_service(fake, en_tienda=5)
    producto = service.state["productos_tienda"][0]

    _vender(service, producto["id_producto"], 2)  # type: ignore[arg-type]

    assert _actualizaciones(fake, "TIENDA_PRODUCTOS")[-1]["cantidad_stock"] == 3
    assert not any(table == "INVENTARIO" and "Cantidad_Stock_E" in body for body, table in ((c[2][1], c[1]) for c in fake.calls if c[0] == "update"))
    assert not any(kind == "insert" and table == "MOV_INV" for kind, table, _ in fake.calls)


def test_fallo_de_supabase_revierte_la_reposicion() -> None:
    fake = FakeSupabase(fail_insert_on="MOV_INV")
    service = _supabase_service(fake)
    item = service.state["inventario"][0]
    antes = deepcopy({k: service.state[k] for k in ("inventario", "productos_tienda", "mov_inv")})

    with pytest.raises(RuntimeError):
        _reponer(service, item["id_item"], 3)  # type: ignore[arg-type]

    assert {k: service.state[k] for k in antes} == antes
    inventario = _actualizaciones(fake, "INVENTARIO")
    tienda = _actualizaciones(fake, "TIENDA_PRODUCTOS")
    if inventario:
        assert inventario[-1]["Cantidad_Stock_E"] == 10
    if tienda:
        assert tienda[-1]["cantidad_stock"] == 0


def _estado(service: LocalGymService, id_item: int) -> str:
    item = service.get_item_inventario(id_item)
    assert item is not None
    return item["estado"]


def test_estado_automatico_sigue_la_reserva_del_inventario() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])
    service.upsert_producto_tienda({**producto, "stock_minimo": 4})
    assert _estado(service, item["id_item"]) == "Disponible"

    _reponer(service, item["id_item"], 6)  # quedan 4 = minimo
    assert _estado(service, item["id_item"]) == "Stock bajo"

    _vender(service, producto["id_producto"], 6)  # vender en tienda no toca la reserva
    assert _estado(service, item["id_item"]) == "Stock bajo"

    _reponer(service, item["id_item"], 4)  # quedan 0
    assert _estado(service, item["id_item"]) == "Agotado"

    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 20})
    assert _estado(service, item["id_item"]) == "Disponible"


def test_cambiar_minimo_recalcula_estado() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    producto = _publicar(service, item["id_item"])

    service.upsert_producto_tienda({**producto, "stock_minimo": 12})

    assert _estado(service, item["id_item"]) == "Stock bajo"


def test_descontinuado_es_manual_y_se_respeta() -> None:
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    _publicar(service, item["id_item"])

    service.upsert_inventario({**service.get_item_inventario(item["id_item"]), "estado": "Descontinuado"})  # type: ignore[dict-item]
    service.registrar_movimiento_inventario({"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "salida", "cantidad": 10})
    assert _estado(service, item["id_item"]) == "Descontinuado"

    # Quitar la marca vuelve al estado calculado.
    service.upsert_inventario({**service.get_item_inventario(item["id_item"]), "estado": "Disponible"})  # type: ignore[dict-item]
    assert _estado(service, item["id_item"]) == "Agotado"


def test_equipo_del_gimnasio_conserva_su_estado_manual() -> None:
    service = _service()
    equipo = service.upsert_inventario({"nombre_item": "Banca", "tipo": "Equipo de fuerza", "cantidad_stock": 0, "estado": "En mantenimiento"})

    assert _estado(service, equipo["id_item"]) == "En mantenimiento"


def test_estados_calculados_se_guardan_en_supabase_al_leer() -> None:
    fake = FakeSupabase()
    service = _supabase_service(fake)
    item = service.state["inventario"][0]
    item["estado"] = "Stock bajo"
    rows = [{"id_item": item["id_item"], "Estado": "Disponible"}]

    service._guardar_estados_automaticos(rows, service.state)

    assert ("update", "INVENTARIO", (item["id_item"], {"Estado": "Stock bajo"})) in fake.calls
