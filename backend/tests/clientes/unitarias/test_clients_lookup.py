"""Mantiene la prioridad de identidad y los fallbacks al consultar una sola lista."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from application.services.clients_service import ClientsService


@pytest.mark.parametrize("identity,expected_id", [
    ({"id_cliente": 1, "email": "dos@example.com", "dni": "33333333"}, 1),
    ({"id_cliente": 99, "email": " DOS@example.com ", "dni": "33333333"}, 2),
    ({"id_cliente": 99, "email": "missing@example.com", "dni": " 33333333 "}, 3),
    ({"correo": "dos@example.com"}, 2),
])
def test_client_lookup_preserves_identity_priority(identity, expected_id):
    gym = Mock()
    gym.clientes_normalized.return_value = [
        {"id_cliente": 1, "correo": "uno@example.com", "dni": "11111111"},
        {"id_cliente": 2, "correo": "dos@example.com", "dni": "22222222"},
        {"id_cliente": 3, "correo": "tres@example.com", "dni": "33333333"},
    ]

    result = ClientsService(gym).get_client_for_user(SimpleNamespace(**identity))

    assert result["id_cliente"] == expected_id
    gym.clientes_normalized.assert_called_once_with()


@pytest.mark.parametrize("identity", [{}, {"id_cliente": 99, "email": "missing@example.com", "dni": "99999999"}])
def test_client_lookup_does_not_return_an_unrelated_client(identity):
    gym = Mock()
    gym.clientes_normalized.return_value = [{"id_cliente": 1, "correo": "uno@example.com", "dni": "11111111"}]

    with pytest.raises(ValueError, match="Cliente no encontrado"):
        ClientsService(gym).get_client_for_user(SimpleNamespace(**identity))
