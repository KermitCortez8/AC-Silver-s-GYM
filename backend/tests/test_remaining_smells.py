"""Contratos de aislamiento y coste acotado de las operaciones refactorizadas."""
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from application.services.attendance_service import AttendanceService, LIMA
from application.services.gym_service import GymService
from infrastructure.repositories.attendance_history_repository import AttendanceHistoryRepository
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from tests.test_priority_fixes import Passwords
from tests.test_supabase_refresh import RecordingRemote, service_with_remote


def test_routine_write_ignores_unrelated_attendance_failures_and_compares_only_catalog():
    class Remote(RecordingRemote):
        expected = None
        def rpc(self, name, body):
            if name == 'commit_gym_transaction':
                self.expected = set(body['p_expected'])
            return super().rpc(name, body)
    remote = Remote()
    remote.error_table = 'ASISTENCIA'
    gym = service_with_remote(remote)
    saved = gym.upsert_rutina(dict(nombre_rutina='Fuerza', servicio='fitness', zonas_musculares='Pierna'))
    assert saved['id_rutina'] == 1
    assert set(remote.calls) == {'CATALOGO_RUTINA'}
    assert remote.expected == {'CATALOGO_RUTINA'}


def test_enrollment_reads_only_its_dependencies_before_rejecting_an_unknown_client():
    remote = RecordingRemote()
    remote.error_table = 'INVENTARIO'
    gym = service_with_remote(remote)
    with pytest.raises(ValueError, match='Cliente'):
        gym.matricular_cliente_horario({'id_cliente': 1, 'id_horario_servicio': 1})
    assert set(remote.calls) == {'CLIENTES', 'MEMBRESIA', 'CATALOGO_RUTINA', 'HORARIOS_SERVICIO', 'MATRICULAS_HORARIO'}


def test_order_name_lookup_does_not_replace_an_unpublished_product_snapshot():
    remote = RecordingRemote({'TIENDA_PRODUCTOS': [{'id_producto': 1, 'nombre_Producto': 'Agua'}]})
    gym = service_with_remote(remote)
    gym.ensure_fresh(('productos_tienda',))
    cached_state = deepcopy(gym.state['productos_tienda'])
    cached_raw = deepcopy(gym._raw_rows['TIENDA_PRODUCTOS'])
    remote.rows['TIENDA_PRODUCTOS'][0]['nombre_Producto'] = 'Agua nueva'
    remote.rows['VENTAS'] = [{'id_venta': 1}]
    remote.rows['DETALLE_VENTA'] = [{'id_venta': 1, 'id_producto': 1}]
    gym.ensure_fresh(('pedidos_tienda',))
    assert gym.state['pedidos_tienda'][0]['items'][0]['nombre_producto'] == 'Agua nueva'
    assert gym.state['productos_tienda'] == cached_state
    assert gym._raw_rows['TIENDA_PRODUCTOS'] == cached_raw


def test_summary_never_materializes_pages_of_closed_history_and_keeps_overnight_visits():
    gym = GymService(MemoryGymRepository(), Passwords())
    history = [dict(id_asistencia=i, id_cliente_num=1, fecha='2020-01-01', hora_salida='11:00') for i in range(1, 2502)]
    gym.repository.state['asistencia'] = [*history,
        dict(id_asistencia=2502, id_cliente_num=2, fecha='2026-10-22', hora='23:00', hora_salida=''),
        dict(id_asistencia=2503, id_cliente_num=3, fecha='2026-10-22', hora_salida='01:00', fecha_salida='2026-10-23'),
        dict(id_asistencia=2504, id_cliente_num=4, fecha='2026-10-23', hora='10:00', hora_salida=''),
        dict(id_asistencia=2505, id_cliente_num=5, fecha='2026-10-23', anulado=True)]
    def forbidden(*args):
        pytest.fail('El resumen no debe consultar páginas de historial')
    gym.repository.attendance_page = forbidden
    service = AttendanceService(gym, clock=lambda: datetime(2026, 10, 23, 12, tzinfo=LIMA))
    summary = service.summary(SimpleNamespace(role='admin'))
    assert (summary['entradas'], summary['salidas'], summary['dentro']) == (1, 1, 2)
    assert {row['id_asistencia'] for row in summary['pendientes']} == {2502, 2504}
    assert [row['id_asistencia'] for row in summary['recientes']] == [2504]


@pytest.mark.parametrize('client_id', [None, 7])
def test_remote_summary_uses_counts_open_visits_and_eight_recent_records(client_id):
    calls = []
    class Database:
        def count(self, table, filters):
            calls.append(('count', table, filters))
            return 3 if 'Fecha' in filters else 2
        def select_filtered(self, table, filters, *, order):
            calls.append(('filtered', table, filters))
            return [{'id_asistencia': 1, 'id_cliente': 7, 'Fecha': '2026-10-22'}] if table == 'ASISTENCIA' else [{'id_cliente': 7, 'Nombres': 'Ana'}]
        def select_page(self, table, filters, *, order, offset, limit):
            calls.append(('page', table, filters))
            assert (offset, limit) == (0, 8)
            return SimpleNamespace(rows=[{'id_asistencia': 2, 'id_cliente': 7, 'Fecha': '2026-10-23'}])
    data = AttendanceHistoryRepository(Database()).summary('2026-10-23', client_id)
    assert (data.entries, data.exits) == (3, 2)
    assert len(calls) == 5
    for kind, table, filters in calls:
        if table == 'ASISTENCIA':
            assert filters['or'] == '(anulado.is.null,anulado.eq.false)'
            if client_id is not None:
                assert filters['id_cliente'] == 'eq.7'
    assert 'fecha_salida.is.null,Fecha.eq.2026-10-23' in calls[1][2]['and']
    assert calls[2][2]['hora_salida'] == 'is.null'


def test_count_requests_no_rows_and_preserves_filters(monkeypatch):
    from io import BytesIO
    from urllib.parse import parse_qs, urlsplit
    from infrastructure.supabase_client import SupabaseRestClient
    calls = []
    def opener(request, timeout):
        query = parse_qs(urlsplit(request.full_url).query)
        calls.append(query)
        assert query['limit'] == ['0']
        assert query['id_cliente'] == ['eq.7']
        assert request.get_header('Prefer') == 'count=exact'
        response = BytesIO(b'[]')
        response.headers = {'Content-Range': '*/42'}
        return response
    monkeypatch.setattr('infrastructure.supabase_client.urlopen', opener)
    assert SupabaseRestClient('https://example.invalid', 'test-only').count('ASISTENCIA', {'id_cliente': 'eq.7'}) == 42
    assert len(calls) == 1
