from __future__ import annotations

from typing import Any

import pytest

from domain.services.inventory_rules import codigo_unidad, es_categoria_por_unidad, prefijo_activo
from infrastructure.services.local_gym_service import LocalGymService
from tests.soporte.testiny_api import documented_api  # noqa: F401

ADMIN = "SGADM001"


def _service() -> LocalGymService:
    service = LocalGymService()
    service.state["usuario"] = [
        service._normalize_usuario_record({"id_usuario": ADMIN, "nombre": "Admin", "correo": "admin@gym.test", "rol": "admin"})
    ]
    return service


def _equipo(service: LocalGymService, nombre: str = "Maquina para correr", stock: int = 3, **extra: Any) -> dict[str, Any]:
    return service.upsert_inventario(
        {"nombre_item": nombre, "tipo": "Equipo cardiovascular", "cantidad_stock": stock, "estado": "Operativo",
         "ubicacion": "Sala de cardio", **extra},
        actor=ADMIN,
    )


def _unidades(service: LocalGymService, id_item: int, activas: bool = True) -> list[dict[str, Any]]:
    return [u for u in service.unidades_inventario()
            if u["id_item"] == id_item and (not activas or u["estado"] != "Dado de baja")]


def _movimiento(service: LocalGymService, id_item: int, tipo: str, **extra: Any) -> dict[str, Any]:
    return service.registrar_movimiento_inventario({"id_item": id_item, "id_usuario": ADMIN, "tipo_movimiento": tipo, **extra})


@pytest.mark.parametrize(("nombre", "esperado"), [
    ("Maquina para correr", "MC"),
    ("Máquina de remo", "MR"),
    ("Mancuerna hexagonal 5 kg par", "MH"),
    ("Colchoneta", "CO"),
    ("Ñandú", "NA"),
    ("123", "AC"),
])
def test_prefijo_usa_las_iniciales_de_las_palabras_significativas(nombre: str, esperado: str) -> None:
    assert prefijo_activo(nombre) == esperado


def test_solo_equipos_y_accesorios_se_controlan_por_unidad() -> None:
    assert es_categoria_por_unidad("Equipo de fuerza")
    assert es_categoria_por_unidad(" accesorio cardio ")
    assert not es_categoria_por_unidad("Tienda")
    assert not es_categoria_por_unidad("Limpieza")
    assert not es_categoria_por_unidad("General")
    assert codigo_unidad(1008, "MC", 15) == "1008-MC-015"


def test_alta_de_equipo_crea_una_unidad_por_stock_inicial() -> None:
    service = _service()
    item = _equipo(service, stock=3)

    unidades = _unidades(service, item["id_item"])
    assert [u["codigo"] for u in unidades] == [f"{item['n_activo']}-MC-00{n}" for n in (1, 2, 3)]
    assert {u["estado"] for u in unidades} == {"Operativo"}
    assert {u["ubicacion"] for u in unidades} == {"Sala de cardio"}
    assert service.get_item_inventario(item["id_item"])["cantidad_stock"] == 3
    # El saldo inicial sigue quedando como una sola entrada en Movimientos.
    movimientos = [m for m in service.movimientos_inventario() if m["id_item"] == item["id_item"]]
    assert [(m["tipo_movimiento"], m["cantidad"]) for m in movimientos] == [("entrada", 3)]


def test_articulos_que_no_son_equipo_no_tienen_unidades() -> None:
    service = _service()
    limpieza = service.upsert_inventario(
        {"nombre_item": "Desinfectante", "tipo": "Limpieza", "cantidad_stock": 5, "estado": "Operativo"}, actor=ADMIN
    )
    tienda = service.upsert_inventario(
        {"nombre_item": "Toalla", "tipo": "Tienda", "cantidad_stock": 5, "estado": "Disponible"}, actor=ADMIN
    )
    assert service.unidades_inventario() == []
    assert limpieza["prefijo_activo"] == "" and tienda["prefijo_activo"] == ""


def test_entrada_continua_el_correlativo() -> None:
    service = _service()
    item = _equipo(service, stock=2)

    _movimiento(service, item["id_item"], "entrada", cantidad=2)

    assert [u["correlativo"] for u in _unidades(service, item["id_item"])] == [1, 2, 3, 4]
    assert service.get_item_inventario(item["id_item"])["cantidad_stock"] == 4


def test_salida_da_de_baja_las_unidades_elegidas_y_conserva_su_historial() -> None:
    service = _service()
    item = _equipo(service, stock=3)
    segunda = _unidades(service, item["id_item"])[1]

    resultado = _movimiento(service, item["id_item"], "salida", cantidad=99, unidades=[segunda["id_unidad"]],
                            descripcion="Se rompió")

    assert resultado["movimiento"]["cantidad"] == 1
    assert resultado["movimiento"]["descripcion"] == f"Se rompió · Unidades: {segunda['codigo']}"
    baja = next(u for u in service.unidades_inventario() if u["id_unidad"] == segunda["id_unidad"])
    assert baja["estado"] == "Dado de baja" and baja["fecha_baja"]
    assert len(_unidades(service, item["id_item"])) == 2
    assert service.get_item_inventario(item["id_item"])["cantidad_stock"] == 2
    # Una nueva entrada no reutiliza el correlativo de la unidad dada de baja.
    _movimiento(service, item["id_item"], "entrada", cantidad=1)
    assert max(u["correlativo"] for u in _unidades(service, item["id_item"])) == 4


@pytest.mark.parametrize(("unidades", "mensaje"), [
    (None, "Elige las unidades"),
    ([], "Elige las unidades"),
    ("repetida", "repetida"),
    ("ajena", "no está activa"),
])
def test_salida_rechaza_unidades_invalidas(unidades: Any, mensaje: str) -> None:
    service = _service()
    item = _equipo(service, stock=2)
    otro = _equipo(service, nombre="Bicicleta estatica", stock=1)
    propia = _unidades(service, item["id_item"])[0]["id_unidad"]
    if unidades == "repetida":
        unidades = [propia, propia]
    elif unidades == "ajena":
        unidades = [_unidades(service, otro["id_item"])[0]["id_unidad"]]

    with pytest.raises(ValueError, match=mensaje):
        _movimiento(service, item["id_item"], "salida", unidades=unidades)
    assert len(_unidades(service, item["id_item"])) == 2


def test_equipos_con_unidades_no_admiten_ajustes_ni_cambios_de_cantidad() -> None:
    service = _service()
    item = _equipo(service, stock=2)

    with pytest.raises(ValueError, match="no admiten ajustes"):
        _movimiento(service, item["id_item"], "ajuste", cantidad=5)

    entrada = _movimiento(service, item["id_item"], "entrada", cantidad=1)["movimiento"]
    with pytest.raises(ValueError, match="solo permiten cambiar la fecha"):
        service.actualizar_movimiento_inventario(entrada["id_mov"], {"cantidad": 4})
    corregido = service.actualizar_movimiento_inventario(entrada["id_mov"], {"descripcion": "Compra noviembre"})
    assert corregido["movimiento"]["descripcion"] == "Compra noviembre"


def test_estado_del_articulo_resume_el_de_sus_unidades() -> None:
    service = _service()
    item = _equipo(service, stock=2)
    primera, segunda = _unidades(service, item["id_item"])

    service.actualizar_unidad_inventario(primera["id_unidad"], {"estado": "En mantenimiento", "ubicacion": "Taller"})
    assert service.get_item_inventario(item["id_item"])["estado"] == "Operativo"

    service.actualizar_unidad_inventario(segunda["id_unidad"], {"estado": "Fuera de servicio"})
    assert service.get_item_inventario(item["id_item"])["estado"] == "En mantenimiento"

    service.dar_de_baja_unidad_inventario(primera["id_unidad"], {"id_usuario": ADMIN, "motivo": "Sin reparación"})
    service.dar_de_baja_unidad_inventario(segunda["id_unidad"], {"id_usuario": ADMIN})
    articulo = service.get_item_inventario(item["id_item"])
    assert (articulo["cantidad_stock"], articulo["estado"]) == (0, "Agotado")


def test_editar_unidad_valida_estado_y_bajas() -> None:
    service = _service()
    item = _equipo(service, stock=1)
    unidad = _unidades(service, item["id_item"])[0]

    with pytest.raises(ValueError, match="Dar de baja"):
        service.actualizar_unidad_inventario(unidad["id_unidad"], {"estado": "Dado de baja"})
    editada = service.actualizar_unidad_inventario(unidad["id_unidad"], {"observaciones": "Banda nueva"})
    assert editada["observaciones"] == "Banda nueva"

    service.dar_de_baja_unidad_inventario(unidad["id_unidad"], {"id_usuario": ADMIN})
    with pytest.raises(ValueError, match="dada de baja"):
        service.actualizar_unidad_inventario(unidad["id_unidad"], {"estado": "Operativo"})


def test_renombrar_no_cambia_el_prefijo_ni_los_codigos() -> None:
    service = _service()
    item = _equipo(service, stock=1)
    codigo = _unidades(service, item["id_item"])[0]["codigo"]

    service.upsert_inventario({**service.get_item_inventario(item["id_item"]), "nombre_item": "Trotadora"}, actor=ADMIN)

    assert service.get_item_inventario(item["id_item"])["prefijo_activo"] == "MC"
    assert _unidades(service, item["id_item"])[0]["codigo"] == codigo


def test_articulo_que_pasa_a_equipo_recibe_codigos_para_su_stock() -> None:
    service = _service()
    item = service.upsert_inventario(
        {"nombre_item": "Banco plano", "tipo": "General", "cantidad_stock": 2, "estado": "Operativo"}, actor=ADMIN
    )
    assert service.unidades_inventario() == []

    service.upsert_inventario({**service.get_item_inventario(item["id_item"]), "tipo": "Equipo de fuerza"}, actor=ADMIN)

    assert [u["codigo"] for u in _unidades(service, item["id_item"])] == [
        f"{item['n_activo']}-BP-001", f"{item['n_activo']}-BP-002"]
    assert service.get_item_inventario(item["id_item"])["cantidad_stock"] == 2


def test_altas_y_entradas_anotan_en_mov_inv_los_codigos_creados() -> None:
    service = _service()
    item = _equipo(service, stock=3)
    alta = next(m for m in service.movimientos_inventario() if m["id_item"] == item["id_item"])
    n = item["n_activo"]
    assert alta["descripcion"] == f"Alta de ítem: saldo inicial · Unidades: {n}-MC-001 a {n}-MC-003"

    service.registrar_movimiento_inventario({
        "id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": 1, "descripcion": "Compra",
    })
    entrada = max(service.movimientos_inventario(), key=lambda m: m["id_mov"])
    assert entrada["descripcion"] == f"Compra · Unidad: {n}-MC-004"


def test_operar_desde_tienda_no_borra_el_stock_de_los_equipos(documented_api) -> None:
    # Las operaciones de Tienda no cargan INVENTARIO_UNIDADES; no deben dejar los equipos en 0.
    api = documented_api
    equipo = api.client.post("/api/inventario", json={"nombre_item": "Banco plano", "tipo": "Equipo de fuerza", "cantidad_stock": 4}).json()
    respuesta = api.client.post("/api/tienda", json={"nombre_producto": "Agua", "precio_venta": 2, "cantidad_stock": 3})
    assert respuesta.status_code == 200, respuesta.text
    recargado = api.gym.get_item_inventario(equipo["id_item"])
    assert (recargado["cantidad_stock"], recargado["estado"]) == (4, "Operativo")
