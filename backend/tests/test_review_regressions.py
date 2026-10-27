"""Regresiones de los seis problemas de la revisión posterior al refactor."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.services.auth_service import AuthService
from application.services.gym_service import GymService
from domain.models.auth import AuthGoogleRequest, AuthPasswordRequest, UserProfile
from domain.services.gym_domain_service import GymDomainService
from infrastructure.authentication import SignedSessionProvider
from infrastructure.config import Settings
from infrastructure.repositories.mappers import accounts, store
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from presentation.dependencies import get_gym_service, require_internal_viewer
from presentation.routes.auth_routes import router as auth_router
from presentation.routes.trainer_routes import router as trainer_router
from presentation.routes.users_routes import router as users_router
from tests.test_priority_fixes import Passwords


@pytest.fixture
def gym(monkeypatch):
    monkeypatch.setattr('infrastructure.security.get_settings', lambda: Settings(auth_secret_key='review-tests-only-' * 3))
    return GymService(MemoryGymRepository(), Passwords(), sessions=SignedSessionProvider())


def internal_account(state='ACTIVO'):
    return dict(id_usuario='SGADM001', rol='admin', nombre='Admin', correo='admin@example.com',
                estado=state, password_hash='test:secret123', google_sub='google-admin')


@pytest.mark.parametrize('state', ['INACTIVO', False, '', None])
def test_inactive_internal_accounts_cannot_login_or_reuse_tokens(gym, state):
    gym.repository.state['usuario'] = [internal_account(state)]
    auth = AuthService(gym)
    for authenticate in (
        lambda: auth.password_auth(AuthPasswordRequest(correo='admin@example.com', password='secret123')),
        lambda: auth.user_from_payload({'sub': 'SGADM001', 'role': 'admin'}),
    ):
        with pytest.raises(ValueError, match='inactiva'):
            authenticate()


def test_disabling_an_internal_account_revokes_an_existing_session(gym):
    gym.repository.state['usuario'] = [internal_account()]
    auth = AuthService(gym)
    assert auth.password_auth(AuthPasswordRequest(correo='admin@example.com', password='secret123')).token
    gym.repository.state['usuario'][0]['estado'] = 'INACTIVO'
    with pytest.raises(ValueError, match='inactiva'):
        auth.user_from_payload({'sub': 'SGADM001'})


def test_disabled_account_is_denied_by_login_and_protected_http_routes(gym):
    gym.repository.state['usuario'] = [internal_account()]
    app = FastAPI()
    for router in (auth_router, users_router):
        app.include_router(router)
    app.dependency_overrides[get_gym_service] = lambda: gym
    client = TestClient(app)
    payload = {'correo': 'admin@example.com', 'password': 'secret123'}
    login = client.post('/auth/password', json=payload)
    assert login.status_code == 200
    headers = {'Authorization': 'Bearer ' + login.json()['token']}
    assert client.get('/auth/me', headers=headers).status_code == 200
    gym.repository.state['usuario'][0]['estado'] = 'INACTIVO'
    assert client.post('/auth/password', json=payload).status_code == 401
    assert client.get('/auth/me', headers=headers).status_code == 401
    assert client.get('/usuarios', headers=headers).status_code == 401


@pytest.mark.parametrize('linked', [True, False])
def test_google_cannot_authenticate_or_link_an_inactive_internal_account(gym, linked):
    account = internal_account('INACTIVO')
    if not linked:
        account['google_sub'] = ''
    gym.repository.state['usuario'] = [account]
    gym.identity = SimpleNamespace(verify=lambda _: dict(sub='google-admin', email='admin@example.com'))
    with pytest.raises(ValueError, match='inactiva'):
        AuthService(gym).google_auth(AuthGoogleRequest(credential='verified-by-test', password='secret123'))
    assert gym.repository.state['usuario'][0]['google_sub'] == account['google_sub']


@pytest.mark.parametrize('linked', [True, False])
def test_google_still_authenticates_and_links_active_internal_accounts(gym, linked):
    account = internal_account()
    if not linked:
        account['google_sub'] = ''
    gym.repository.state['usuario'] = [account]
    gym.identity = SimpleNamespace(verify=lambda _: dict(sub='google-admin', email='admin@example.com'))
    session = AuthService(gym).google_auth(AuthGoogleRequest(credential='verified-by-test', password='secret123'))
    assert session.user.role == 'admin'
    assert session.token
    assert gym.repository.state['usuario'][0]['google_sub'] == 'google-admin'


@pytest.mark.parametrize('state', ['INACTIVO', False])
def test_editing_and_normalizing_an_internal_account_does_not_reactivate_it(gym, state):
    gym.repository.state['usuario'] = [internal_account(state)]
    gym.repository.state = GymDomainService(gym.repository.state, gym.passwords).normalize()
    assert gym.repository.state['usuario'][0]['estado'] == 'INACTIVO'
    saved = gym.upsert_usuario(dict(id_usuario='SGADM001', rol='admin', nombre='Admin editado', correo='admin@gmail.com'))
    assert accounts._user_to_remote(saved)['Estado'] is False


@pytest.mark.parametrize('claimed_actor', ['SGADM001', None])
def test_progress_uses_the_authenticated_trainer_even_if_the_actor_is_spoofed_or_missing(gym, claimed_actor):
    gym.repository.state.update(
        catalogo_rutina=[dict(id_rutina=1, servicio='fitness')],
        horarios_servicio=[dict(id_horario_servicio=1, servicio='fitness', id_rutina=1, activo=True)],
        matriculas_horario=[dict(id_matricula=1, id_cliente=1, id_horario_servicio=1, estado='ACTIVA')],
    )
    actor = UserProfile(id='SGTRA002', id_usuario='SGTRA002', email='trainer@example.com', name='Trainer', role='trainer')
    app = FastAPI()
    app.include_router(trainer_router)
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.dependency_overrides[require_internal_viewer] = lambda: actor
    response = TestClient(app).post('/trainer/matriculas/1/progreso', json={'id_usuario': claimed_actor})
    assert response.status_code == 200
    assert response.json()['id_usuario'] == 'SGTRA002'
    assert gym.repository.state['rutina_progreso'][0]['id_usuario'] == 'SGTRA002'


def test_client_edit_preserves_registration_date_across_normalization_and_mapping(gym, monkeypatch):
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-10-23')
    first = gym.upsert_cliente(dict(nombre='Ana', correo='ana@gmail.com', password='secret123', estado='EN_TRAMITE'))
    assert first['fecha_registro'] == '2026-10-23'
    gym.repository.state = GymDomainService(gym.repository.state, gym.passwords).normalize()
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-10-24')
    saved = gym.upsert_cliente({**first, 'nombre': 'Ana editada', 'fecha_registro': '2099-01-01'})
    reloaded = accounts._map_client(accounts._client_to_remote(saved))
    assert reloaded['nombre'] == 'Ana editada'
    assert reloaded['fecha_registro'] == '2026-10-23'


@pytest.mark.parametrize('price,quantity', [(10, 1), (0.25, 1), (1.23, 3)])
def test_order_breakdown_survives_persistence_using_its_saved_lines(gym, price, quantity):
    gym.repository.state['productos_tienda'] = [dict(id_producto=1, nombre_producto='Agua', precio_venta=price,
                                                   cantidad_stock=10, estado='Disponible')]
    order = gym.crear_pedido_tienda_pago_pendiente({'items': [{'id_producto': 1, 'cantidad': quantity}]})
    remote = store._sale_to_remote(order)
    details = [store._map_sale_detail(store._sale_detail_to_remote(order['id_pedido'], item), {1: 'Agua'})
               for item in order['items']]
    reloaded = store._map_sale(remote, details)
    assert {key: reloaded[key] for key in ('subtotal', 'igv', 'total')} == {
        key: order[key] for key in ('subtotal', 'igv', 'total')}


def test_historical_order_without_details_keeps_its_known_total():
    order = store._map_sale({'id_venta': 1, 'total_Venta': 11.80}, [])
    assert (order['subtotal'], order['igv'], order['total']) == (11.80, 0, 11.80)


def test_client_deletion_removes_enrollments_progress_and_releases_capacity(gym):
    state = gym.repository.state
    state.update(
        clientes=[dict(id_cliente=1), dict(id_cliente=2)],
        matriculas_horario=[dict(id_matricula=i, id_cliente=i, id_horario_servicio=1, estado='ACTIVA') for i in (1, 2)],
        rutina_progreso=[dict(id_progreso=i, id_matricula=i) for i in (1, 2)],
        horarios_servicio=[dict(id_horario_servicio=1, cupos=2, cupos_usados=2)],
    )
    other_progress = deepcopy(state['rutina_progreso'][1])
    gym.delete_cliente(1)
    assert [row['id_cliente'] for row in state['clientes']] == [2]
    assert [row['id_cliente'] for row in state['matriculas_horario']] == [2]
    assert state['rutina_progreso'] == [other_progress]
    assert state['horarios_servicio'][0]['cupos_usados'] == 1


def test_summary_counts_only_paid_current_memberships_with_canonical_and_legacy_states(gym, monkeypatch):
    monkeypatch.setattr('domain.services.gym_domain_service._today_iso', lambda: '2026-10-23')
    baseline = dict(estado='ACTIVO', estado_pago='PAGADO', fecha_inicio='2026-10-01', fecha_fin='2026-10-23')
    variants = [{}, {'estado': 'ACTIVA'}, {'estado_pago': 'PENDIENTE'}, {'fecha_fin': '2026-10-22'},
                {'fecha_inicio': '2026-10-24', 'fecha_fin': '2026-11-24'}, {'estado': 'EN_TRAMITE'}]
    gym.repository.state['membresia'] = [dict(baseline, id_membresia=i, id_cliente=i, **variant)
                                         for i, variant in enumerate(variants, 1)]
    assert gym.summary()['stats']['membresias_activas'] == 2
