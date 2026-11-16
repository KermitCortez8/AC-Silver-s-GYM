"""Oráculos de TC-81..91, TC-192 y TC-193 sobre operaciones reales aisladas."""
from copy import deepcopy

import pytest

from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


def article(api, **changes):
    response = api.client.post("/api/inventario", json={
        "nombre_item": "Mancuerna QA", "tipo": "Equipo", "cantidad_stock": 10,
        "stock_minimo": 3, "unidad_venta": "unidad", "precio_venta": 15,
        "ubicacion": "Almacén QA", "estado": "Disponible", **changes,
    })
    assert response.status_code == 200, response.text
    return response.json()


def movement(api, item, kind, quantity):
    return api.client.post("/api/inventario/movimientos", json={
        "id_item": item["id_item"], "id_usuario": "SGADM001", "tipo_movimiento": kind,
        "cantidad": quantity, "descripcion": "Movimiento QA documentado",
    })


def test_tc081_tc082_crea_y_consulta_todos_los_datos_sin_mutar_stock(documented_api):
    api = documented_api
    saved = article(api)
    before = business_state(api)
    [loaded] = api.client.get("/api/inventario").json()
    for field in ("id_item", "nombre_item", "tipo", "cantidad_stock", "stock_minimo", "precio_venta", "ubicacion", "estado", "unidad_venta"):
        assert loaded[field] == saved[field]
    assert loaded["cantidad_stock"] == 10
    assert business_state(api) == before


def test_tc083_editar_ubicacion_no_modifica_existencias_ni_movimientos(documented_api):
    api = documented_api
    saved = article(api)
    before = deepcopy(api.gym.state["mov_inv"])
    response = api.client.post("/api/inventario", json={**saved, "ubicacion": "Sala QA", "observaciones": "Revisado"})
    assert response.status_code == 200, response.text
    [loaded] = api.client.get("/api/inventario").json()
    assert loaded["ubicacion"] == "Sala QA"
    assert loaded["cantidad_stock"] == 10
    assert api.gym.state["mov_inv"] == before


def test_tc084_retirar_recurso_libre_no_afecta_otro(documented_api):
    api = documented_api
    target = article(api, cantidad_stock=0)
    control = article(api, nombre_item="Control QA", cantidad_stock=0)
    response = api.client.delete(f"/api/inventario/{target['id_item']}")
    assert response.status_code in (200, 204), response.text
    remaining = api.client.get("/api/inventario").json()
    assert not any(row["id_item"] == target["id_item"] for row in remaining)
    assert remaining == [control]


@pytest.mark.parametrize("field,value", [("cantidad_stock", -1), ("cantidad_stock", 1.5),
                                         ("precio_venta", -1), ("stock_minimo", -1)])
def test_tc085_datos_invalidos_no_crean_ni_modifican_recursos(documented_api, field, value):
    api = documented_api
    saved = article(api)
    before = business_state(api)
    response = api.client.post("/api/inventario", json={**saved, field: value})
    assert response.status_code in (400, 422)
    assert business_state(api) == before


def test_tc086_historial_se_conserva_al_retirar_articulo(documented_api):
    api = documented_api
    saved = article(api)
    history = deepcopy(api.gym.movimientos_inventario())
    response = api.client.delete(f"/api/inventario/{saved['id_item']}")
    assert response.status_code == 200, response.text
    assert api.gym.get_item_inventario(saved["id_item"])["estado"] == "Descontinuado"
    assert api.gym.movimientos_inventario() == history


@pytest.mark.parametrize("kind,quantity,expected", [("entrada", 5, 15), ("salida", 3, 7), ("ajuste", 8, 8)])
def test_tc087_tc088_tc089_movimientos_guardan_saldo_actor_y_motivo(documented_api, kind, quantity, expected):
    api = documented_api
    saved = article(api)
    before_count = len(api.gym.movimientos_inventario())
    response = movement(api, saved, kind, quantity)
    assert response.status_code == 200, response.text
    reloaded = api.gym.get_item_inventario(saved["id_item"])
    assert reloaded["cantidad_stock"] == expected
    history = api.gym.movimientos_inventario()
    assert len(history) == before_count + 1
    row = response.json()["movimiento"]
    assert (row["tipo_movimiento"], row["cantidad"], row["id_usuario"]) == (kind, quantity, "SGADM001")
    assert row["fecha_movimiento"] and row["descripcion"] == "Movimiento QA documentado"


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "1e2", True])
def test_tc090_movimiento_invalido_conserva_stock_e_historia(documented_api, quantity):
    api = documented_api
    saved = article(api)
    before = business_state(api)
    assert movement(api, saved, "entrada", quantity).status_code == 422
    assert business_state(api) == before


def test_tc091_salida_insuficiente_no_tiene_escrituras_parciales(documented_api):
    api = documented_api
    saved = article(api)
    before = business_state(api)
    response = movement(api, saved, "salida", 11)
    assert response.status_code == 400 and "Stock insuficiente" in response.text
    assert business_state(api) == before


def test_tc192_corregir_movimiento_recalcula_un_solo_registro(documented_api):
    api = documented_api
    saved = article(api)
    row = movement(api, saved, "entrada", 5).json()["movimiento"]
    count = len(api.gym.movimientos_inventario())
    endpoint = f"/api/inventario/movimientos/{row['id_mov']}"
    assert api.client.put(endpoint, json={"cantidad": 3}).status_code == 200
    assert api.gym.get_item_inventario(saved["id_item"])["cantidad_stock"] == 13
    assert api.client.put(endpoint, json={"tipo_movimiento": "salida", "cantidad": 2}).status_code == 200
    assert api.gym.get_item_inventario(saved["id_item"])["cantidad_stock"] == 8
    assert len(api.gym.movimientos_inventario()) == count
    before = business_state(api)
    response = api.client.put("/api/inventario/movimientos/999999", json={"cantidad": 2})
    assert response.status_code == 404, response.text
    assert business_state(api) == before


def test_tc193_estado_automatico_en_limites_y_descontinuado_manual(documented_api):
    api = documented_api
    saved = article(api, tipo="Tienda")
    assert api.gym.get_item_inventario(saved["id_item"])["estado"] == "Disponible"
    for kind, quantity, expected in [("salida", 7, "Stock bajo"), ("salida", 3, "Agotado"), ("entrada", 5, "Disponible")]:
        assert movement(api, saved, kind, quantity).status_code == 200
        assert api.gym.get_item_inventario(saved["id_item"])["estado"] == expected
    retired = article(api, nombre_item="Retirado QA", tipo="Tienda", estado="Descontinuado")
    assert movement(api, retired, "entrada", 5).status_code == 200
    assert api.gym.get_item_inventario(retired["id_item"])["estado"] == "Descontinuado"


@pytest.mark.parametrize("fails", [False, True])
def test_tc166_reposicion_10_y_2_se_guarda_completa_o_revierte(fails):
    from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
    from application.services.gym_service import GymService
    from tests.inventario.integracion.test_inventario_tienda_stock import FakeSupabase, _supabase_service, _reponer
    from tests.soporte.atomic_fake import seed_snapshot

    fake = FakeSupabase(fail_insert_on="MOV_INV" if fails else None)
    service = _supabase_service(fake)
    service.state["productos_tienda"][0]["cantidad_stock"] = 2
    seed_snapshot(service)
    before = deepcopy(fake.rows)
    if fails:
        with pytest.raises(RuntimeError):
            _reponer(service, service.state["inventario"][0]["id_item"], 4)
        assert fake.rows == before
        expected = (10, 2)
    else:
        result = _reponer(service, service.state["inventario"][0]["id_item"], 4)
        assert result["stock_tienda"] == 6
        assert fake.rows["INVENTARIO"][0]["Cantidad_Stock_E"] == 6
        assert fake.rows["TIENDA_PRODUCTOS"][0]["cantidad_stock"] == 6
        assert len(fake.rows["MOV_INV"]) == len(before["MOV_INV"]) + 1
        expected = (6, 6)
    # Nueva instancia del repositorio de prueba; el caso no certifica SQL real.
    reloaded = GymService(MemoryGymRepository(deepcopy(service.state)), service.passwords)
    assert (reloaded.inventario()[0]["cantidad_stock"], reloaded.productos_tienda()[0]["cantidad_stock"]) == expected
