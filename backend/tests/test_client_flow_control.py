"""Control reproducible del flujo; sin proveedores ni datos reales."""
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.errors import PersistenceUnavailable
from application.services.attendance_service import AttendanceService, LIMA
from application.services.auth_service import AuthService, ClientMembershipExpired
from application.services.clients_service import ClientsService
from infrastructure.services.local_gym_service import LocalGymService
from presentation import dependencies as deps
from presentation.error_handlers import install_error_handlers
from presentation.routes import clients_routes


VALID = dict(nombre='Cliente Control', correo='control@gmail.com', dni='01234567',
             telefono='987654321', password='secreto123', plan='MENSUAL')
ADMIN = SimpleNamespace(role='admin', id='SGADM001', id_usuario='SGADM001', name='Admin', id_cliente=None)


@pytest.fixture
def flow(monkeypatch):
    for module in ('domain.services.gym_domain_service', 'application.services.auth_service',
                   'application.services.clients_service', 'infrastructure.services.supabase_gym_service'):
        monkeypatch.setattr(f'{module}._today_iso', lambda: '2026-10-07')
    gym = LocalGymService()
    clients = ClientsService(gym)
    result = clients.register_admin_client(VALID)
    return gym, clients, result


def client_api(service):
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(clients_routes.router, prefix='/api')
    app.dependency_overrides[deps.get_clients_service] = lambda: service
    app.dependency_overrides[deps.require_admin_or_staff] = lambda: ADMIN
    return TestClient(app)


def test_delete_failure_reaches_http_instead_of_reporting_success():
    gym = Mock()
    gym.delete_cliente.side_effect = PersistenceUnavailable('respuesta privada proveedor')
    response = client_api(ClientsService(gym)).delete('/api/clientes/1')
    assert response.status_code == 503
    assert 'privada' not in response.text
    gym.delete_cliente.assert_called_once_with(1)


@pytest.mark.parametrize('identity', ['', 'SGCLIbad', 'otro-1', 'SGCLI0'])
def test_delete_rejects_invalid_identity(identity):
    gym = Mock()
    with pytest.raises(ValueError):
        ClientsService(gym).delete_client(identity)
    gym.delete_cliente.assert_not_called()


def test_successful_delete_runs_existing_cascade(flow):
    gym, clients, result = flow
    response = client_api(clients).delete(f"/api/clientes/{result['cliente']['id_cliente']}")
    assert response.status_code == 204
    assert gym.state['clientes'] == gym.state['membresia'] == []


@pytest.mark.parametrize('status,payment', [('EN_TRAMITE', 'PAGADO'), ('ACTIVO', 'PAGADO'),
                                           ('VENCIDA', 'PAGADO'), ('ACTIVO', 'PENDIENTE')])
def test_confirmed_membership_cannot_be_replaced(flow, status, payment):
    gym, _, result = flow
    member = gym.state['membresia'][0]
    member.update(estado=status, estado_pago=payment, referencia_pago='pago-original',
                  fecha_pago='2026-10-01', fecha_inicio='2026-10-01', fecha_fin='2026-10-31')
    before = deepcopy(member)
    with pytest.raises(ValueError, match='confirmada'):
        gym.crear_membresia({**member, 'fecha_fin': '2027-01-01'})
    assert gym.state['membresia'][0] == before


def test_membership_cannot_be_transferred_to_another_client(flow):
    gym, clients, result = flow
    other = clients.register_admin_client({**VALID, 'correo': 'otro@gmail.com', 'dni': '12345678'})
    member = result['membresia']
    before = deepcopy(gym.state['membresia'])
    with pytest.raises(ValueError, match='otro cliente'):
        gym.crear_membresia({**member, 'id_cliente': other['cliente']['id_cliente']})
    assert gym.state['membresia'] == before


def test_pending_edit_cannot_set_activation_dates_or_state(flow):
    gym, _, result = flow
    member = result['membresia']
    changed = gym.crear_membresia({**member, 'estado': 'ACTIVO', 'fecha_inicio': '2026-10-01',
                                  'fecha_fin': '2026-11-01'})
    assert changed['estado'] == 'EN_TRAMITE'
    assert changed['estado_pago'] == 'PENDIENTE'
    assert changed['fecha_inicio'] == changed['fecha_fin'] == ''


def test_zero_saved_amount_is_not_repriced_during_confirmation(flow):
    gym, clients, result = flow
    gym.state['membresia'][0]['monto_pago'] = 0
    amount = result['plan']['precio']
    cid = result['cliente']['id_cliente']
    mid = result['membresia']['id_membresia']
    assert clients.payment_amount_matches(cid, amount, mid) is False
    with pytest.raises(ValueError, match='importe'):
        clients.confirm_public_payment(cid, dict(id_membresia=mid, monto_pago=amount, referencia_pago='cs_sintetica'))
    assert gym.state['membresia'][0]['monto_pago'] == 0
    assert gym.state['membresia'][0]['estado_pago'] == 'PENDIENTE'


def schedule_payload(gym, **changes):
    gym.state['catalogo_rutina'] = [dict(id_rutina=7, servicio='fitness', nombre_rutina='Control')]
    return dict(servicio='fitness', id_rutina=7, dia='miercoles', hora_inicio='10:00',
                hora_fin='11:00', cupos=1, **changes)


@pytest.mark.parametrize('changes', [dict(dia='feriado'), dict(hora_inicio='basura10:00'),
                                      dict(hora_fin='11:00 texto'), dict(hora_inicio='10:00:30'),
                                      dict(hora_inicio='13:00 pm', hora_fin='14:00 pm')])
def test_invalid_schedule_is_rejected_without_writing(flow, changes):
    gym, _, _ = flow
    payload = schedule_payload(gym)
    payload.update(changes)
    before = deepcopy(gym.state['horarios_servicio'])
    with pytest.raises(ValueError):
        gym.upsert_horario_servicio(payload)
    assert gym.state['horarios_servicio'] == before


@pytest.mark.parametrize('start,end', [('10:00:00', '11:00:00'), ('10 am', '11 am'), ('10:00 a. m.', '11:00 a. m.')])
def test_valid_schedule_is_canonical_for_attendance(flow, start, end):
    gym, _, _ = flow
    payload = schedule_payload(gym)
    payload.update(hora_inicio=start, hora_fin=end)
    saved = gym.upsert_horario_servicio(payload)
    assert saved['hora_inicio'] == '10:00'
    assert saved['hora_fin'] == '11:00'


@pytest.mark.parametrize('changes', [dict(fecha_inicio=''), dict(fecha_inicio='2026-02-30'),
                                      dict(fecha_fin='9999-99-99'), dict(fecha_fin='no-es-fecha')])
def test_attendance_uses_real_membership_dates(flow, changes):
    gym, _, result = flow
    cid = result['cliente']['id_cliente']
    gym.confirmar_pago_manual_cliente(cid)
    gym.activar_membresia_cliente(cid)
    gym.state['membresia'][0].update(changes)
    service = AttendanceService(gym, clock=lambda: datetime(2026, 10, 7, 10, 30, tzinfo=LIMA))
    with pytest.raises(ValueError, match='vigente'):
        service.enter_general(VALID['dni'], str(uuid4()), ADMIN)
    assert gym.state['asistencia'] == []


@pytest.mark.parametrize('origin', ['PUBLICO', 'ADMIN'])
def test_full_registration_activation_enrollment_attendance_and_expiration(flow, monkeypatch, origin):
    from application.services.auth_service import ClientActivationRequired
    from application.services.membership_checkout_service import confirm_verified_checkout
    from domain.money import cents
    from datetime import timedelta

    gym = LocalGymService()
    clients = ClientsService(gym)
    day = ['2026-10-07']
    for module in ('domain.services.gym_domain_service', 'application.services.auth_service',
                   'application.services.clients_service'):
        monkeypatch.setattr(f'{module}._today_iso', lambda: day[0])
    if origin == 'PUBLICO':
        registered = clients.register_public_client(VALID)
        retry = clients.register_public_client(VALID)
        assert retry['cliente']['id_cliente'] == registered['cliente']['id_cliente']
        assert retry['membresia'] == registered['membresia']
        before = deepcopy(gym.state['clientes'])
        for bad in ({'password': 'incorrecta'}, {'dni': '87654321'}):
            with pytest.raises(ValueError):
                clients.register_public_client({**VALID, **bad})
        assert gym.state['clientes'] == before
    else:
        registered = clients.register_admin_client(VALID)
    assert len(gym.state['clientes']) == len(gym.state['membresia']) == 1
    assert 'password_hash' not in registered['cliente']
    cid = registered['cliente']['id_cliente']
    mid = registered['membresia']['id_membresia']
    auth = AuthService(gym)
    with pytest.raises(ClientActivationRequired):
        auth.session_for_client(gym.get_cliente(cid))
    with pytest.raises(ValueError, match='sin pago'):
        clients.activate_client_membership(cid)
    if origin == 'PUBLICO':
        checkout = dict(id='cs_sintetica', livemode=False, payment_status='paid', status='complete',
                        mode='payment', currency='pen', amount_total=cents(registered['membresia']['monto_pago']),
                        client_reference_id=f'membership:{cid}',
                        metadata=dict(purpose='membership', client_id=str(cid), membership_id=str(mid)))
        gateway = SimpleNamespace(get_checkout_session=lambda _: checkout)
        notify = Mock(return_value={'status': 'simulada'})
        for _ in range(2):
            payment = confirm_verified_checkout('cs_sintetica', clients, SimpleNamespace(stripe_mode='test'),
                                                gateway=gateway, notify=notify)
            assert payment['confirmed']
    else:
        clients.confirm_manual_payment(cid)
        clients.confirm_manual_payment(cid)
    assert gym.latest_membership(cid)['estado'] == 'EN_TRAMITE'
    with pytest.raises(ClientActivationRequired):
        auth.session_for_client(gym.get_cliente(cid))
    active = clients.activate_client_membership(cid)['membresia']
    assert clients.activate_client_membership(cid)['membresia'] == active
    assert auth.session_for_client(gym.get_cliente(cid)).user.id_cliente == cid
    schedule = gym.upsert_horario_servicio(schedule_payload(gym))
    sid = schedule['id_horario_servicio']
    enrollment = gym.matricular_cliente_horario(dict(id_cliente=cid, id_horario_servicio=sid))
    with pytest.raises(ValueError, match='ya esta matriculado'):
        gym.matricular_cliente_horario(dict(id_cliente=cid, id_horario_servicio=sid))
    second = clients.register_admin_client({**VALID, 'correo': 'segundo@gmail.com', 'dni': '12345678'})
    cid2 = second['cliente']['id_cliente']
    clients.confirm_manual_payment(cid2)
    clients.activate_client_membership(cid2)
    with pytest.raises(ValueError, match='sin cupos'):
        gym.matricular_cliente_horario(dict(id_cliente=cid2, id_horario_servicio=sid))
    current = [datetime(2026, 10, 7, 10, 30, tzinfo=LIMA)]
    attendance = AttendanceService(gym, clock=lambda: current[0])
    row = attendance.enter(dict(id_matricula=enrollment['id_matricula']), ADMIN)
    assert attendance.enter(dict(id_matricula=enrollment['id_matricula']), ADMIN)['id_asistencia'] == row['id_asistencia']
    with pytest.raises(ValueError, match='entrada sin salida'):
        attendance.enter_general(VALID['dni'], str(uuid4()), ADMIN)
    current[0] = datetime(2026, 10, 7, 10, 45, tzinfo=LIMA)
    assert attendance.exit(row['id_asistencia'], ADMIN)['estado'] == 'completada'
    gym.cancelar_matricula_horario(enrollment['id_matricula'], id_cliente=cid)
    assert gym.get_horario_servicio(sid)['cupos_usados'] == 0
    last_day = gym.latest_membership(cid)['fecha_fin']
    day[0] = last_day
    auth.session_for_client(gym.get_cliente(cid))
    current[0] = datetime.fromisoformat(f'{last_day}T12:00:00').replace(tzinfo=LIMA)
    visit = attendance.enter_general(VALID['dni'], str(uuid4()), ADMIN)
    attendance.exit(visit['id_asistencia'], ADMIN)
    day[0] = (current[0].date() + timedelta(days=1)).isoformat()
    current[0] += timedelta(days=1)
    with pytest.raises(ClientMembershipExpired):
        auth.session_for_client(gym.get_cliente(cid))
    before = len(gym.state['asistencia'])
    with pytest.raises(ValueError, match='vigente'):
        attendance.enter_general(VALID['dni'], str(uuid4()), ADMIN)
    assert len(gym.state['asistencia']) == before
    assert gym.latest_membership(cid)['estado_pago'] == 'PAGADO'
    assert len([m for m in gym.state['membresia'] if m['id_cliente'] == cid]) == 1


@pytest.mark.parametrize('value', [None, 'ausente'])
def test_legacy_missing_amount_keeps_fallback(flow, value):
    gym, clients, result = flow
    member = gym.state['membresia'][0]
    if value is None:
        member['monto_pago'] = None
    else:
        member.pop('monto_pago')
    amount = result['plan']['precio']
    cid = result['cliente']['id_cliente']
    assert clients.payment_amount_matches(cid, amount, member['id_membresia'])
    saved = clients.confirm_public_payment(cid, dict(id_membresia=member['id_membresia'], monto_pago=amount,
                                                    referencia_pago='cs_historica'))
    assert saved['membresia']['monto_pago'] == amount


def test_invalid_delete_identity_is_reported_as_http_400():
    gym = Mock()
    response = client_api(ClientsService(gym)).delete('/api/clientes/0')
    assert response.status_code == 400
    gym.delete_cliente.assert_not_called()


def test_confirmed_membership_edit_is_reported_as_http_400(flow):
    from presentation.routes import memberships_routes

    gym, clients, result = flow
    cid = result['cliente']['id_cliente']
    clients.confirm_manual_payment(cid)
    saved = clients.activate_client_membership(cid)['membresia']
    before = deepcopy(gym.state['membresia'])
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(memberships_routes.router, prefix='/api')
    app.dependency_overrides[deps.get_gym_service] = lambda: gym
    app.dependency_overrides[deps.require_admin_or_staff] = lambda: ADMIN
    response = TestClient(app).post('/api/membresias', json=saved)
    assert response.status_code == 400
    assert 'confirmada' in response.json()['detail']
    assert gym.state['membresia'] == before
