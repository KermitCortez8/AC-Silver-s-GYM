"""Regresiones de permisos, identidades, mapeos, dinero, duración e IO."""
import asyncio
from datetime import datetime, timezone
import threading
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.services.gym_service import GymService
from domain.money import cents, discounted_price, order_totals
from domain.services import gym_values
from infrastructure.config import Settings
from infrastructure.authentication import SignedSessionProvider
from infrastructure.repositories.gym_repository import SupabaseGymRepository
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from infrastructure.security import create_local_token
from presentation.dependencies import get_gym_service, get_store_images_service
from presentation.routes import inventory_routes, memberships_routes, store_routes, clients_routes


class Passwords:
    def hash(self, value):
        return 'test:' + value

    def verify(self, value, encoded):
        return encoded == self.hash(value)


@pytest.fixture
def protected_api(monkeypatch):
    monkeypatch.setattr('infrastructure.security.get_settings', lambda: Settings(auth_secret_key='local-tests-only-' * 3))
    service = GymService(MemoryGymRepository(), Passwords(), sessions=SignedSessionProvider())
    state = service.repository.state
    state['usuario'] = [dict(id_usuario=f'SG{prefix}{i:03}', rol=role, nombre=role, correo=role+'@example.com', estado='ACTIVO')
                        for i, (prefix, role) in enumerate([('ADM', 'admin'), ('STA', 'staff'), ('TRA', 'trainer')], 1)]
    state['clientes'] = [dict(id_cliente=i, id_usuario=f'SGCLI{i:03}', nombre='Cliente', correo=f'client{i}@example.com',
                              estado='ACTIVO', telefono='', dni=str(i), plan='MENSUAL', promocion='SIN PROMOCION') for i in (10, 11)]
    state['membresia'] = [dict(id_membresia=i, id_cliente=i, id_pm=1, estado='ACTIVO', estado_pago='PAGADO',
                                fecha_inicio='2020-01-01', fecha_fin='2099-01-01') for i in (10, 11)]
    state['pedidos_tienda'] = [dict(id_pedido=i, id_cliente=i, cliente_correo=f'client{i}@example.com', items=[]) for i in (10, 11)]
    app = FastAPI()
    app.dependency_overrides[get_gym_service] = lambda: service
    app.dependency_overrides[get_store_images_service] = lambda: SimpleNamespace(upload=lambda *args: {})
    for router in (inventory_routes.router, store_routes.router, memberships_routes.router):
        app.include_router(router, prefix='/api')
    def headers(role):
        identity = {'admin': 'SGADM001', 'staff': 'SGSTA002', 'trainer': 'SGTRA003', 'user': 'SGCLI010'}[role]
        profile = {'id': identity, 'role': role}
        if role == 'user':
            profile['id_cliente'] = 10
        return {'Authorization': 'Bearer ' + create_local_token(profile)}
    return TestClient(app), service, headers


WRITES = [
    ('POST', '/api/inventario', {'nombre_item': 'Demo', 'tipo': 'General', 'cantidad_stock': 1}),
    ('DELETE', '/api/inventario/1', None),
    ('POST', '/api/inventario/movimientos', {'id_item': 1, 'id_usuario': 'spoof', 'tipo_movimiento': 'entrada'}),
    ('PUT', '/api/inventario/movimientos/1', {'cantidad': 2}),
    ('POST', '/api/tienda', {'nombre_producto': 'Demo', 'precio_venta': 5}),
    ('DELETE', '/api/tienda/1', None),
    ('PUT', '/api/tienda/pedidos/1', {'estado_pedido': 'ENTREGADO'}),
    ('POST', '/api/planes-membresia', {'nombre_plan': 'MENSUAL', 'duracion': '30 dias', 'precio': 79}),
    ('PUT', '/api/planes-membresia/1', {'nombre_plan': 'MENSUAL', 'duracion': '30 dias', 'precio': 79}),
    ('DELETE', '/api/planes-membresia/1', None),
    ('POST', '/api/membresias', {'id_cliente': 10, 'id_pm': 1, 'fecha_inicio': '', 'fecha_fin': ''}),
]


@pytest.mark.parametrize('method,path,payload', WRITES)
@pytest.mark.parametrize('role,status', [(None, 401), ('user', 403), ('trainer', 403)])
def test_internal_writes_require_an_authorized_role(protected_api, method, path, payload, role, status):
    client, _gym, headers = protected_api
    response = client.request(method, path, json=payload, headers=headers(role) if role else {})
    assert response.status_code == status


def test_internal_staff_can_write_and_cannot_spoof_movement_actor(protected_api):
    client, gym, headers = protected_api
    response = client.post('/api/inventario', headers=headers('staff'),
                           json={'nombre_item': 'Demo', 'tipo': 'General', 'cantidad_stock': 1})
    assert response.status_code == 200
    item = response.json()
    response = client.post('/api/inventario/movimientos', headers=headers('staff'), json={
        'id_item': item['id_item'], 'id_usuario': 'SGADM001', 'tipo_movimiento': 'entrada', 'cantidad': 2,
    })
    assert response.status_code == 200
    assert gym.movimientos_inventario()[0]['id_usuario'] == 'SGSTA002'


def test_orders_and_memberships_are_private_and_filtered(protected_api):
    client, _gym, headers = protected_api
    assert client.get('/api/tienda/pedidos').status_code == 401
    assert [r['id_cliente'] for r in client.get('/api/tienda/pedidos', headers=headers('user')).json()] == [10]
    assert len(client.get('/api/tienda/pedidos', headers=headers('admin')).json()) == 2
    assert [r['id_cliente'] for r in client.get('/api/membresias', headers=headers('user')).json()] == [10]
    assert client.get('/api/clientes/11/membresias', headers=headers('user')).status_code == 403
    assert client.get('/api/planes-membresia').status_code == 200
    assert client.get('/api/tienda').status_code == 200


def test_image_upload_requires_staff_but_listing_remains_public(protected_api):
    client, _gym, headers = protected_api
    for role, status in [(None, 401), ('user', 403)]:
        response = client.post('/api/tienda/imagenes', headers=headers(role) if role else {},
                               files={'file': ('x.png', b'image', 'image/png')})
        assert response.status_code == status


def test_user_identity_is_unique_across_roles_and_stable_after_role_change(monkeypatch):
    gym = GymService(MemoryGymRepository(), Passwords())
    users = [gym.upsert_usuario({'nombre': role, 'correo': role+'@gmail.com', 'rol': role, 'password': 'secret123'})
             for role in ('admin', 'trainer', 'staff')]
    assert [u['id_usuario'] for u in users] == ['SGADM001', 'SGTRA002', 'SGSTA003']
    updated = gym.upsert_usuario({**users[0], 'rol': 'trainer'})
    assert updated['id_usuario'] == 'SGADM001'
    monkeypatch.setattr('infrastructure.supabase_client.SupabaseRestClient.validate_columns', lambda *_args: None)
    mapper = SupabaseGymRepository('https://example.invalid', 'unused')
    assert len({mapper._user_to_remote(u)['id_usuario'] for u in users}) == 3
    assert mapper._map_user(mapper._user_to_remote(updated))['id_usuario'] == 'SGADM001'


@pytest.mark.parametrize('entity,payload,fields', [
    ('promotion', {'id_promocion': 1, 'limite_cupos': 4, 'usos_actuales': 2, 'icono_etiqueta': 'x', 'palabra_clave': 'FLASH'},
     ['limite_cupos', 'usos_actuales', 'icono_etiqueta', 'palabra_clave']),
    ('membership', {'id_membresia': 1, 'id_promocion': 4}, ['id_promocion']),
    ('inventory', {'id_item': 1, 'unidad_venta': 'pack', 'precio_venta': 12.5, 'stock_minimo': 7, 'ubicacion': 'Sala A', 'observaciones': 'nota'},
     ['unidad_venta', 'precio_venta', 'stock_minimo', 'ubicacion', 'observaciones']),
    ('product', {'id_producto': 1, 'descripcion': 'texto', 'unidad_venta': 'pack', 'stock_minimo': 0},
     ['descripcion', 'unidad_venta', 'stock_minimo']),
])
def test_business_fields_survive_round_trip(monkeypatch, entity, payload, fields):
    monkeypatch.setattr('infrastructure.supabase_client.SupabaseRestClient.validate_columns', lambda *_args: None)
    mapper = SupabaseGymRepository('https://example.invalid', 'unused')
    remote = getattr(mapper, f'_{entity}_to_remote')(payload)
    local = getattr(mapper, f'_map_{entity}')(remote)
    assert {k: local[k] for k in fields} == {k: payload[k] for k in fields}


@pytest.mark.parametrize('price,discount,kind,expected', [(79, 10, 'porcentaje', 71.10), (0.05, 10, 'porcentaje', 0.04),
    (10.05, 2.345, 'monto', 7.70), (79, 90, 'monto', 0)])
def test_money_uses_cents_and_half_up(price, discount, kind, expected):
    assert discounted_price(price, discount, kind) == expected
    assert cents('1.005') == 101
    assert order_totals(25) == {'subtotal': 0.25, 'igv': 0.05, 'total': 0.30}


def test_activation_uses_configured_duration_and_stays_idempotent():
    gym = GymService(MemoryGymRepository(), Passwords())
    gym.upsert_plan_membresia({'id_pm': 1, 'nombre_plan': 'MENSUAL', 'duracion': '45 dias', 'precio': 79})
    saved = gym.registrar_cliente_publico({'nombre': 'Demo', 'correo': 'demo@gmail.com', 'dni': '12345678',
                                         'password': 'secret123', 'telefono': '987654321', 'plan': 'MENSUAL'})
    identity = saved['cliente']['id_cliente']
    gym.confirmar_pago_manual_cliente(identity)
    first = gym.activar_membresia_cliente(identity)['membresia']
    assert (datetime.fromisoformat(first['fecha_fin']) - datetime.fromisoformat(first['fecha_inicio'])).days == 45
    assert gym.activar_membresia_cliente(identity)['membresia'] == first


def test_domain_date_and_time_use_lima(monkeypatch):
    instant = datetime.fromisoformat('2026-10-23T01:30:00+00:00')
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz or timezone.utc)
    monkeypatch.setattr(gym_values, 'datetime', Clock)
    assert gym_values._today_iso() == '2026-10-22'
    assert gym_values._now_time() == '20:30'


def test_stripe_webhook_does_not_block_the_event_loop(monkeypatch):
    started, release = threading.Event(), threading.Event()
    def blocking(*_args):
        started.set()
        return {'received': release.wait(2)}
    from types import SimpleNamespace
    payments = SimpleNamespace(process_webhook=blocking)
    class Request:
        async def body(self):
            return b'synthetic'
    async def run():
        task = asyncio.create_task(clients_routes.stripe_webhook(Request(), '', payments))
        async def ticker():
            while not started.is_set():
                await asyncio.sleep(0)
            release.set()
        await asyncio.wait_for(ticker(), timeout=1)
        assert await task == {'received': True}
    asyncio.run(run())


def test_missing_transaction_rpc_never_falls_back_to_partial_rest_writes(monkeypatch):
    from tests.atomic_fake import AtomicFakeMixin
    class MissingRPC(AtomicFakeMixin):
        def __init__(self):
            self.rows = {}
            self.writes = []
        def validate_columns(self, *_args):
            pass
        def select_all(self, table, order=None):
            return self.rows.get(table, [])
        def rpc(self, name, body):
            if name == 'commit_gym_transaction':
                raise RuntimeError('Supabase: {"code":"PGRST202"}')
            return super().rpc(name, body)
        def insert(self, *_args):
            pytest.fail('No se permite un fallback REST')
        update = delete = insert
    database = MissingRPC()
    monkeypatch.setattr('infrastructure.repositories.gym_repository.SupabaseRestClient', lambda *_args: database)
    gym = GymService(SupabaseGymRepository('local', 'unused'), Passwords())
    with pytest.raises(RuntimeError, match='015_atomic_gym_transactions.sql'):
        gym.upsert_usuario({'nombre': 'Ana', 'correo': 'ana@gmail.com', 'rol': 'staff', 'password': 'secret123'})
    assert gym.usuarios() == []
    assert database.writes == []


@pytest.mark.parametrize('entity,expected', [('inventory', 1), ('product', 5)])
def test_nullable_legacy_stock_threshold_still_uses_its_default(monkeypatch, entity, expected):
    monkeypatch.setattr('infrastructure.supabase_client.SupabaseRestClient.validate_columns', lambda *_args: None)
    mapper = SupabaseGymRepository('https://example.invalid', 'unused')
    assert getattr(mapper, f'_map_{entity}')({'stock_minimo': None})['stock_minimo'] == expected
    assert getattr(mapper, f'_map_{entity}')({'stock_minimo': 0})['stock_minimo'] == 0
