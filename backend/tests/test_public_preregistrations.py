"""Registro público separado: sin clientes impagos, sin Stripe real ni correos."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.operations.preregistrations import AttachPreregistrationCheckoutCommand
from application.services.clients_service import ClientsService
from application.services.client_payments_service import ClientPaymentsService
from application.services.gym_service import GymService
from domain.errors import EntityNotFound
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from presentation.dependencies import get_client_payments_service
from presentation.error_handlers import install_error_handlers
from presentation.routes.clients_routes import router
from tests.test_priority_fixes import Passwords

PAYLOAD = dict(nombre='Solicitud local', correo='solicitud@example.com', dni='12345678',
               telefono='999111222', password='clave-local', plan='MENSUAL')


class Gateway:
    configured = True

    def __init__(self):
        self.sessions, self.created = {}, []
        self.fail_create = self.fail_retrieve = False

    def validate_configuration(self):
        pass

    def create_preregistration_checkout(self, row):
        if self.fail_create:
            raise RuntimeError('fallo privado del proveedor')
        key = (row['token'], row['intento'])
        self.created.append(key)
        sid = f"cs_local_{row['token']}_{row['intento']}"
        self.sessions.setdefault(sid, dict(id=sid, url=f'https://checkout.example.test/{sid}', livemode=False,
            mode='payment', currency='pen', amount_total=round(row['monto_pago'] * 100), status='open', payment_status='unpaid',
            client_reference_id=f"preregistration:{row['token']}",
            metadata=dict(purpose='membership_preregistration', preregistration_token=row['token'], attempt=str(row['intento']))))
        return dict(configured=True, session_id=sid, checkout_url=self.sessions[sid]['url'], amount=row['monto_pago'], currency='PEN')

    def get_checkout_session(self, sid):
        if self.fail_retrieve:
            raise RuntimeError('sin conexión privada')
        return deepcopy(self.sessions[sid])

    def expire_checkout_session(self, sid):
        checkout = self.get_checkout_session(sid)
        if checkout['status'] == 'open':
            self.sessions[sid]['status'] = 'expired'
        return self.get_checkout_session(sid)

    def find_preregistration_checkout(self, row):
        if self.fail_retrieve:
            raise RuntimeError('sin conexión privada')
        return next((deepcopy(s) for s in self.sessions.values()
                     if s['client_reference_id'] == f"preregistration:{row['token']}"
                     and s['metadata']['attempt'] == str(row['intento'])), None)

    def construct_webhook_event(self, payload, signature):
        if signature != 'firma-local':
            raise ValueError('Firma inválida')
        return payload


@pytest.fixture
def setup():
    gym = GymService(MemoryGymRepository(), Passwords())
    clients = ClientsService(gym)
    gateway, notify = Gateway(), Mock(return_value={'status': 'simulada'})
    settings = SimpleNamespace(has_supabase_credentials=True, stripe_mode='test')
    payments = ClientPaymentsService(clients, gym, settings, gateway_factory=lambda _: gateway, notify=notify)
    return gym, clients, gateway, payments, notify


def paid(gateway, result):
    sid = result['payment']['session_id']
    gateway.sessions[sid].update(status='complete', payment_status='paid')
    return sid


def event(payments, checkout, kind='checkout.session.completed'):
    return payments.process_webhook({'type': kind, 'data': {'object': checkout}}, 'firma-local')


def test_public_http_stores_only_a_private_temporary_request(setup):
    gym, _, _, payments, _ = setup
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_client_payments_service] = lambda: payments
    response = TestClient(app).post('/registro-publico', json={**PAYLOAD, 'estado_pago': 'PAGADO', 'google_sub': 'falso'})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {'preregistro', 'payment'}
    assert set(body['preregistro']) == {'token', 'estado', 'expira_en', 'monto_pago'}
    assert gym.clientes_normalized() == gym.membresias() == []
    row = gym.repository.state['preregistros'][0]
    assert row['password_hash'] == 'test:clave-local'
    assert row['google_sub'] == ''
    assert PAYLOAD['password'] not in response.text


def test_retry_preserves_request_quote_and_checkout_despite_catalog_changes(setup):
    gym, _, gateway, payments, _ = setup
    first = payments.register_public(PAYLOAD)
    gym.repository.state['planes_membresia'][0]['precio'] = 999
    retry = payments.register_public({**PAYLOAD, 'plan': 'ANUAL'})
    assert retry == first
    assert len(gateway.created) == len(gym.repository.state['preregistros']) == 1
    assert gym.clientes_normalized() == []


@pytest.mark.parametrize('change', [{'password': 'otra-clave'}, {'dni': '87654321'}, {'correo': 'otra@example.com'}])
def test_retry_cannot_take_over_another_request(setup, change):
    gym, _, _, payments, _ = setup
    payments.register_public(PAYLOAD)
    before = deepcopy(gym.repository.state)
    with pytest.raises(ValueError):
        payments.register_public({**PAYLOAD, **change})
    assert gym.repository.state == before


def test_checkout_failure_retains_draft_without_exposing_provider_or_duplicating_it(setup):
    gym, _, gateway, payments, _ = setup
    gateway.fail_create = True
    first = payments.register_public(PAYLOAD)
    assert 'privado' not in str(first)
    assert 'checkout_url' not in first['payment']
    assert gym.clientes_normalized() == []
    gateway.fail_create = False
    retry = payments.register_public(PAYLOAD)
    assert retry['preregistro']['token'] == first['preregistro']['token']
    assert len(gym.repository.state['preregistros']) == 1


def test_verified_webhook_creates_paid_client_once_without_browser_return(setup):
    gym, clients, gateway, payments, notify = setup
    result = payments.register_public(PAYLOAD)
    sid = paid(gateway, result)
    event(payments, gateway.sessions[sid])
    confirmed = payments.confirm_return(sid)
    assert confirmed['confirmed'] and confirmed['preregistration_token'] == result['preregistro']['token']
    assert len(gym.clientes_normalized()) == len(gym.membresias()) == 1
    membership = gym.latest_membership(confirmed['id_cliente'])
    assert membership['estado'] == 'EN_TRAMITE' and membership['estado_pago'] == 'PAGADO'
    assert membership['fecha_inicio'] == membership['fecha_fin'] == ''
    row = gym.repository.state['preregistros'][0]
    assert row['estado'] == 'CONVERTIDO' and row['password_hash'] == row['correo'] == row['dni'] == ''
    clients.activate_client_membership(confirmed['id_cliente'])
    active = deepcopy(gym.latest_membership(confirmed['id_cliente']))
    payments.confirm_return(sid)
    assert gym.latest_membership(confirmed['id_cliente']) == active
    assert notify.call_args.args[-1] == 'payment'


@pytest.mark.parametrize('change', [dict(amount_total=1), dict(currency='usd'), dict(livemode=True),
    dict(mode='subscription'), dict(client_reference_id='preregistration:ajeno'), dict(id='cs_ajena'),
    dict(metadata=dict(purpose='membership_preregistration', preregistration_token='ajeno', attempt='1'))])
def test_confirmation_rejects_unrelated_or_altered_payment(setup, change):
    gym, _, gateway, payments, notify = setup
    result = payments.register_public(PAYLOAD)
    sid = paid(gateway, result)
    gateway.sessions[sid].update(change)
    with pytest.raises((ValueError, EntityNotFound)):
        payments.confirm_return(sid)
    assert gym.clientes_normalized() == gym.membresias() == []
    notify.assert_not_called()


def test_unpaid_complete_session_neither_creates_client_nor_expires_processing_payment(setup):
    gym, _, gateway, payments, notify = setup
    result = payments.register_public(PAYLOAD)
    sid = result['payment']['session_id']
    gateway.sessions[sid]['status'] = 'complete'
    assert payments.confirm_return(sid)['confirmed'] is False
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert gym.repository.state['preregistros'][0]['estado'] == 'PENDIENTE'
    assert gym.clientes_normalized() == []
    notify.assert_not_called()


def test_expiration_archives_request_and_releases_promo_once_then_allows_new_attempt(setup):
    gym, _, gateway, payments, _ = setup
    gym.upsert_promocion(dict(nombre='Oferta', tipo_descuento='monto', valor_descuento=10, activo=True, limite_cupos=1))
    result = payments.register_public(PAYLOAD)
    assert gym.promociones()[0]['usos_actuales'] == 1
    sid = result['payment']['session_id']
    gateway.sessions[sid]['status'] = 'expired'
    for _ in range(2):
        event(payments, gateway.sessions[sid], 'checkout.session.expired')
    assert gym.repository.state['preregistros'][0]['estado'] == 'EXPIRADO'
    assert gym.promociones()[0]['usos_actuales'] == 0
    retry = payments.register_public(PAYLOAD)
    assert retry['preregistro']['token'] == result['preregistro']['token']
    assert retry['payment']['session_id'] != sid
    # Un evento antiguo no archiva el nuevo intento.
    event(payments, gateway.sessions[sid], 'checkout.session.expired')
    assert gym.repository.state['preregistros'][0]['estado'] == 'PENDIENTE'
    assert gym.promociones()[0]['usos_actuales'] == 1


def test_periodic_reconciliation_preserves_uncertain_payment_and_confirms_late_paid_session(setup):
    gym, _, gateway, payments, _ = setup
    result = payments.register_public(PAYLOAD)
    gateway.fail_retrieve = True
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert gym.repository.state['preregistros'][0]['estado'] == 'PENDIENTE'
    gateway.fail_retrieve = False
    paid(gateway, result)
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert len(gym.clientes_normalized()) == 1
    assert gym.repository.state['preregistros'][0]['estado'] == 'CONVERTIDO'


def test_periodic_reconciliation_expires_open_session_before_archiving(setup):
    gym, _, gateway, payments, _ = setup
    result = payments.register_public(PAYLOAD)
    assert payments.archive_due_preregistrations('2000-01-01T00:00:00+00:00') == 0
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert gateway.sessions[result['payment']['session_id']]['status'] == 'expired'
    assert gym.repository.state['preregistros'][0]['estado'] == 'EXPIRADO'
    assert gym.clientes_normalized() == []


def test_webhook_before_checkout_attachment_and_parallel_confirmations_do_not_duplicate(setup, monkeypatch):
    gym, _, gateway, payments, _ = setup
    create = gateway.create_preregistration_checkout
    def immediately_paid(row):
        result = create(row)
        sid = result['session_id']
        gateway.sessions[sid].update(status='complete', payment_status='paid')
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(payments.confirm_return, [sid, sid]))
        return result
    monkeypatch.setattr(gateway, 'create_preregistration_checkout', immediately_paid)
    payments.register_public(PAYLOAD)
    assert len(gym.clientes_normalized()) == len(gym.membresias()) == 1
    assert gym.repository.state['preregistros'][0]['estado'] == 'CONVERTIDO'


def test_deleted_customer_is_not_resurrected_by_replayed_payment(setup):
    gym, clients, gateway, payments, _ = setup
    sid = paid(gateway, payments.register_public(PAYLOAD))
    confirmed = payments.confirm_return(sid)
    clients.delete_client(f"SGCLI{confirmed['id_cliente']:03d}")
    with pytest.raises(EntityNotFound):
        payments.confirm_return(sid)
    assert gym.clientes_normalized() == gym.membresias() == []
    # Una nueva alta tras el borrado es otro intento, sin reutilizar el comprobante antiguo.
    assert payments.register_public(PAYLOAD)['payment']['session_id'] != sid


def test_admin_registration_still_supports_unpaid_clients_but_cannot_duplicate_a_pending_public_identity(setup):
    gym, clients, _, payments, _ = setup
    payments.register_public(PAYLOAD)
    with pytest.raises(ValueError, match='preregistro'):
        clients.register_admin_client(PAYLOAD)
    saved = clients.register_admin_client({**PAYLOAD, 'correo': 'admin@example.com', 'dni': '87654321'})
    assert saved['membresia']['estado_pago'] == 'PENDIENTE'
    assert saved['cliente']['origen_registro'] == 'ADMIN'
    assert len(gym.clientes_normalized()) == 1


def test_lost_attachment_reuses_the_same_checkout_on_retry(setup, monkeypatch):
    gym, _, gateway, payments, _ = setup
    # GymService construye executors ligeros; se inyecta el fallo en el repositorio.
    original = gym.repository.execute
    fail = [True]
    def once(command, passwords=None):
        if isinstance(command, AttachPreregistrationCheckoutCommand) and fail[0]:
            fail[0] = False
            raise RuntimeError('respuesta perdida')
        return original(command, passwords)
    monkeypatch.setattr(gym.repository, 'execute', once)
    first = payments.register_public(PAYLOAD)
    assert 'checkout_url' not in first['payment']
    retry = payments.register_public(PAYLOAD)
    assert len(set(gateway.created)) == 1 and len(gateway.sessions) == 1
    assert retry['payment']['checkout_url']


def test_old_uncertain_creation_is_recovered_without_creating_a_second_checkout(setup, monkeypatch):
    gym, _, gateway, payments, _ = setup
    result = payments.register_public(PAYLOAD)
    row = gym.repository.state['preregistros'][0]
    row.update(checkout_session_id='', checkout_url='', creado_en='2000-01-01T00:00:00+00:00')
    before = len(gateway.created)
    retry = payments.register_public(PAYLOAD)
    assert retry['payment']['session_id'] == result['payment']['session_id']
    assert len(gateway.created) == before


def test_unstarted_expired_request_is_archived_only_after_successful_provider_search(setup):
    gym, _, gateway, payments, _ = setup
    gateway.fail_create = True
    payments.register_public(PAYLOAD)
    gym.repository.state['preregistros'][0]['creado_en'] = '2000-01-01T00:00:00+00:00'
    gateway.fail_retrieve = True
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert gym.repository.state['preregistros'][0]['estado'] == 'PENDIENTE'
    gateway.fail_retrieve = False
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert gym.repository.state['preregistros'][0]['estado'] == 'EXPIRADO'
    assert gateway.created == []


def test_google_identity_is_verified_and_copied_only_after_payment(setup):
    gym, clients, gateway, payments, _ = setup
    clients.identity = SimpleNamespace(verify=lambda _: dict(email=PAYLOAD['correo'], sub='google-local', name='Nombre local'))
    clients.sessions = SimpleNamespace(validate_configuration=lambda: None)
    result = payments.register_public({**PAYLOAD, 'google_credential': 'credencial-local', 'password': ''})
    assert gym.clientes_normalized() == []
    assert gym.repository.state['preregistros'][0]['google_sub'] == 'google-local'
    payments.confirm_return(paid(gateway, result))
    assert gym.repository.state['clientes'][0]['google_sub'] == 'google-local'
    assert gym.repository.state['preregistros'][0]['google_sub'] == ''


def test_reserved_plan_cannot_be_deleted_or_repriced_during_payment(setup):
    gym, _, gateway, payments, _ = setup
    result = payments.register_public(PAYLOAD)
    with pytest.raises(ValueError, match='solicitudes'):
        gym.delete_plan_membresia(1)
    gym.upsert_plan_membresia(dict(id_pm=1, nombre_plan='MENSUAL', precio=999, duracion='30 días', activo=False))
    sid = paid(gateway, result)
    confirmed = payments.confirm_return(sid)
    assert gym.latest_membership(confirmed['id_cliente'])['monto_pago'] == 79
