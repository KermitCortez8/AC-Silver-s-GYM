from copy import deepcopy
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.membresias_pagos.integracion.test_membership_renewal import renewal
from application.services.clients_service import ClientsService
from application.services.client_payments_service import ClientPaymentsService
from presentation.dependencies import get_client_payments_service, get_current_user
from presentation.routes.clients_routes import router


@pytest.fixture
def admin(renewal, monkeypatch):
    gym, source, settings, calls, service, token = renewal
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-11-09')
    gym.state['clientes'][0]['estado'] = 'ACTIVO'
    service.gateway.create_membership_checkout = lambda row, **options: calls.append((row, options)) or {
        'session_id': 'cs_test_admin_renewal', 'checkout_url': 'https://checkout.stripe.com/test'}
    payments = ClientPaymentsService(ClientsService(gym), gym, settings,
        gateway_factory=lambda _: service.gateway, notify=lambda *args: {'status': 'sent'})
    app = FastAPI()
    app.include_router(router, prefix='/api')
    app.dependency_overrides[get_client_payments_service] = lambda: payments
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role='admin')
    http = TestClient(app)
    return gym, source, calls, payments, app, http


def payload(admin, method='efectivo'):
    gym, source, calls, payments, app, http = admin
    details = http.get(f"/api/clientes/{source['id_cliente']}/renovacion").json()
    return {'id_membresia_origen': details['id_membresia_origen'], 'monto_pago': details['monto_pago'],
            'metodo_pago': method, 'pago_recibido': method == 'efectivo'}


def test_admin_cash_renews_atomically_and_retries_do_not_create_another_purchase(admin):
    gym, source, calls, payments, app, http = admin
    before = deepcopy(gym.membership(source['id_cliente'], source['id_membresia']))
    request = payload(admin)
    url = f"/api/clientes/{source['id_cliente']}/renovar-membresia"
    first = http.post(url, json=request)
    assert first.status_code == 200
    assert first.json()['membership_status'] == 'ACTIVO'
    assert first.json()['fecha_inicio'] == '2026-11-11'
    membership = gym.latest_membership(source['id_cliente'])
    assert membership['metodo_pago'] == 'efectivo' and membership['estado_pago'] == 'PAGADO'
    assert http.post(url, json=request).status_code == 400
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 2
    assert gym.membership(source['id_cliente'], source['id_membresia']) == before
    assert not calls
    assert 'password_hash' not in first.text


def test_cash_requires_receipt_confirmation_and_current_price_without_partial_writes(admin):
    gym, source, calls, payments, app, http = admin
    request = payload(admin)
    url = f"/api/clientes/{source['id_cliente']}/renovar-membresia"
    assert http.post(url, json={**request, 'pago_recibido': False}).status_code == 400
    assert http.post(url, json={**request, 'monto_pago': request['monto_pago'] + 1}).status_code == 400
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 1


def test_admin_stripe_reuses_pending_checkout_and_returns_to_admin(admin):
    gym, source, calls, payments, app, http = admin
    request = payload(admin, 'stripe')
    url = f"/api/clientes/{source['id_cliente']}/renovar-membresia"
    first = http.post(url, json=request)
    assert first.status_code == 200
    assert first.json()['payment']['checkout_url'].startswith('https://checkout.stripe.com/')
    assert calls[0][1] == {'admin': True}
    assert gym.latest_membership(source['id_cliente'])['estado_pago'] == 'PENDIENTE'
    assert http.post(url, json=request).status_code == 200
    assert len(calls) == 1 and len(gym.membresias_por_cliente(source['id_cliente'])) == 2
    assert http.post(url, json={**request, 'metodo_pago': 'efectivo', 'pago_recibido': True}).status_code == 400
    assert gym.latest_membership(source['id_cliente'])['estado_pago'] == 'PENDIENTE'


def test_cash_double_submission_is_atomic_even_when_concurrent(admin):
    gym, source, calls, payments, app, http = admin
    request = payload(admin)
    def renew(_):
        try:
            return payments.renew_admin(source['id_cliente'], request)['membership_status']
        except ValueError:
            return 'duplicado'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(renew, range(2)))
    assert results.count('ACTIVO') == 1
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 2


@pytest.mark.parametrize('role', ['user', 'trainer'])
def test_renewal_endpoints_reject_non_staff_sessions(admin, role):
    gym, source, calls, payments, app, http = admin
    request = payload(admin)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=role)
    assert http.get(f"/api/clientes/{source['id_cliente']}/renovacion").status_code == 403
    assert http.post(f"/api/clientes/{source['id_cliente']}/renovar-membresia", json=request).status_code == 403
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 1


def test_first_paid_but_unactivated_membership_cannot_be_renewed(admin):
    gym, source, calls, payments, app, http = admin
    next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])['estado'] = 'EN_TRAMITE'
    assert http.get(f"/api/clientes/{source['id_cliente']}/renovacion").status_code == 400


def test_staff_can_renew_long_expired_membership_without_email_token_or_stripe_config(admin):
    gym, source, calls, payments, app, http = admin
    previous = next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])
    previous.update(fecha_inicio='2026-01-01', fecha_fin='2026-02-01', estado='VENCIDA')
    gym.state['clientes'][0]['estado'] = 'VENCIDA'
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role='staff')
    result = http.post(f"/api/clientes/{source['id_cliente']}/renovar-membresia", json=payload(admin))
    assert result.status_code == 200 and result.json()['fecha_inicio'] == '2026-11-09'
    assert not calls


@pytest.mark.parametrize('origin', ['PUBLICO', 'ADMIN'])
def test_renewal_is_available_for_clients_from_either_registration_origin(admin, origin):
    gym, source, calls, payments, app, http = admin
    gym.state['clientes'][0]['origen_registro'] = origin
    response = http.post(f"/api/clientes/{source['id_cliente']}/renovar-membresia", json=payload(admin))
    assert response.status_code == 200 and response.json()['membership_status'] == 'ACTIVO'


@pytest.mark.parametrize('days,allowed', [(8, False), (7, True), (3, True), (0, True), (-1, True)])
def test_admin_renewal_window_is_enforced_in_preview_and_cash_transaction(admin, days, allowed):
    from datetime import date, timedelta
    gym, source, calls, payments, app, http = admin
    row = next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])
    row['fecha_fin'] = (date(2026, 11, 9) + timedelta(days=days)).isoformat()
    url = f"/api/clientes/{source['id_cliente']}"
    preview = http.get(url + '/renovacion')
    assert preview.status_code == (200 if allowed else 400)
    client = next(c for c in ClientsService(gym).list_clients() if c['id_cliente'] == source['id_cliente'])
    assert client['renewal_allowed'] is allowed
    request = {'id_membresia_origen': source['id_membresia'], 'monto_pago': gym.get_plan_membresia(source['id_pm'])['precio'],
               'metodo_pago': 'efectivo', 'pago_recibido': True}
    response = http.post(url + '/renovar-membresia', json=request)
    assert response.status_code == (200 if allowed else 400)
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == (2 if allowed else 1)
    assert not calls
    if not allowed:
        assert '7 días' in response.json()['detail']


def test_early_stripe_and_generic_membership_creation_cannot_bypass_the_window(admin):
    gym, source, calls, payments, app, http = admin
    row = next(m for m in gym.state['membresia'] if m['id_membresia'] == source['id_membresia'])
    row['fecha_fin'] = '2026-12-09'
    request = {'id_membresia_origen': source['id_membresia'], 'monto_pago': gym.get_plan_membresia(source['id_pm'])['precio'],
               'metodo_pago': 'stripe'}
    assert http.post(f"/api/clientes/{source['id_cliente']}/renovar-membresia", json=request).status_code == 400
    with pytest.raises(ValueError, match='7 días'):
        gym.crear_membresia({'id_cliente': source['id_cliente'], 'id_pm': source['id_pm']})
    assert len(gym.membresias_por_cliente(source['id_cliente'])) == 1 and not calls
