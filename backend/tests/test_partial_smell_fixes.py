"""Contratos de los cinco hallazgos que quedaban parcialmente corregidos."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from application.errors import SchemaNotReady
from application.services import store_checkout_service as checkout
from domain.errors import EnrollmentConflict, EntityNotFound, MembershipRequired
from domain.models.auth import UserProfile
from domain.models.gym import (
    MembresiaInput, InventarioInput, ProductoTiendaInput, MatriculaHorarioInput,
    PedidoTiendaItemInput, EjercicioInput, EjercicioProgresoInput, CatalogoRutinaInput, RutinaProgresoInput,
)
from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_unit_of_work import GymUnitOfWork
from infrastructure.repositories.atomic_changes import SnapshotConflict
from infrastructure.services.local_gym_service import LocalGymService
from presentation.dependencies import get_gym_service, get_current_user
from presentation.routes.gym_routes import router as gym_router
from presentation.routes.inventory_routes import router as inventory_router


def api(router, service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_gym_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id='SGADM001', id_usuario='SGADM001', name='Admin', email='admin@example.com', role='admin',
    )
    return TestClient(app)


@pytest.mark.parametrize('exception,status', [
    (EnrollmentConflict('Mensaje nuevo sin palabras clave'), 409),
    (MembershipRequired('Otro mensaje de membresía'), 403),
    (ValueError('sin cupos: frase antigua sin tipo de conflicto'), 400),
    (SchemaNotReady('006_schedule_email_notifications.sql'), 503),
])
def test_enrollment_http_status_depends_on_error_type_not_its_text(exception, status):
    def enroll(_):
        raise exception
    client = api(gym_router, SimpleNamespace(matricular_cliente_horario=enroll))
    result = client.post('/gym/matriculas', json={'id_cliente': 1, 'id_horario_servicio': 10})
    assert result.status_code == status
    assert result.json()['detail'] == str(exception)


def test_inventory_not_found_status_survives_a_changed_message():
    def change(*_):
        raise EntityNotFound('Ya no existe el movimiento solicitado')
    client = api(inventory_router, SimpleNamespace(actualizar_movimiento_inventario=change))
    response = client.put('/inventario/movimientos/12', json={'descripcion': 'Una corrección'})
    assert response.status_code == 404


def test_unit_of_work_can_retry_and_restore_state_without_a_global_repository():
    cache = GymCache(state={'usuario': [{'id_usuario': 1, 'nombre': 'original'}]})
    commits = []
    reloads = []
    def commit(previous, current, keys):
        commits.append(deepcopy(current['usuario']))
        if len(commits) == 1:
            raise SnapshotConflict('Cambio concurrente')
    def load(resources):
        assert cache.state['usuario'][0]['nombre'] == 'original'
        reloads.append(resources)
        cache.state['usuario'][0]['nombre'] = 'otra instancia'
    database = SimpleNamespace(rpc=lambda *_: {'USUARIO': 1})
    work = GymUnitOfWork(database, cache, SimpleNamespace(refresh_if_stale=lambda _: None, load=load),
                         SimpleNamespace(commit=commit), SimpleNamespace(missing_tables=set()))
    def change(state):
        state['usuario'][0]['nombre'] += ' actualizado'
        return state['usuario'][0]['nombre']
    result = work.change(change, resources=('usuario',))
    assert result == 'otra instancia actualizado'
    assert reloads == [('usuario',)]
    assert commits[0][0]['nombre'] == 'original actualizado'
    assert cache.state['usuario'][0]['nombre'] == result


def test_cache_queries_cannot_mutate_owned_state_or_call_a_database():
    cache = GymCache(state={'usuario': [{'nombre': 'Ana'}], 'asistencia': []})
    cache.read(lambda state: state['usuario'][0].update(nombre='Cambio local'), resources=('usuario',))
    assert cache.state['usuario'][0]['nombre'] == 'Ana'


class StoreGym:
    def __init__(self, gateway):
        self.gateway_factory = lambda _: gateway
        self.saved = []
    def ensure_fresh(self):
        pass
    def get_pedido_tienda(self, _):
        return {'id_pedido': 7, 'estado_pago': 'PENDIENTE', 'estado_pedido': 'PENDIENTE', 'referencia_pago': 'cs_pending'}
    def actualizar_pedido_tienda(self, identity, payload, actor=None):
        self.saved.append((identity, payload, actor))
        return {'id_pedido': identity, **payload}


class Gateway:
    configured = True
    def __init__(self, status):
        self.status, self.expired = status, []
    def validate_configuration(self):
        pass
    def expire_checkout_session(self, session_id):
        self.expired.append(session_id)
        return {'id': session_id, 'status': self.status}


def test_administrative_cancel_closes_checkout_before_changing_order():
    gateway = Gateway('expired')
    gym = StoreGym(gateway)
    result = checkout.actualizar_estado_pedido(gym, None, 7, {'estado_pedido': 'CANCELADO'}, actor='SGADM001')
    assert gateway.expired == ['cs_pending']
    assert gym.saved == [(7, {'estado_pedido': 'CANCELADO'}, 'SGADM001')]
    assert result['estado_pedido'] == 'CANCELADO'


@pytest.mark.parametrize('session_status', ['open', 'complete'])
def test_failed_close_or_a_payment_race_does_not_cancel_the_order(monkeypatch, session_status):
    gateway = Gateway(session_status)
    gym = StoreGym(gateway)
    confirmed = []
    monkeypatch.setattr(checkout, 'confirmar_sesion_tienda', lambda session, *_: confirmed.append(session))
    with pytest.raises((ValueError, RuntimeError)):
        checkout.actualizar_estado_pedido(gym, None, 7, {'estado_pedido': 'CANCELADO'})
    assert gym.saved == []
    assert bool(confirmed) == (session_status == 'complete')


def test_other_order_statuses_do_not_contact_the_gateway():
    gym = StoreGym(None)
    checkout.actualizar_estado_pedido(gym, None, 7, {'estado_pedido': 'ENTREGADO'})
    assert gym.saved[0][1] == {'estado_pedido': 'ENTREGADO'}


@pytest.mark.parametrize('model,payload,field', [
    (MembresiaInput, {'id_cliente': 1, 'id_pm': 1, 'fecha_inicio': '2026-10-23', 'fecha_fin': '2026-10-24'}, 'id_cliente'),
    (MembresiaInput, {'id_cliente': 1, 'id_pm': 1, 'fecha_inicio': '2026-10-23', 'fecha_fin': '2026-10-24'}, 'id_pm'),
    (InventarioInput, {'nombre_item': 'Pesas', 'tipo': 'Equipo', 'cantidad_stock': 2}, 'id_item'),
    (ProductoTiendaInput, {'nombre_producto': 'Agua', 'precio_venta': 3}, 'id_producto'),
    (MatriculaHorarioInput, {'id_cliente': 'SGCLI001', 'id_horario_servicio': 1}, 'id_horario_servicio'),
    (PedidoTiendaItemInput, {'id_producto': 1, 'cantidad': 1}, 'id_producto'),
])
@pytest.mark.parametrize('invalid_id', [-1, 0, True, ''])
def test_identifiers_must_be_positive_and_nonempty(model, payload, field, invalid_id):
    with pytest.raises(ValidationError):
        model(**{**payload, field: invalid_id})


@pytest.mark.parametrize('model,field', [(EjercicioInput, 'peso_sugerido_kg'), (EjercicioProgresoInput, 'peso_utilizado_kg')])
def test_exercise_weights_reject_negatives_and_preserve_zero(model, field):
    with pytest.raises(ValidationError):
        model(nombre_ejercicio='Sentadillas', **{field: -5})
    assert getattr(model(nombre_ejercicio='Sentadillas', **{field: 0}), field) == 0
    assert getattr(model(nombre_ejercicio='Sentadillas', **{field: None}), field) is None


def test_nested_exercise_contracts_reject_missing_identity_and_invalid_weights():
    with pytest.raises(ValidationError):
        CatalogoRutinaInput(nombre_rutina='Piernas', zonas_musculares='Piernas', ejercicios=[{}])
    with pytest.raises(ValidationError):
        RutinaProgresoInput(ejercicios_detalle=[{'id_ejercicio': 1, 'peso_utilizado_kg': -10}])
    # La referencia a un ejercicio existente no obliga a repetir su nombre.
    assert EjercicioProgresoInput(id_ejercicio='exercise-1', series_completadas=0).series_completadas == 0


def test_direct_domain_commands_also_reject_invalid_exercise_data_before_mutating_state():
    gym = LocalGymService()
    snapshot = lambda: gym.repository.read(lambda state: {key: value for key, value in state.items() if not key.startswith("_")})
    previous = snapshot()
    with pytest.raises(ValueError, match='peso_sugerido_kg'):
        gym.upsert_rutina({'nombre_rutina': 'Piernas', 'ejercicios': [{'nombre_ejercicio': 'Sentadillas', 'peso_sugerido_kg': -1}]})
    assert snapshot() == previous
    with pytest.raises(ValueError, match='peso_utilizado_kg'):
        gym.registrar_progreso_rutina(1, {'ejercicios_detalle': [{'nombre_ejercicio': 'Sentadillas', 'peso_utilizado_kg': -1}]})
    assert snapshot() == previous
