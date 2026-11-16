"""TC-128: una referencia distinta no reemplaza un pago confirmado."""
from copy import deepcopy

import pytest

from application.services.clients_service import ClientsService
from tests.notificaciones.integracion.test_testiny_avisos import paid_membership


def test_tc128_referencia_incompatible_no_reemplaza_pago_ni_extiende_fechas():
    gym, paid, _plan = paid_membership()
    before = deepcopy(gym.state)
    member = paid["membresia"]
    with pytest.raises(ValueError, match="otro pago confirmado"):
        ClientsService(gym).confirm_public_payment(paid["cliente"]["id_cliente"], {
            "id_membresia": member["id_membresia"], "monto_pago": member["monto_pago"],
            "metodo_pago": "stripe", "referencia_pago": "otra-referencia-qa"})
    assert gym.state == before
