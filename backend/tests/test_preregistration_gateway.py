"""Contrato del adaptador Stripe: referencias opacas y recuperación sin nuevos cobros."""
from types import SimpleNamespace

import pytest

from infrastructure.config import Settings
from infrastructure.services.stripe_service import StripeService


def registration():
    return dict(token='12345678-1234-4234-8234-123456789abc', intento=1, correo='local@example.com',
                monto_pago=69, plan={'nombre_plan': 'MENSUAL'}, creado_en='2026-10-30T00:00:00+00:00')


def gateway():
    return StripeService(Settings(stripe_secret_key='sk_test_local', stripe_webhook_secret='whsec_local',
                                  frontend_public_url='https://gym.example.test'))


def test_checkout_retries_have_same_key_and_do_not_put_personal_data_in_metadata(monkeypatch):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return {'id': 'cs_local', 'url': 'https://checkout.example.test/local'}
    monkeypatch.setattr('infrastructure.services.stripe_service.stripe.checkout.Session.create', create)
    row = registration()
    service = gateway()
    service.create_preregistration_checkout(row)
    service.create_preregistration_checkout(row)
    assert calls[0] == calls[1]
    assert calls[0]['metadata'] == {'purpose': 'membership_preregistration',
                                  'preregistration_token': row['token'], 'attempt': '1'}
    assert f"/registro/pago/p-{row['token']}?result=success" in calls[0]['success_url']
    assert calls[0]['line_items'][0]['price_data']['unit_amount'] == 6900
    service.create_preregistration_checkout({**row, 'intento': 2})
    assert calls[-1]['idempotency_key'] != calls[0]['idempotency_key']


def test_recovery_searches_all_pages_and_uses_token_and_attempt(monkeypatch):
    row, calls = registration(), []
    wanted = {'id': 'cs_recuperada', 'client_reference_id': f"preregistration:{row['token']}", 'metadata': {'attempt': '1'}}
    def listing(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(auto_paging_iter=lambda: iter([
            {**wanted, 'id': 'cs_anterior', 'metadata': {'attempt': '0'}},
            {**wanted, 'id': 'cs_ajena', 'client_reference_id': 'preregistration:ajena'}, wanted]))
    monkeypatch.setattr('infrastructure.services.stripe_service.stripe.checkout.Session.list', listing)
    assert gateway().find_preregistration_checkout(row) == wanted
    assert calls[0]['created']['gte'] > 0


def test_recovery_failure_is_not_treated_as_no_payment(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError('detalles privados')
    monkeypatch.setattr('infrastructure.services.stripe_service.stripe.checkout.Session.list', fail)
    with pytest.raises(RuntimeError, match='reconciliar') as caught:
        gateway().find_preregistration_checkout(registration())
    assert 'privados' not in str(caught.value)
