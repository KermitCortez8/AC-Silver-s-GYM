import threading

import pytest

from services.supabase_gym_service import SupabaseGymService


def service_with_remote(remote):
    service = object.__new__(SupabaseGymService)
    service.supabase = remote
    service.lock = threading.Lock()
    service.remote_columns = {}
    service.missing_remote_tables = set()
    service.state = service._seed()
    service._last_refresh_at = 0
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
