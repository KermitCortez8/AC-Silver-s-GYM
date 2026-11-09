from datetime import date
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

import pytest

from application.services.clients_service import ClientsService
from application.services.membership_renewal_service import MembershipRenewalService, renewal_token
from application.services.membership_notifications import enqueue_expiration_reminders
from application.services.email_templates import membership_expiration_email
from infrastructure.config import Settings
from infrastructure.services.local_gym_service import LocalGymService


@pytest.fixture
def renewal(monkeypatch):
    monkeypatch.setattr('application.services.membership_renewal_service.lima_today', lambda: date(2026, 11, 9))
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-09')
    gym = LocalGymService()
    saved = ClientsService(gym).register_admin_client({
        'nombre': 'Cliente Renovación', 'correo': 'renovacion@example.com',
        'dni': '34567891', 'password': 'secreto123', 'plan': 'MENSUAL',
    })
    source = gym.state['membresia'][0]
    source.update(estado='ACTIVO', estado_pago='PAGADO', fecha_inicio='2026-10-10', fecha_fin='2026-11-10')
    settings = Settings(auth_secret_key='solo-pruebas', frontend_public_url='https://gym.example')
    calls = []
    gateway = SimpleNamespace(validate_configuration=lambda: None,
                              get_checkout_session=lambda sid: {'status': 'open', 'url': 'https://checkout.stripe.com/test'},
                              create_membership_checkout=lambda row: calls.append(row) or {'session_id': 'cs_test_renewal', 'checkout_url': 'https://checkout.stripe.com/test'})
    service = MembershipRenewalService(gym, settings, gateway)
    return gym, source, settings, calls, service, renewal_token(settings, source)


def test_link_details_and_checkout_reuse_pending_without_mutating_source(renewal):
    gym, source, settings, calls, service, token = renewal
    details = service.details(token)
    amount = details['monto_pago']
    before = dict(source)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: service.checkout(token, amount), range(2)))
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 2
    assert len({c['membresia']['id_membresia'] for c in calls}) == 1
    assert calls[0]['membresia']['estado_pago'] == 'PENDIENTE'
    assert gym.membership(source['id_cliente'], source['id_membresia']) == before
    assert 'correo' not in details and 'id_cliente' not in details


def test_modified_expired_and_early_links_are_rejected(renewal, monkeypatch):
    gym, source, settings, calls, service, token = renewal
    for invalid in (token[:-1] + ('a' if token[-1] != 'a' else 'b'), 'otro', token.replace('.', '.1', 1)):
        with pytest.raises(ValueError, match='enlace'):
            service.details(invalid)
    for today in (date(2026, 11, 2), date(2026, 12, 11)):
        monkeypatch.setattr('application.services.membership_renewal_service.lima_today', lambda: today)
        with pytest.raises(ValueError, match='enlace'):
            service.checkout(token, 100)
    assert not calls


def test_price_change_rejected_and_paid_renewal_prevents_new_charge(renewal):
    gym, source, settings, calls, service, token = renewal
    amount = service.details(token)['monto_pago']
    with pytest.raises(ValueError, match='precio'):
        service.checkout(token, amount + 1)
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 1
    service.checkout(token, amount)
    pending = calls[-1]['membresia']
    gym.confirmar_pago_cliente_publico(source['id_cliente'], {
        'id_membresia': pending['id_membresia'], 'monto_pago': amount,
        'metodo_pago': 'stripe', 'referencia_pago': 'cs_renewal',
    })
    assert service.details(token)['renovada'] is True
    gym.state['planes_membresia'][0]['precio'] = amount + 30
    assert service.details(token)['monto_pago'] == amount
    with pytest.raises(ValueError, match='pagada'):
        service.checkout(token, amount)
    assert len(calls) == 1


def test_reminders_select_lima_window_and_skip_paid_renewal(renewal):
    gym, source, settings, calls, service, token = renewal
    events = []
    notifier = SimpleNamespace(notify=lambda *args: events.append(args))
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 6))
    assert not events
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 7))
    assert events[-1][0] == 'expiring'
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 10))
    assert events[-1][0] == 'expiring'
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 11))
    assert events[-1][0] == 'expired'
    message = membership_expiration_email(settings, 'expiring', events[0][1], events[0][2])
    assert f'/renovar-membresia#token={token}' in message['text']
    gym.crear_membresia({'id_cliente': source['id_cliente'], 'id_pm': source['id_pm']})
    gym.confirmar_pago_manual_cliente(source['id_cliente'])
    events.clear()
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 11))
    assert not events


def test_checkout_reuses_open_session_and_retries_only_expired_session(renewal):
    gym, source, settings, calls, service, token = renewal
    amount = service.details(token)['monto_pago']
    service.checkout(token, amount)
    service.checkout(token, amount)
    assert len(calls) == 1
    service.gateway.get_checkout_session = lambda sid: {'status': 'expired'}
    service.checkout(token, amount)
    assert len(calls) == 2
    assert calls[-1]['checkout_attempt'] == 'cs_test_renewal'
    service.gateway.get_checkout_session = lambda sid: {'status': 'complete', 'payment_status': 'paid'}
    with pytest.raises(ValueError, match='confirmar su pago'):
        service.checkout(token, amount)
    assert len(calls) == 2


def test_public_api_uses_personal_link_and_rejects_invalid_amounts(renewal):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from presentation.routes.clients_routes import router
    from presentation.dependencies import get_client_payments_service
    gym, source, settings, calls, service, token = renewal
    app = FastAPI()
    app.include_router(router, prefix='/api')
    app.dependency_overrides[get_client_payments_service] = lambda: SimpleNamespace(renewal=lambda: service)
    http = TestClient(app)
    response = http.get('/api/renovacion', params={'token': token})
    assert response.status_code == 200
    amount = response.json()['monto_pago']
    assert http.get('/api/renovacion', params={'token': 'alterado'}).status_code == 400
    assert http.post('/api/renovacion/checkout', json={'token': token, 'monto_pago': -1}).status_code == 422
    assert http.post('/api/renovacion/checkout', json={'token': token, 'monto_pago': amount + 1}).status_code == 400
    assert http.post('/api/renovacion/checkout', json={'token': token, 'monto_pago': amount}).status_code == 200


def test_early_renewal_payment_preserves_current_access(renewal, monkeypatch):
    gym, source, settings, calls, service, token = renewal
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-09')
    gym.state['clientes'][0]['estado'] = 'ACTIVO'
    amount = service.details(token)['monto_pago']
    service.checkout(token, amount)
    pending = calls[-1]['membresia']
    gym.confirmar_pago_cliente_publico(source['id_cliente'], {
        'id_membresia': pending['id_membresia'], 'monto_pago': amount,
        'metodo_pago': 'stripe', 'referencia_pago': 'cs_test_renewal',
    })
    assert gym.get_cliente(source['id_cliente'])['estado'] == 'ACTIVO'
    assert gym.membership(source['id_cliente'], source['id_membresia'])['fecha_fin'] == '2026-11-10'


def test_expired_renewal_activates_on_verified_payment_and_duplicate_does_not_extend(renewal, monkeypatch):
    from copy import deepcopy
    from application.services.membership_checkout_service import confirm_verified_checkout
    from application.services.auth_service import AuthService
    from application.services.email_templates import membership_email
    gym, source, settings, calls, service, token = renewal
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-11')
    monkeypatch.setattr('application.services.auth_service._today_iso', lambda: '2026-11-11')
    service.checkout(token, service.details(token)['monto_pago'])
    pending = calls[-1]['membresia']
    checkout = {'id': 'cs_test_renewal', 'status': 'complete', 'payment_status': 'paid', 'livemode': False,
                'mode': 'payment', 'client_reference_id': f"membership:{source['id_cliente']}",
                'metadata': {'purpose': 'membership', 'client_id': str(source['id_cliente']),
                             'membership_id': str(pending['id_membresia'])},
                'currency': 'pen', 'amount_total': int(pending['monto_pago'] * 100)}
    notices = []
    notify = lambda _settings, _clients, saved, event: notices.append((saved, event)) or {'status': 'sent'}
    confirm = lambda: confirm_verified_checkout('cs_test_renewal', ClientsService(gym), settings, checkout,
        gateway=service.gateway, notify=notify)
    result = confirm()
    assert result['membership_status'] == 'ACTIVO'
    assert result['fecha_inicio'] == '2026-11-11'
    assert result['fecha_fin'] == '2026-12-11'
    AuthService(gym).session_for_client(gym.get_cliente(source['id_cliente']))
    before = deepcopy(gym.latest_membership(source['id_cliente']))
    assert confirm()['membership_status'] == 'ACTIVO'
    assert gym.latest_membership(source['id_cliente']) == before
    mail = membership_email(settings, 'payment', notices[0][0], gym.get_plan_membresia(pending['id_pm']))
    assert 'automáticamente' in mail['text'] and 'activación administrativa' not in mail['text']
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2027-01-01')
    gym.expire_memberships()
    assert confirm()['membership_status'] == 'VENCIDA'
    assert gym.latest_membership(source['id_cliente'])['fecha_fin'] == before['fecha_fin']


def test_early_renewal_starts_after_inclusive_last_day_and_is_not_activated_twice(renewal, monkeypatch):
    gym, source, settings, calls, service, token = renewal
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-09')
    source_before = gym.membership(source['id_cliente'], source['id_membresia'])
    service.checkout(token, service.details(token)['monto_pago'])
    gym.confirmar_pago_manual_cliente(source['id_cliente'])
    renewed = gym.latest_membership(source['id_cliente'])
    assert renewed['estado'] == 'ACTIVO'
    assert renewed['fecha_inicio'] == '2026-11-11'
    assert renewed['fecha_fin'] == '2026-12-11'
    assert gym.membership(source['id_cliente'], source['id_membresia']) == source_before
    gym.confirmar_pago_manual_cliente(source['id_cliente'])
    assert gym.latest_membership(source['id_cliente']) == renewed


def test_paid_history_without_any_initial_activation_cannot_bypass_first_activation(monkeypatch):
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-09')
    gym = LocalGymService()
    registered = ClientsService(gym).register_admin_client({
        'nombre': 'Primera Activación', 'correo': 'primera@example.com',
        'dni': '12349876', 'password': 'secreto123', 'plan': 'MENSUAL',
    })
    client_id = registered['cliente']['id_cliente']
    gym.confirmar_pago_manual_cliente(client_id)
    assert gym.latest_membership(client_id)['estado'] == 'EN_TRAMITE'
    gym.crear_membresia({'id_cliente': client_id, 'id_pm': registered['membresia']['id_pm']})
    gym.confirmar_pago_manual_cliente(client_id)
    assert gym.latest_membership(client_id)['estado'] == 'EN_TRAMITE'
    assert gym.get_cliente(client_id)['estado'] != 'ACTIVO'


def test_reconfirmation_recovers_previously_paid_pending_renewal_without_new_charge(renewal, monkeypatch):
    gym, source, settings, calls, service, token = renewal
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-11')
    service.checkout(token, service.details(token)['monto_pago'])
    pending = calls[-1]['membresia']
    stored = next(m for m in gym.state['membresia'] if m['id_membresia'] == pending['id_membresia'])
    stored.update(estado_pago='PAGADO', referencia_pago='cs_test_renewal', fecha_pago='2026-11-10')
    gym.confirmar_pago_cliente_publico(source['id_cliente'], {
        'id_membresia': pending['id_membresia'], 'monto_pago': pending['monto_pago'],
        'referencia_pago': 'cs_test_renewal', 'metodo_pago': 'stripe'})
    renewed = gym.latest_membership(source['id_cliente'])
    assert renewed['estado'] == 'ACTIVO'
    assert renewed['fecha_inicio'] == '2026-11-11'
    assert renewed['fecha_pago'] == '2026-11-10'
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 2


@pytest.mark.parametrize('days,allowed', [(8, False), (7, True), (3, True), (0, True), (-1, True)])
def test_personal_link_and_checkout_use_last_week_or_expired_membership(renewal, days, allowed):
    from datetime import timedelta
    gym, source, settings, calls, service, token = renewal
    row = next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])
    row['fecha_fin'] = (date(2026, 11, 9) + timedelta(days=days)).isoformat()
    token = renewal_token(settings, row)
    if allowed:
        amount = service.details(token)['monto_pago']
        assert service.checkout(token, amount)['checkout_url']
        assert len(calls) == 1
    else:
        with pytest.raises(ValueError, match='enlace'):
            service.details(token)
        with pytest.raises(ValueError, match='enlace'):
            service.checkout(token, 80)
        assert not calls and len(gym.membresias_por_cliente(source['id_cliente'])) == 1


def test_expiration_notice_requires_an_activated_period_not_initial_payment_or_future_period(renewal):
    gym, source, settings, calls, service, token = renewal
    row = next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])
    events = []
    notifier = SimpleNamespace(notify=lambda *args: events.append(args))
    row['estado'] = 'EN_TRAMITE'
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 9))
    assert not events
    row.update(estado='ACTIVO', fecha_inicio='2026-11-10', fecha_fin='2026-11-11')
    enqueue_expiration_reminders(notifier, gym, date(2026, 11, 9))
    assert not events
