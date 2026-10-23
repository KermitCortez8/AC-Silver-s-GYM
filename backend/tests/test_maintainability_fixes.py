"""Regresiones de contratos, consultas puras y errores de infraestructura."""
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest
from pydantic import ValidationError

from application.services.client_payments_service import ClientPaymentsService
from application.services.gym_service import GymService
from domain.errors import EntityNotFound, MembershipRequired
from domain.image_policy import validate_image
from domain.models.gym import (
    ClienteInput, UsuarioInput, PlanMembresiaInput, PromocionInput,
    InventarioInput, MembresiaInput, HorarioServicioInput,
)
from infrastructure.http_transport import RemoteServiceError, json_request
from infrastructure.repositories.enrollment_errors import raise_schedule_enrollment_error
from infrastructure.repositories.mappers import store, memberships
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from infrastructure.repositories.schema_policy import prepare_write
from infrastructure.authentication import PasswordService


@pytest.mark.parametrize('model,payload', [
    (ClienteInput, {'nombre': '', 'correo': 'a@example.com'}),
    (ClienteInput, {'nombre': 'Ana', 'correo': 'incorrecto'}),
    (UsuarioInput, {'nombre': 'Ana', 'correo': 'a@example.com', 'rol': 'staff', 'password': 'secret123'} | {'nombre': '  '}),
    (PlanMembresiaInput, {'nombre_plan': 'Plan', 'duracion': '30 dias', 'precio': -1}),
    (InventarioInput, {'nombre_item': 'Pesas', 'tipo': 'Equipo', 'cantidad_stock': -1}),
    (InventarioInput, {'nombre_item': 'Pesas', 'tipo': 'Equipo', 'cantidad_stock': 1, 'precio_venta': float('inf')}),
    (PromocionInput, {'nombre': 'Promo', 'valor_descuento': 101}),
    (PromocionInput, {'nombre': 'Promo', 'fecha_inicio': '2026-02-30'}),
    (PromocionInput, {'nombre': 'Promo', 'fecha_inicio': '2026-10-23', 'fecha_fin': '2026-10-22'}),
    (MembresiaInput, {'id_cliente': 1, 'id_pm': 1, 'fecha_inicio': '', 'fecha_fin': '2026-10-23'}),
    (HorarioServicioInput, {'servicio': 'fitness', 'id_rutina': 1, 'hora_inicio': '25:00'}),
    (HorarioServicioInput, {'servicio': 'fitness', 'id_rutina': 1, 'hora_inicio': '09:00', 'hora_fin': '08:00'}),
])
def test_invalid_inputs_are_rejected_before_running_commands(model, payload):
    with pytest.raises(ValidationError):
        model(**payload)


def test_zero_values_survive_database_mapping():
    assert store._sale_to_remote({'total': 0, 'subtotal': 99})['total_Venta'] == 0
    detail = store._sale_detail_to_remote(1, {'cantidad': 2, 'precio_unitario': 0, 'precio': 10, 'subtotal': 0})
    assert detail['Precio_Unitario'] == detail['Subtotal'] == 0
    assert memberships._membership_to_remote({'monto_pago': 0})['monto_pago'] == 0


def test_query_refresh_does_not_write_or_expose_mutable_state(monkeypatch):
    repo = MemoryGymRepository()
    gym = GymService(repo, PasswordService())
    repo.state['clientes'] = [{'id_cliente': 1, 'id_usuario': 'SGCLI001', 'nombre': 'Ana', 'estado': 'ACTIVO'}]
    repo.state['membresia'] = [{'id_membresia': 1, 'id_cliente': 1, 'estado': 'ACTIVO', 'estado_pago': 'PAGADO',
                               'fecha_inicio': '2026-01-01', 'fecha_fin': '2026-01-31'}]
    before = deepcopy(repo.state)
    monkeypatch.setattr('application.services.gym_service.domain_clock._today_iso', lambda: '2026-10-23')
    monkeypatch.setattr(repo, 'change', lambda *a, **k: pytest.fail('Una consulta intentó escribir'))
    gym.ensure_fresh()
    assert gym.get_cliente(1)['estado'] == 'VENCIDA'
    result = gym.membresias()
    result[0]['estado'] = 'ACTIVO'
    assert gym.membresias()[0]['estado'] == 'VENCIDA'
    assert repo.state == before


def test_unknown_columns_are_not_silently_discarded():
    with pytest.raises(RuntimeError, match='observacion_nueva'):
        prepare_write('VENTAS', {'id_venta': 1, 'observacion_nueva': 'dato'}, {'VENTAS': {'id_venta'}}, lambda *_: None)


def test_google_schema_check_preserves_connection_failures():
    error = RemoteServiceError('Supabase', 403, {'code': '42501', 'message': 'denied'})
    def denied(*_):
        raise error
    with pytest.raises(RemoteServiceError) as raised:
        prepare_write('USUARIO', {'google_sub': 'subject'}, {}, denied)
    assert raised.value is error


def test_shared_transport_keeps_database_codes_and_causes():
    def opener(request, timeout):
        assert request.get_header('Authorization') == 'Bearer test'
        raise HTTPError(request.full_url, 409, 'Conflict', {}, BytesIO(b'{"code":"23505","message":"duplicate"}'))
    with pytest.raises(RemoteServiceError) as raised:
        json_request('https://example.invalid', method='POST', headers={'Authorization': 'Bearer test'},
                     context='Supabase', opener=opener, body={'id': 1})
    assert raised.value.code == '23505'
    assert isinstance(raised.value.__cause__, HTTPError)


@pytest.mark.parametrize('message,expected', [('sin membresia activa', MembershipRequired), ('horario no disponible', EntityNotFound)])
def test_database_messages_are_translated_at_the_adapter_boundary(message, expected):
    with pytest.raises(expected):
        raise_schedule_enrollment_error(RemoteServiceError('RPC', 400, {'code': 'P0001', 'message': message}))


def test_registration_keeps_the_saved_client_when_checkout_fails():
    saved = {'cliente': {'id_cliente': 1}, 'membresia': {'id_membresia': 1}}
    calls = []
    class Gateway:
        configured = True
        def validate_configuration(self):
            pass
        def create_membership_checkout(self, result, admin=False):
            assert result == saved and admin
            raise RuntimeError('Stripe temporalmente no disponible')
    clients = SimpleNamespace(register_admin_client=lambda payload: calls.append(payload) or saved)
    service = ClientPaymentsService(clients, None, None, gateway_factory=lambda _: Gateway(), notify=lambda *_: None)
    payload = {'pagar_con_stripe': True}
    result = service.register_admin(payload)
    assert result['cliente'] == saved['cliente']
    assert result['payment']['configured'] is True
    assert len(calls) == 1


@pytest.mark.parametrize('filename,mime', [('a.svg', 'image/svg+xml'), ('a.jpg', 'image/png'), ('a.png', 'text/plain')])
def test_image_policy_rejects_unsupported_or_mismatched_formats(filename, mime):
    with pytest.raises(ValueError):
        validate_image(filename, b'image', mime)


def test_http_reports_a_late_repository_failure_as_503():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from presentation.error_handlers import install_error_handlers
    from application.errors import PersistenceUnavailable
    app = FastAPI()
    install_error_handlers(app)
    @app.get('/read')
    def query():
        raise PersistenceUnavailable('detalle interno de proveedor')
    response = TestClient(app).get('/read')
    assert response.status_code == 503
    assert 'detalle interno' not in response.text
