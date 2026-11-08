"""Transacciones y concurrencia reales en PostgreSQL desechable explícito."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from application.services.client_payments_service import ClientPaymentsService
from application.services.clients_service import ClientsService
from tests.test_atomic_transactions_postgres import CONTAINER, database, clear, service
from tests.test_public_preregistrations import PAYLOAD, Gateway, paid

pytestmark = pytest.mark.skipif(not CONTAINER, reason='Requiere un PostgreSQL desechable explícito')


def setup(database, monkeypatch):
    gym = service(database, monkeypatch)
    gym.upsert_plan_membresia(dict(nombre_plan='MENSUAL', precio=79, duracion='30 días', activo=True))
    gateway = Gateway()
    payments = payments_for(gym, gateway)
    return gym, gateway, payments


def payments_for(gym, gateway):
    return ClientPaymentsService(ClientsService(gym), gym,
        SimpleNamespace(has_supabase_credentials=True, stripe_mode='test'),
        gateway_factory=lambda _: gateway, notify=Mock(return_value={'status': 'simulada'}))


def test_real_public_registration_is_private_and_does_not_insert_customers(database, monkeypatch):
    gym, gateway, payments = setup(database, monkeypatch)
    first = payments.register_public(PAYLOAD)
    retry = payments.register_public(PAYLOAD)
    assert first == retry
    assert database.rows('CLIENTES') == database.rows('MEMBRESIA') == []
    rows = database.rows('PREREGISTROS_MEMBRESIA')
    assert len(rows) == 1 and rows[0]['estado'] == 'PENDIENTE'
    for role in ('anon', 'authenticated'):
        with pytest.raises(RuntimeError, match='permission denied'):
            database.sql(f'set role {role}; select * from public."PREREGISTROS_MEMBRESIA";')
        with pytest.raises(RuntimeError, match='permission denied'):
            database.sql(f"set role {role}; select public.commit_gym_transaction('{{\"PREREGISTROS_MEMBRESIA\":[]}}', '[]');")


def test_conversion_is_atomic_and_retryable_after_a_database_failure(database, monkeypatch):
    gym, gateway, payments = setup(database, monkeypatch)
    result = payments.register_public(PAYLOAD)
    sid = paid(gateway, result)
    database.sql('''create function public.reject_preregistration_conversion() returns trigger language plpgsql as $$
        begin raise exception 'conversion rejected for isolated test'; end $$;
        create trigger reject_preregistration_conversion before insert on public."MEMBRESIA"
        for each row execute function public.reject_preregistration_conversion();''')
    before = database.rows('PREREGISTROS_MEMBRESIA')
    try:
        with pytest.raises(RuntimeError, match='conversion rejected'):
            payments.confirm_return(sid)
        assert database.rows('CLIENTES') == database.rows('MEMBRESIA') == []
        assert database.rows('PREREGISTROS_MEMBRESIA') == before
        assert gym.repository.state['clientes'] == gym.repository.state['membresia'] == []
    finally:
        database.sql('''drop trigger reject_preregistration_conversion on public."MEMBRESIA";
                        drop function public.reject_preregistration_conversion();''')
    confirmed = payments.confirm_return(sid)
    payments.confirm_return(sid)
    assert confirmed['confirmed']
    assert len(database.rows('CLIENTES')) == len(database.rows('MEMBRESIA')) == 1
    assert database.rows('MEMBRESIA')[0]['estado_pago'] == 'PAGADO'
    assert database.rows('PREREGISTROS_MEMBRESIA')[0]['estado'] == 'CONVERTIDO'


def test_two_servers_confirm_the_same_checkout_without_duplicate_customers(database, monkeypatch):
    first, gateway, payments = setup(database, monkeypatch)
    result = payments.register_public(PAYLOAD)
    second = service(database, monkeypatch)
    second_payments = payments_for(second, gateway)
    second.ensure_fresh()
    sid = paid(gateway, result)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(p.confirm_return, sid) for p in (payments, second_payments)]
        confirmations = [f.result() for f in futures]
    assert all(c['confirmed'] for c in confirmations)
    assert confirmations[0]['id_cliente'] == confirmations[1]['id_cliente']
    assert len(database.rows('CLIENTES')) == len(database.rows('MEMBRESIA')) == 1


def test_two_servers_prepare_same_identity_without_duplicate_requests(database, monkeypatch):
    first, gateway, payments = setup(database, monkeypatch)
    second = service(database, monkeypatch)
    second_payments = payments_for(second, gateway)
    second.ensure_fresh()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(p.register_public, PAYLOAD) for p in (payments, second_payments)]
        requests = [f.result() for f in futures]
    assert requests[0]['preregistro']['token'] == requests[1]['preregistro']['token']
    assert len(database.rows('PREREGISTROS_MEMBRESIA')) == 1
    assert database.rows('CLIENTES') == []


def test_expiry_and_payment_reconciliation_never_delete_a_paid_customer(database, monkeypatch):
    gym, gateway, payments = setup(database, monkeypatch)
    result = payments.register_public(PAYLOAD)
    sid = paid(gateway, result)
    payments.archive_due_preregistrations('2099-01-01T00:00:00+00:00')
    assert len(database.rows('CLIENTES')) == len(database.rows('MEMBRESIA')) == 1
    assert database.rows('PREREGISTROS_MEMBRESIA')[0]['estado'] == 'CONVERTIDO'
    assert payments.confirm_return(sid)['confirmed']
