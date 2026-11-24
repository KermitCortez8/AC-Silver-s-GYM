from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.services.client_payments_service import ClientPaymentsService
from application.services.clients_service import ClientsService
from domain.models.auth import UserProfile
from infrastructure.config import Settings
from infrastructure.services.local_gym_service import LocalGymService
from presentation.dependencies import get_client_payments_service, get_clients_service, get_current_user, get_settings
from presentation.routes.clients_routes import router


REGISTRO = dict(nombre='Cliente de prueba', correo='pago@example.com', dni='12345678',
                telefono='999111222', password='clave-local', plan='MENSUAL')


@pytest.fixture
def entorno():
    settings = Settings(supabase_url='https://gym.example.test', supabase_key='solo-local',
                        pagos_yape_qr_url='/pagos/yape.png',
                        pagos_mercado_pago_enlaces='{"79.00":"https://mpago.la/enlace-prueba"}')
    gym = LocalGymService()
    clients = ClientsService(gym)
    payments = ClientPaymentsService(clients, gym, settings, gateway_factory=lambda _: None,
                                     notify=lambda *_: {'status': 'not_configured'})
    usuario = SimpleNamespace(role='staff')
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_client_payments_service] = lambda: payments
    app.dependency_overrides[get_clients_service] = lambda: clients
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: UserProfile(
        id='CUENTA1', name='Personal', email='staff@example.com', role=usuario.role,
    )
    return TestClient(app), gym, payments, usuario


def test_qr_publico_reserva_el_precio_y_requiere_verificacion_de_recepcion(entorno):
    api, gym, pagos, usuario = entorno
    alta = api.post('/registro-publico', json={**REGISTRO, 'medio_pago': 'yape_plin', 'estado_pago': 'PAGADO'}).json()
    assert alta['payment'] == {'revision_pendiente': True, 'medio_pago': 'yape_plin',
                               'amount': 79, 'qr_url': '/pagos/yape.png'}
    token = alta['preregistro']['token']
    assert gym.clientes_normalized() == gym.membresias() == []
    assert pagos.archive_due_preregistrations(now='9999-01-01T00:00:00+00:00') == 1
    assert api.post('/registro-publico', json={**REGISTRO, 'medio_pago': 'yape_plin'}).json()['preregistro']['token'] == token
    confirmacion = f'/preregistros/{token}/confirmar-pago-externo'
    usuario.role = 'user'
    assert api.get('/preregistros/pagos-pendientes').status_code == 403
    assert api.post(confirmacion, json={'operacion': 'PAGO12345', 'monto_recibido': 79}).status_code == 403
    usuario.role = 'staff'
    fila, = api.get('/preregistros/pagos-pendientes').json()
    assert fila['token'] == token and 'password_hash' not in fila
    assert api.post(confirmacion, json={'operacion': 'PAGO12345', 'monto_recibido': 78}).status_code == 400
    for _ in range(2):
        assert api.post(confirmacion, json={'operacion': 'pago-12345', 'monto_recibido': 79}).status_code == 200
    assert api.get('/preregistros/pagos-pendientes').json() == []
    membresia, = gym.membresias()
    assert (membresia['estado_pago'], membresia['estado'], membresia['metodo_pago']) == ('PAGADO', 'EN_TRAMITE', 'yape_plin')
    assert membresia['referencia_pago'] == 'yape_plin:PAGO12345'


def test_enlace_admin_usa_importe_fijo_y_registra_referencia_sin_cobrar_por_stripe(entorno):
    api, gym, *_ = entorno
    promo = gym.upsert_promocion({'nombre': 'Descuento QA', 'valor_descuento': 10, 'tipo_descuento': 'monto', 'activo': True})
    registro = {**REGISTRO, 'medio_pago': 'mercado_pago'}
    assert api.post('/clientes/registro-admin', json={**registro, 'id_promocion': promo['id_promocion']}).status_code == 400
    assert gym.membresias() == []
    response = api.post('/clientes/registro-admin', json=registro)
    assert response.status_code == 201
    datos = response.json()
    cid = datos['cliente']['id_cliente']
    assert datos['payment']['enlace'] == 'https://mpago.la/enlace-prueba'
    assert datos['membresia']['estado_pago'] == 'PENDIENTE'
    assert api.get(f'/clientes/{cid}/instrucciones-pago').json() == datos['payment']
    assert api.post(f'/clientes/{cid}/pago-stripe').status_code == 400
    assert api.post(f'/clientes/{cid}/confirmar-pago-manual').status_code == 400
    recibo = {'id_membresia': datos['membresia']['id_membresia'], 'operacion': 'MP72084', 'monto_recibido': 79}
    assert api.post(f'/clientes/{cid}/confirmar-pago-externo', json=recibo).status_code == 200
    assert gym.membresias()[0]['referencia_pago'] == 'mercado_pago:MP72084'
    otro = api.post('/clientes/registro-admin', json={**registro, 'correo': 'otro@example.com', 'dni': '59876543'}).json()
    otro_cliente = otro['cliente']['id_cliente']
    recibo.update(id_membresia=otro['membresia']['id_membresia'], operacion='mp-72084')
    assert api.post(f'/clientes/{otro_cliente}/confirmar-pago-externo', json=recibo).status_code == 400
