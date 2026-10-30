"""Contratos públicos de composición, comandos acotados y consultas paginadas."""
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from application.operations.accounts import DeleteClienteCommand, GetUsuarioQuery
from application.operations.memberships import UpsertPlanMembresiaCommand
from application.read_models import AttendanceCriteria, AttendancePage, PageRequest
from application.services.attendance_service import AttendanceService
from application.services.gym_service import GymService
from domain.models.resources import Resource
from domain.services.accounts_rules import AccountsDependencies, AccountsRules
from domain.services.gym_domain_service import GymDomainService
from domain.services.rule_context import RuleContext
from infrastructure.http_transport import RemoteServiceError
from infrastructure.repositories.attendance_history_repository import AttendanceHistoryRepository
from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
from infrastructure.supabase_client import SupabaseRestClient, RowsPage
from tests.test_priority_fixes import Passwords


def test_accounts_component_can_run_with_an_explicit_membership_policy_only():
    calls = []
    context = RuleContext({'usuario': [], 'clientes': [], 'membresia': []}, Passwords(),
                          today_provider=lambda: '2026-10-23')
    policy = AccountsDependencies(ensure_membership_for_active_client=lambda *args: calls.append(args))
    accounts = AccountsRules(context, policy)
    saved = accounts.upsert_cliente({'nombre': 'Ana', 'correo': 'ana@gmail.com', 'estado': 'EN_TRAMITE', 'password': 'secreto123'})
    assert saved['nombre'] == 'Ana'
    assert context.state['clientes'][0]['id_cliente'] == 1
    assert accounts.get_cliente(1)['correo'] == 'ana@gmail.com'
    assert len(calls) == 1


def test_application_uses_typed_operations_without_callback_or_string_dispatch():
    received = []
    class Repository:
        def query(self, query, passwords):
            received.append(query)
            return {'id_usuario': query.id_usuario}
        def execute(self, command, passwords):
            received.append(command)
            return {**command.payload, 'id_pm': 4}
    service = GymService(Repository(), Passwords())
    assert service.get_usuario('SGADM001')['id_usuario'] == 'SGADM001'
    assert service.upsert_plan_membresia({'nombre_plan': 'Especial', 'precio': 40})['id_pm'] == 4
    assert isinstance(received[0], GetUsuarioQuery)
    assert isinstance(received[1], UpsertPlanMembresiaCommand)
    assert received[1].resources == (Resource.PLANES_MEMBRESIA,)
    with pytest.raises(ValueError, match='contrato'):
        service.executor.query(received[1])
    with pytest.raises(ValueError, match='contrato'):
        service.executor.execute('delete_cliente')
    assert len(received) == 2


def test_commands_cannot_mutate_resources_outside_their_declared_unit():
    repo = MemoryGymRepository()
    repo.state['pedidos_tienda'] = [{'id_pedido': 91}]
    class Command:
        operation_kind = 'command'
        resources = (Resource.USUARIO,)
        def run(self, rules):
            rules.context.state.setdefault('pedidos_tienda', []).clear()
            rules.context.state['usuario'].append({'id_usuario': 'SGADM001'})
            return {'ok': True}
    GymService(repo, Passwords()).executor.execute(Command())
    assert repo.state['pedidos_tienda'] == [{'id_pedido': 91}]
    assert repo.state['usuario'] == [{'id_usuario': 'SGADM001'}]


def test_client_deletion_keeps_the_whole_cascade_inside_one_command():
    repo = MemoryGymRepository()
    for key, identity in [('clientes', 'id_cliente'), ('membresia', 'id_membresia'),
                          ('asistencia', 'id_asistencia'), ('horario', 'id_horario'),
                          ('tickets_atencion', 'id_ticket')]:
        repo.state[key] = [{identity: 1, 'id_cliente': 1}, {identity: 2, 'id_cliente': 2}]
    GymService(repo, Passwords()).delete_cliente(1)
    for resource in (Resource.CLIENTES, Resource.MEMBRESIA, Resource.ASISTENCIA,
                     Resource.HORARIO, Resource.TICKETS_ATENCION):
        assert [row['id_cliente'] for row in repo.state[resource]] == [2]
    assert set(DeleteClienteCommand.resources) >= {Resource.ASISTENCIA, Resource.HORARIO, Resource.TICKETS_ATENCION}


def test_failed_typed_command_does_not_publish_partial_business_state():
    repo = MemoryGymRepository()
    before = deepcopy({k: v for k, v in repo.state.items() if not k.startswith('_')})
    class Command:
        operation_kind = 'command'
        resources = (Resource.USUARIO,)
        def run(self, rules):
            rules.context.state['usuario'].append({'id_usuario': 'SGADM001'})
            raise RuntimeError('commit rejected')
    with pytest.raises(RuntimeError, match='commit rejected'):
        GymService(repo, Passwords()).executor.execute(Command())
    assert {k: v for k, v in repo.state.items() if not k.startswith('_')} == before


@pytest.mark.parametrize('page,size', [(0, 15), (1, 0), (1, 101)])
def test_page_contract_rejects_invalid_ranges(page, size):
    with pytest.raises(ValueError, match='Paginación'):
        PageRequest(page, size)


def test_history_passes_client_scope_to_persistence_and_hides_audit():
    received = []
    def page(criteria, request):
        received.append((criteria, request))
        return AttendancePage([{'id_asistencia': 90, 'id_cliente_num': 7, 'fecha': '2026-10-23',
                                'auditoria': [{'actor': 'privado'}], 'id_usuario_registra': 1}],
                              [{'id_cliente': 7, 'nombre': 'Ana', 'dni': '12345678'}], 44)
    service = AttendanceService(SimpleNamespace(attendance_page=page))
    # La conversión de identificador forma parte de la capacidad pública del gimnasio.
    service.gym.parse_client_id = GymDomainService().parse_client_id
    result = service.history(SimpleNamespace(role='user', id_cliente=7), page=2, page_size=15,
                             desde='2026-10-01', hasta='2026-10-23', estado='dentro')
    criteria, request = received[0]
    assert criteria.client_id == 7 and not criteria.include_annulled
    assert criteria.since == '2026-10-01' and criteria.status == 'dentro'
    assert request.offset == 15
    assert result['total'] == 44 and result['page'] == 2
    assert result['items'][0]['cliente_nombre'] == 'Ana'
    assert 'auditoria' not in result['items'][0] and 'id_usuario_registra' not in result['items'][0]


def test_remote_history_reads_only_page_and_its_clients_with_database_filters():
    received = []
    class Database:
        def select_page(self, table, filters, **bounds):
            received.append((table, filters, bounds))
            return RowsPage([{'id_asistencia': 99, 'id_cliente': 7, 'Fecha': '2026-10-23', 'Hora': '08:00'}], 300)
        def select_filtered(self, table, filters, **kwargs):
            assert table == 'CLIENTES' and filters == {'id_cliente': 'in.(7)'}
            return [{'id_cliente': 7, 'Nombres': 'Ana', 'DNI': '12345678'}]
    result = AttendanceHistoryRepository(Database()).page(
        AttendanceCriteria(client_id=7, since='2026-10-01', until='2026-10-23', status='dentro',
                           kind='general', include_annulled=False), PageRequest(3, 10))
    table, filters, bounds = received[0]
    assert table == 'ASISTENCIA' and bounds['offset'] == 20 and bounds['limit'] == 10
    assert filters['id_cliente'] == 'in.(7)'
    assert 'Fecha.gte.2026-10-01' in filters['and'] and 'Fecha.lte.2026-10-23' in filters['and']
    assert 'anulado.eq.false' in filters['and'] and 'hora_salida.is.null' in filters['and']
    assert 'servicio.eq.gimnasio' in filters['and']
    assert result.total == 300 and result.records[0]['id_asistencia'] == 99
    assert result.clients[0]['nombre'] == 'Ana'


def test_dni_filter_cannot_override_the_session_client():
    class Database:
        def select_filtered(self, *args, **kwargs):
            return [{'id_cliente': 8}]
        def select_page(self, *args, **kwargs):
            pytest.fail('No debe consultar el historial de otro cliente')
    result = AttendanceHistoryRepository(Database()).page(
        AttendanceCriteria(client_id=7, dni='87654321', include_annulled=False), PageRequest())
    assert result.total == 0 and result.records == []


def test_supabase_page_fills_requested_size_when_server_caps_each_response(monkeypatch):
    calls = []
    def opener(request, timeout):
        query = parse_qs(urlsplit(request.full_url).query)
        offset = int(query['offset'][0])
        calls.append(offset)
        assert request.get_header('Prefer') == 'count=exact'
        assert query['id_cliente'] == ['eq.7']
        response = BytesIO(__import__('json').dumps([{'id': n} for n in range(offset, min(offset + 2, offset + int(query['limit'][0]), 9))]).encode())
        response.headers = {'Content-Range': f'{offset}-{min(offset + 1, 8)}/9'}
        return response
    monkeypatch.setattr('infrastructure.supabase_client.urlopen', opener)
    result = SupabaseRestClient('https://example.invalid', 'test').select_page('ASISTENCIA', {'id_cliente': 'eq.7'},
        order='id_asistencia.asc', offset=3, limit=5)
    assert [row['id'] for row in result.rows] == [3, 4, 5, 6, 7]
    assert result.total == 9 and calls == [3, 5, 7]


def test_supabase_page_past_last_row_keeps_filtered_total(monkeypatch):
    def opener(request, timeout):
        query = parse_qs(urlsplit(request.full_url).query)
        if query.get('offset'):
            raise HTTPError(request.full_url, 416, 'Range', {}, BytesIO(b'{"code":"PGRST103"}'))
        assert query['limit'] == ['0']
        response = BytesIO(b'[]')
        response.headers = {'content-range': '*/3'}
        return response
    monkeypatch.setattr('infrastructure.supabase_client.urlopen', opener)
    result = SupabaseRestClient('https://example.invalid', 'test').select_page('ASISTENCIA', {},
        order='id_asistencia.asc', offset=30, limit=15)
    assert result.rows == [] and result.total == 3


def test_supabase_pagination_does_not_hide_permission_errors(monkeypatch):
    def opener(request, timeout):
        raise HTTPError(request.full_url, 403, 'Denied', {}, BytesIO(b'{"code":"42501"}'))
    monkeypatch.setattr('infrastructure.supabase_client.urlopen', opener)
    with pytest.raises(RemoteServiceError) as failure:
        SupabaseRestClient('https://example.invalid', 'test').select_page('ASISTENCIA', {},
            order='id_asistencia.asc', offset=0, limit=15)
    assert failure.value.code == '42501'
