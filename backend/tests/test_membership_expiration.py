from copy import deepcopy
from datetime import datetime, timezone
import threading
import time

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from dependencies import get_current_user, get_gym_service
from routes.auth_routes import router as auth_router
from services.auth_service import AuthService, ClientMembershipExpired, ClientMembershipRequired
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService
from services.membership_lifecycle import apply_membership_expiration
from services.supabase_gym_service import SupabaseGymService
import services.gym_domain_service as domain


@pytest.fixture
def gym(monkeypatch):
    for module in ('gym_domain_service', 'auth_service', 'clients_service', 'supabase_gym_service'):
        monkeypatch.setattr(f'services.{module}._today_iso', lambda: '2026-10-01')
    service = LocalGymService()
    result = ClientsService(service).register_admin_client({
        'nombre': 'Cliente Vigente', 'correo': 'cliente@example.com', 'dni': '12345678',
        'password': 'secreto123', 'plan': 'MENSUAL',
    })
    client_id = result['cliente']['id_cliente']
    service.confirmar_pago_manual_cliente(client_id)
    service.activar_membresia_cliente(client_id)
    membership = service.state['membresia'][0]
    membership.update(fecha_inicio='2026-09-01', fecha_fin='2026-10-01')
    return service


def expire(gym):
    gym.state['membresia'][0]['fecha_fin'] = '2026-09-30'


def api(gym):
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_gym_service] = lambda: gym

    @app.get('/private')
    def private(user=Depends(get_current_user)):
        return {'id': user.id}

    return TestClient(app)


def test_access_includes_last_day_and_expiration_preserves_payment_history(gym, monkeypatch):
    service = AuthService(gym)
    account = gym.state['clientes'][0]
    service.session_for_client(account)
    original = deepcopy(gym.state['membresia'][0])
    monkeypatch.setattr('services.gym_domain_service._today_iso', lambda: '2026-10-02')
    monkeypatch.setattr('services.auth_service._today_iso', lambda: '2026-10-02')
    with pytest.raises(ClientMembershipExpired):
        service.session_for_client(account)
    assert account['estado'] == 'VENCIDA'
    assert gym.state['membresia'][0] == {**original, 'estado': 'VENCIDA'}
    assert gym.expire_memberships() is False


@pytest.mark.parametrize('instant, expected', [
    ('2026-10-02T04:59:59+00:00', '2026-10-01'),
    ('2026-10-02T05:00:00+00:00', '2026-10-02'),
])
def test_date_boundary_uses_peru_midnight(monkeypatch, instant, expected):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(instant).astimezone(tz or timezone.utc)
    monkeypatch.setattr(domain, 'datetime', Clock)
    assert domain._today_iso() == expected


def test_expired_password_login_and_existing_signed_token_are_blocked(gym):
    client = api(gym)
    login = client.post('/auth/password', json={'correo': 'cliente@example.com', 'password': 'secreto123'})
    assert login.status_code == 200
    headers = {'Authorization': f"Bearer {login.json()['token']}"}
    assert client.get('/private', headers=headers).status_code == 200
    expire(gym)
    for response in (
        client.get('/auth/me', headers=headers),
        client.get('/private', headers=headers),
        client.post('/auth/password', json={'correo': 'cliente@example.com', 'password': 'secreto123'}),
    ):
        assert response.status_code == 403
        assert response.json()['detail']['code'] == 'membership_expired'
    assert gym.state['clientes'][0]['estado'] == 'VENCIDA'


def test_linked_google_login_is_blocked_after_expiration(gym, monkeypatch):
    account = gym.state['clientes'][0]
    account['google_sub'] = 'google-client'
    monkeypatch.setattr('services.auth_service.verify_google_credential', lambda _: {
        'sub': 'google-client', 'email': 'cliente@example.com', 'name': 'Cliente',
    })
    expire(gym)
    response = api(gym).post('/auth/google', json={'credential': 'signed-google-token'})
    assert response.status_code == 403
    assert response.json()['detail']['code'] == 'membership_expired'


@pytest.mark.parametrize('changes', [
    {'fecha_inicio': '2026-10-02'},
    {'fecha_fin': ''},
    {'fecha_fin': 'no-es-una-fecha'},
    {'estado_pago': 'PENDIENTE'},
])
def test_active_flag_alone_does_not_allow_missing_unpaid_or_future_membership(gym, changes):
    gym.state['membresia'][0].update(changes)
    with pytest.raises(ClientMembershipRequired):
        AuthService(gym).session_for_client(gym.state['clientes'][0])


def test_pending_registration_with_placeholder_dates_does_not_expire(gym):
    gym.state['clientes'][0]['estado'] = 'PENDIENTE_PAGO'
    gym.state['membresia'][0].update(estado='PENDIENTE_PAGO', estado_pago='PENDIENTE', fecha_fin='2020-01-01')
    assert gym.expire_memberships() is False
    assert gym.state['clientes'][0]['estado'] == 'PENDIENTE_PAGO'


def test_current_paid_renewal_preserves_access_and_expires_only_old_membership(gym):
    previous = deepcopy(gym.state['membresia'][0])
    previous.update(id_membresia=0, estado='ACTIVO', fecha_fin='2026-09-01')
    gym.state['membresia'].append(previous)
    assert gym.expire_memberships() is True
    assert previous['estado'] == 'VENCIDA'
    assert gym.state['clientes'][0]['estado'] == 'ACTIVO'
    AuthService(gym).session_for_client(gym.state['clientes'][0])


def test_expired_membership_cannot_be_reactivated_or_extended_through_edit(gym):
    expire(gym)
    with pytest.raises(ValueError, match='vencida'):
        gym.activar_membresia_cliente(gym.state['clientes'][0]['id_cliente'])
    with pytest.raises(ValueError, match='vencida'):
        ClientsService(gym).upsert_client({**gym.state['clientes'][0], 'estado': 'ACTIVO'})
    assert len(gym.state['membresia']) == 1
    assert gym.state['membresia'][0]['fecha_fin'] == '2026-09-30'


def test_duplicate_stripe_payment_cannot_unblock_expired_account(gym):
    membership = gym.state['membresia'][0]
    membership.update(metodo_pago='stripe', referencia_pago='cs_paid_original')
    expire(gym)
    gym.expire_memberships()
    gym.confirmar_pago_cliente_publico(membership['id_cliente'], {
        'id_membresia': membership['id_membresia'], 'monto_pago': membership['monto_pago'],
        'referencia_pago': 'cs_paid_original', 'metodo_pago': 'stripe',
    })
    assert membership['estado'] == 'VENCIDA'
    assert gym.state['clientes'][0]['estado'] == 'VENCIDA'


def test_new_paid_membership_can_restore_access_after_admin_activation(gym):
    expire(gym)
    gym.expire_memberships()
    old = gym.state['membresia'][0]
    gym.crear_membresia({'id_cliente': old['id_cliente'], 'id_pm': old['id_pm'], 'estado': 'PENDIENTE_PAGO'})
    gym.confirmar_pago_manual_cliente(old['id_cliente'])
    with pytest.raises(ClientMembershipExpired):
        AuthService(gym).session_for_client(gym.state['clientes'][0])
    gym.activar_membresia_cliente(old['id_cliente'])
    AuthService(gym).session_for_client(gym.state['clientes'][0])
    assert gym.state['clientes'][0]['estado'] == 'ACTIVO'
    assert old['estado'] == 'VENCIDA'
    assert old['fecha_fin'] == '2026-09-30'


def test_no_change_expiration_does_not_write_or_extend_refresh_ttl(gym, monkeypatch):
    def unexpected_write(_fn):
        pytest.fail('La comprobación de vigencia no debe escribir sin cambios')
    monkeypatch.setattr(gym, '_mutate', unexpected_write)
    assert gym.expire_memberships() is False


def test_supabase_expiration_persists_membership_and_boolean_account_block(gym):
    expire(gym)
    writes = []

    class Remote:
        def validate_columns(self, *_args):
            pass
        def update(self, table, pk, id_value, body):
            writes.append((table, body))
        def select(self, table, order=None):
            return self.select_all(table, order)
        def select_all(self, table, order=None):
            if table == 'CLIENTES':
                return [service._client_to_remote(service.state['clientes'][0])]
            if table == 'MEMBRESIA':
                return [service._membership_to_remote(service.state['membresia'][0])]
            return []

    service = object.__new__(SupabaseGymService)
    service.lock = threading.Lock()
    service.state = deepcopy(gym.state)
    service.supabase = Remote()
    service.remote_columns = {}
    service.missing_remote_tables = set()
    service._last_refresh_at = time.monotonic()
    service.ensure_fresh()
    assert [table for table, _ in writes] == ['MEMBRESIA', 'CLIENTES']
    assert writes[0][1]['Estado'] == 'VENCIDA'
    assert writes[0][1]['estado_pago'] == 'PAGADO'
    assert writes[1][1]['Estado'] is False
    assert service.clientes_normalized()[0]['estado'] == 'VENCIDA'
    service.ensure_fresh()
    assert len(writes) == 2
    # Un nuevo refresco remoto recupera VENCIDA sin PATCH redundantes.
    service._last_refresh_at = 0
    service.ensure_fresh()
    assert service.state['clientes'][0]['estado'] == 'VENCIDA'
    assert len(writes) == 2


def test_inactive_supabase_account_is_exposed_as_expired_after_reload(gym):
    mapper = object.__new__(SupabaseGymService)
    client = mapper._map_client({'id_cliente': 1, 'Estado': False})
    membership = mapper._map_membership({
        'id_cliente': 1, 'Estado': 'Vencida', 'Fecha_Fin': '2026-09-30', 'estado_pago': 'PAGADO',
    })
    state = {'clientes': [client], 'membresia': [membership]}
    assert apply_membership_expiration(state, '2026-10-01') is True
    assert client['estado'] == 'VENCIDA'


def test_internal_staff_account_does_not_require_a_membership(gym):
    gym.state['usuario'].append({
        'id_usuario': 'SGADM999', 'rol': 'admin', 'nombre': 'Admin', 'correo': 'admin@example.com',
    })
    profile = AuthService(gym).user_from_payload({'sub': 'SGADM999'})
    assert profile.role == 'admin'
