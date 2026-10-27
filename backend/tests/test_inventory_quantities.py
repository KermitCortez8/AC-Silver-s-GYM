from copy import deepcopy

import pytest
from pydantic import ValidationError

from domain.models.gym import InventarioInput, MovimientoInventarioInput, MovimientoInventarioUpdateInput, ProductoTiendaInput
from tests.test_inventario_tienda_stock import ADMIN, _service, _nuevo_item_tienda


@pytest.mark.parametrize("value", ["", " ", -1, "+1", "1.5", 1.5, "1e2", "2E3", "12abc", "2\n", True, 2147483648])
def test_inventory_and_store_contracts_reject_malformed_quantities(value):
    for field in ("cantidad_stock", "stock_minimo"):
        with pytest.raises(ValidationError):
            InventarioInput.model_validate({"nombre_item": "Agua", "tipo": "Tienda", "cantidad_stock": 0, field: value})
        with pytest.raises(ValidationError):
            ProductoTiendaInput.model_validate({"nombre_producto": "Agua", "precio_venta": 2, field: value})
    for model, defaults in [
        (MovimientoInventarioInput, {"id_item": 1, "id_usuario": ADMIN, "tipo_movimiento": "entrada"}),
        (MovimientoInventarioUpdateInput, {}),
    ]:
        with pytest.raises(ValidationError):
            model.model_validate({**defaults, "cantidad": value})


def test_zero_stock_is_valid_and_zero_movement_is_rejected():
    item = InventarioInput(nombre_item="Agua", tipo="Tienda", cantidad_stock="0", stock_minimo="0")
    assert item.cantidad_stock == item.stock_minimo == 0
    assert MovimientoInventarioUpdateInput(cantidad="12").cantidad == 12
    with pytest.raises(ValidationError):
        MovimientoInventarioUpdateInput(cantidad=0)


@pytest.mark.parametrize("value", [0, -1, 1.5, "1e2", "", True, 2147483648])
def test_invalid_movements_do_not_change_stock_or_history(value):
    service = _service()
    item = _nuevo_item_tienda(service, stock=10)
    before = deepcopy(service.state)
    payload = {"id_item": item["id_item"], "id_usuario": ADMIN, "tipo_movimiento": "entrada", "cantidad": value}
    with pytest.raises(ValueError):
        service.registrar_movimiento_inventario(payload)
    assert service.state == before
    with pytest.raises(ValueError):
        service.actualizar_movimiento_inventario(service.movimientos_inventario()[0]["id_mov"], {"cantidad": value})
    assert service.state == before
