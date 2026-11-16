"""TC-156: líneas de pedido; solo validación de contratos sin Stripe ni stock."""
from copy import deepcopy

from pydantic import ValidationError
import pytest

from domain.models.gym import PedidoTiendaItemInput, PedidoTiendaCheckoutInput


def test_tc156_linea_valida_cantidad_dos_y_rechazos_antes_de_comprar():
    payload = {"id_producto": 1, "cantidad": 2}
    original = deepcopy(payload)
    line = PedidoTiendaItemInput.model_validate(payload)
    assert line.id_producto == 1 and line.cantidad == 2
    for value in (0, -1, 1.5, "abc"):
        with pytest.raises(ValidationError):
            PedidoTiendaItemInput.model_validate({**payload, "cantidad": value})
    with pytest.raises(ValidationError):
        PedidoTiendaCheckoutInput(items=[])
    assert payload == original
