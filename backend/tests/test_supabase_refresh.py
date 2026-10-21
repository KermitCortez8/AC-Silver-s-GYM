import threading

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import Settings
from routes.auth_routes import router as auth_router
from routes.attendance_routes import router as attendance_router
from routes.clients_routes import router as clients_router
from routes.gym_routes import router as gym_router
from routes.users_routes import router as users_router
from services.supabase_gym_service import SupabaseGymService
from utils.security import create_local_token


def service_with_remote(remote):
    service = object.__new__(SupabaseGymService)
    service.supabase = remote
    service.lock = threading.Lock()
    service.remote_columns = {}
    service.missing_remote_tables = set()
    service.state = service._seed()
    service._last_refresh_at = 0
    service._resource_refreshed_at = {}
    return service


def test_remote_reads_overlap_without_exceeding_six_connections():
    barrier = threading.Barrier(6)
    lock = threading.Lock()
    counts = {'started': 0, 'active': 0, 'peak': 0}

    class Remote:
        def select(self, table, order=None):
            with lock:
                counts['started'] += 1
                counts['active'] += 1
                position = counts['started']
                counts['peak'] = max(counts['peak'], counts['active'])
            try:
                if position <= 6:
                    barrier.wait(timeout=3)
                return []
            finally:
                with lock:
                    counts['active'] -= 1
        select_all = select

    service = service_with_remote(Remote())
    service.ensure_fresh()
    assert counts['started'] == 18
    assert counts['peak'] == 6
    assert service._last_refresh_at > 0


def test_required_remote_failure_preserves_previous_state_and_refresh_time():
    class Remote:
        def select(self, table, order=None):
            if table == 'USUARIO':
                raise RuntimeError('Supabase unavailable')
            return []
        select_all = select
    service = service_with_remote(Remote())
    original = service.state
    original['clientes'] = [{'id_cliente': 99, 'estado': 'ACTIVO'}]
    with pytest.raises(RuntimeError, match='unavailable'):
        service.ensure_fresh()
    assert service.state is original
    assert service.state['clientes'][0]['id_cliente'] == 99
    assert service._last_refresh_at == 0


def test_optional_missing_table_still_loads_other_sections():
    class Remote:
        def select(self, table, order=None):
            if table == 'PROMOCIONES':
                raise RuntimeError('PGRST205 table missing')
            if table == 'USUARIO':
                return [{'id_usuario': 1, 'Nombres': 'Admin', 'Correo': 'admin@example.com', 'Rol': 'admin'}]
            return []
        select_all = select
    service = service_with_remote(Remote())
    service.ensure_fresh()
    assert 'PROMOCIONES' in service.missing_remote_tables
    assert len(service.state['usuario']) == 1
    assert service.state['promociones'] == []


class RecordingRemote:
    def __init__(self, rows=None):
        self.calls = []
        self.writes = []
        self.rows = rows or {}
        self.error_table = None

    def select(self, table, order=None):
        self.calls.append(table)
        if table == self.error_table:
            raise RuntimeError('Supabase unavailable')
        return self.rows.get(table, [])

    select_all = select

    def update(self, table, pk, value, body):
        self.writes.append(('update', table, value))
        for row in self.rows.get(table, []):
            if row.get(pk) == value:
                row.update(body)

    def delete(self, table, pk, value):
        self.writes.append(('delete', table, value))
        self.rows[table] = [row for row in self.rows.get(table, []) if row.get(pk) != value]

    def insert(self, table, body):
        self.writes.append(('insert', table, body.get('id_usuario')))
        self.rows.setdefault(table, []).append(body)


def test_constructing_service_validates_schema_without_loading_every_table(monkeypatch):
    checks = []
    monkeypatch.setattr('services.supabase_gym_service.SupabaseRestClient.validate_columns',
                        lambda self, table, columns: checks.append(table))
    monkeypatch.setattr('services.supabase_gym_service.SupabaseRestClient.select',
                        lambda *_args, **_kwargs: pytest.fail('Unexpected startup data query'))
    monkeypatch.setattr('services.supabase_gym_service.SupabaseRestClient.select_all',
                        lambda *_args, **_kwargs: pytest.fail('Unexpected startup data query'))
    service = SupabaseGymService('https://example.invalid', 'test')
    assert checks == ['MEMBRESIA', 'VENTAS']
    assert service._resource_refreshed_at == {}


def test_sections_load_only_needed_tables_and_preserve_other_sections(monkeypatch):
    monkeypatch.setattr('services.supabase_gym_service.time.monotonic', lambda: 100)
    remote = RecordingRemote({'USUARIO': [{'id_usuario': 1, 'Nombres': 'Admin', 'Rol': 'admin'}]})
    service = service_with_remote(remote)
    service.ensure_fresh(('usuario',))
    assert remote.calls == ['USUARIO']
    users = service.state['usuario']
    service.ensure_fresh(('clientes',))
    assert set(remote.calls) == {'USUARIO', 'CLIENTES', 'MEMBRESIA'}
    assert service.state['usuario'] is users
    service.ensure_fresh(('usuario', 'clientes'))
    assert len(remote.calls) == 3
    assert service._last_refresh_at == 0


def test_table_cache_expiration_is_independent_between_sections(monkeypatch):
    clock = [100]
    monkeypatch.setattr('services.supabase_gym_service.time.monotonic', lambda: clock[0])
    remote = RecordingRemote()
    service = service_with_remote(remote)
    service.ensure_fresh(('usuario',))
    clock[0] = 104
    service.ensure_fresh(('planes_membresia',))
    clock[0] = 106
    service.ensure_fresh(('usuario', 'planes_membresia'))
    assert remote.calls.count('USUARIO') == 2
    assert remote.calls.count('PLANES_MEMBRESIA') == 1


def test_failed_partial_refresh_keeps_data_and_can_be_retried(monkeypatch):
    monkeypatch.setattr('services.supabase_gym_service.time.monotonic', lambda: 100)
    remote = RecordingRemote()
    service = service_with_remote(remote)
    service.state['clientes'] = [{'id_cliente': 99, 'estado': 'ACTIVO'}]
    original = service.state
    remote.error_table = 'MEMBRESIA'
    with pytest.raises(RuntimeError, match='unavailable'):
        service.ensure_fresh(('clientes',))
    assert service.state is original
    assert service._resource_refreshed_at == {}
    remote.error_table = None
    service.ensure_fresh(('clientes',))
    assert service.state['clientes'] == []
    assert set(service._resource_refreshed_at) == {'clientes', 'membresia'}


def test_first_mutation_after_partial_read_loads_remaining_tables():
    remote = RecordingRemote({'CLIENTES': [{'id_cliente': 7, 'Nombres': 'Cliente'}]})
    service = service_with_remote(remote)
    service.ensure_fresh(('usuario',))
    result = service._mutate(lambda state: len(state['clientes']))
    assert result == 1
    assert 'ASISTENCIA' in remote.calls
    assert set(service._resource_refreshed_at) == set(service.READ_STATE_KEYS)


def test_order_reads_include_product_names_and_shared_inventory_stock():
    remote = RecordingRemote({
        'TIENDA_PRODUCTOS': [{'id_producto': 1, 'id_item': 2, 'nombre_Producto': 'Agua', 'precio_Venta': 3}],
        'INVENTARIO': [{'id_item': 2, 'Tipo': 'Tienda', 'Cantidad_Stock_E': 0, 'Estado': 'Agotado'}],
        'VENTAS': [{'id_venta': 10}],
        'DETALLE_VENTA': [{'id_venta': 10, 'id_producto': 1, 'Cantidad': 1}],
    })
    service = service_with_remote(remote)
    service.ensure_fresh(('pedidos_tienda',))
    assert set(remote.calls) == {'VENTAS', 'DETALLE_VENTA', 'TIENDA_PRODUCTOS', 'INVENTARIO'}
    assert service.state['pedidos_tienda'][0]['items'][0]['nombre_producto'] == 'Agua'
    assert service.state['productos_tienda'][0]['estado'] == 'Agotado'


@pytest.fixture
def scoped_api(monkeypatch):
    settings = Settings(supabase_url='https://example.invalid', supabase_key='test', auth_secret_key='x' * 48)
    monkeypatch.setattr('dependencies.get_settings', lambda: settings)
    monkeypatch.setattr('utils.security.get_settings', lambda: settings)
    remote = RecordingRemote({
        'USUARIO': [{'id_usuario': 1, 'Nombre': 'Admin', 'Correo': 'admin@example.com', 'Rol': 'admin'}],
        'CLIENTES': [{'id_cliente': 7, 'Nombres': 'Cliente', 'Estado': True}],
    })
    service = service_with_remote(remote)
    monkeypatch.setattr('dependencies._get_supabase_gym_service', lambda *_args: service)
    app = FastAPI()
    for router in (auth_router, attendance_router, clients_router, gym_router, users_router):
        app.include_router(router, prefix='/api')
    token = create_local_token({'id': 'SGADM001', 'role': 'admin'})
    return TestClient(app, headers={'Authorization': f'Bearer {token}'}), remote, service


def test_admin_navigation_reuses_account_cache_without_loading_unrelated_modules(scoped_api):
    client, remote, service = scoped_api
    response = client.get('/api/auth/me')
    assert response.status_code == 200
    assert response.json()['role'] == 'admin'
    assert remote.calls == ['USUARIO']
    response = client.get('/api/clientes')
    assert response.status_code == 200
    assert response.json()[0]['id_cliente'] == 7
    assert set(remote.calls) == {'USUARIO', 'CLIENTES', 'MEMBRESIA'}
    assert len(remote.calls) == 3
    assert client.get('/api/gym/configuracion').status_code == 200
    assert remote.calls[-1] == 'CONFIGURACION_GIMNASIO'
    assert client.get('/api/usuarios').status_code == 200
    assert len(remote.calls) == 4
    assert service.state['clientes'][0]['id_cliente'] == 7


def test_cached_account_role_changes_still_revoke_admin_access(scoped_api):
    client, remote, service = scoped_api
    assert client.get('/api/clientes').status_code == 200
    remote.rows['USUARIO'][0]['Rol'] = 'trainer'
    service._resource_refreshed_at['usuario'] = 0
    assert client.get('/api/clientes').status_code in {401, 403}
    assert remote.calls.count('USUARIO') == 2
    assert remote.calls.count('CLIENTES') == 1


def test_unknown_reads_and_writes_keep_full_validation():
    from starlette.requests import Request
    from dependencies import _resources_for_request

    for method, path in [('POST', '/api/clientes'), ('GET', '/api/future-module')]:
        request = Request({'type': 'http', 'method': method, 'path': path, 'headers': []})
        assert _resources_for_request(request) is None


def test_health_check_does_not_refresh_admin_histories():
    from starlette.requests import Request
    from dependencies import _resources_for_request

    for path in ('/health', '/api/health'):
        request = Request({'type': 'http', 'method': 'GET', 'path': path, 'headers': []})
        resources = _resources_for_request(request)
        remote = RecordingRemote()
        service = service_with_remote(remote)
        service.ensure_fresh(resources)
        assert remote.calls == ['PLANES_MEMBRESIA']


def test_attendance_history_loads_clients_without_loading_store_or_schedules(scoped_api):
    client, remote, _service = scoped_api
    response = client.get('/api/asistencia/historial')
    assert response.status_code == 200
    assert response.json()['items'] == []
    assert set(remote.calls) == {'USUARIO', 'CLIENTES', 'MEMBRESIA', 'ASISTENCIA'}


def test_normalized_client_list_keeps_latest_membership_from_unsorted_history():
    remote = RecordingRemote({
        'CLIENTES': [{'id_cliente': 7, 'Nombres': 'Cliente', 'Estado': False}],
        'MEMBRESIA': [
            {'id_membresia': 8, 'id_cliente': 7, 'Estado': 'EN_TRAMITE', 'monto_pago': 90},
            {'id_membresia': 4, 'id_cliente': 7, 'Estado': 'EN_TRAMITE', 'monto_pago': 50},
            {'id_membresia': 15, 'id_cliente': 8, 'Estado': 'EN_TRAMITE', 'monto_pago': 120},
        ],
    })
    service = service_with_remote(remote)
    service.ensure_fresh(('clientes',))
    result = service.clientes_normalized()
    assert result[0]['id_membresia'] == 8
    assert result[0]['monto_pago'] == 90


def test_saving_and_deleting_users_does_not_load_other_sections(scoped_api):
    client, remote, service = scoped_api
    remote.rows['USUARIO'].append({'id_usuario': 2, 'Nombre': 'Trainer', 'Rol': 'trainer'})
    response = client.post('/api/usuarios', json={
        'id_usuario': 'SGADM001', 'nombre': 'Admin actualizado', 'correo': 'admin@example.com', 'rol': 'admin',
    })
    assert response.status_code == 200
    assert response.json()['nombre'] == 'Admin actualizado'
    assert remote.calls == ['USUARIO']
    assert remote.writes == [('update', 'USUARIO', 1)]
    assert client.delete('/api/usuarios/SGTRA002').status_code == 204
    assert remote.calls == ['USUARIO']
    assert remote.writes[-1] == ('delete', 'USUARIO', 2)
    assert service._last_refresh_at == 0
    assert [user['id_usuario'] for user in service.state['usuario']] == ['SGADM001']


def test_user_mutations_do_not_copy_unrelated_cached_histories():
    class UnrelatedHistory:
        def __deepcopy__(self, _memo):
            pytest.fail('A user mutation copied attendance history')

    remote = RecordingRemote({'USUARIO': [{'id_usuario': 1, 'Nombre': 'Admin', 'Rol': 'admin'}]})
    service = service_with_remote(remote)
    history = [UnrelatedHistory()]
    service.state['asistencia'] = history
    service.upsert_usuario({'id_usuario': 'SGADM001', 'nombre': 'Admin', 'rol': 'admin'})
    assert remote.calls == ['USUARIO']
    assert service.state['asistencia'] is history


def test_failed_user_update_restores_account_without_discarding_other_sections():
    remote = RecordingRemote({'USUARIO': [{'id_usuario': 1, 'Nombre': 'Admin', 'Rol': 'admin'}]})
    service = service_with_remote(remote)
    service.ensure_fresh(('usuario',))
    history = [{'id_asistencia': 50}]
    service.state['asistencia'] = history

    def fail(*_args):
        raise RuntimeError('Update failed')

    remote.update = fail
    with pytest.raises(RuntimeError, match='Update failed'):
        service.upsert_usuario({'id_usuario': 'SGADM001', 'nombre': 'Otro nombre', 'rol': 'admin'})
    assert service.state['usuario'][0]['nombre'] == 'Admin'
    assert service.state['asistencia'] is history
    assert service._resource_refreshed_at == {}
