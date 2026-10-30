"""Reglas de formularios: sin correo real, Stripe, red ni base de datos externa."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from application.services.clients_service import ClientsService
from domain.models.auth import UserProfile
from domain.models.gym import ClienteInput, PlanMembresiaInput, RegistroPublicoClienteInput, UsuarioInput
from domain.validation import account_email
from infrastructure.services.local_gym_service import LocalGymService
from presentation import dependencies as deps
from presentation.error_handlers import install_error_handlers
from presentation.routes import clients_routes, users_routes


VALID = dict(nombre='Ana', correo='ana@gmail.com', dni='01234567', telefono='987654321', password='secreto123')


@pytest.mark.parametrize('email', ['ana@gmail.com', 'ana@hotmail.com', 'ana@example.com', 'ana@outlook.com', 'ana@company.com', 'ana@sub.gmail.com', 'ana@gmail.com.evil.com', '  ANA@GMAIL.COM  '])
def test_approved_account_email_is_normalized(email):
    assert account_email(email) == email.strip().lower()


@pytest.mark.parametrize('email', ['', 'ana', '@gmail.com', 'ana@@gmail.com', 'ana..gym@gmail.com',
                                  '.ana@gmail.com', 'ana.@gmail.com', 'ana b@gmail.com', 'ana@gmail',
                                  'ana@-gmail.com', 'ana@gmail.com\nmail@hotmail.com'])
def test_malformed_account_email_has_an_actionable_message(email):
    with pytest.raises(ValueError, match='correo válido|obligatorio'):
        account_email(email)


@pytest.mark.parametrize('email', ['ana@example.org', 'ana@example.com.pe', 'ana@gmail.co'])
@pytest.mark.parametrize('model', [ClienteInput, UsuarioInput, RegistroPublicoClienteInput])
def test_every_account_write_schema_rejects_unapproved_domains(email, model):
    with pytest.raises(ValidationError, match='Solo se permiten correos que terminen en .com'):
        model.model_validate({**VALID, 'correo': email, 'rol': 'staff'})


@pytest.mark.parametrize('field,value,expected', [
    ('nombre', ' ', 'obligatorio'), ('dni', '', 'DNI es obligatorio'),
    ('dni', '1234567', 'exactamente 8'), ('dni', '12ab5678', 'exactamente 8'),
    ('telefono', '', 'teléfono es obligatorio'), ('telefono', '123456', 'entre 7 y 9'),
    ('telefono', '1234567890', 'entre 7 y 9'), ('telefono', '987 65432', 'sin espacios ni letras'),
    ('password', '', 'al menos 6'), ('password', '12345', 'al menos 6'),
])
def test_public_registration_reports_specific_field_errors(field, value, expected):
    with pytest.raises(ValidationError, match=expected):
        RegistroPublicoClienteInput.model_validate({**VALID, field: value})


@pytest.mark.parametrize('path', ['/api/registro-publico', '/api/clientes', '/api/clientes/registro-admin', '/api/usuarios'])
@pytest.mark.parametrize('field,value', [('correo', 'ana@example.org'), ('dni', 'bad'), ('telefono', 'bad')])
def test_invalid_account_requests_do_not_reach_writes_or_checkout(path, field, value):
    calls = []
    def record(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError('No debe guardar ni abrir Stripe con datos inválidos')
    fake = SimpleNamespace(register_public=record, register_admin=record, upsert_client=record, upsert_user=record)
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(clients_routes.router, prefix='/api')
    app.include_router(users_routes.router, prefix='/api')
    for dependency in (deps.get_clients_service, deps.get_users_service, deps.get_client_payments_service):
        app.dependency_overrides[dependency] = lambda: fake
    app.dependency_overrides[deps.get_current_user] = lambda: UserProfile(
        id='SGADM001', name='Admin', email='admin@example.com', role='admin')
    response = TestClient(app).post(path, json={**VALID, 'rol': 'staff', field: value})
    assert response.status_code == 422, response.text
    assert response.json()['detail'][0]['loc'] == ['body', field]
    assert 'input' not in response.json()['detail'][0]
    assert calls == []


@pytest.mark.parametrize('method', ['upsert_usuario', 'upsert_cliente', 'registrar_cliente_publico'])
def test_domain_commands_cannot_bypass_email_validation(method):
    gym = LocalGymService()
    before = deepcopy(gym.state)
    with pytest.raises(ValueError, match='Solo se permiten correos'):
        getattr(gym, method)({**VALID, 'correo': 'ana@example.org', 'rol': 'staff'})
    # The repository initializes identity metadata on its first command.
    assert {key: value for key, value in gym.state.items() if not key.startswith('_')} == before


def test_verified_google_email_cannot_bypass_domain_validation():
    gym = LocalGymService()
    gym.identity = SimpleNamespace(verify=lambda _: dict(email='ana@company.org', sub='verified', name='Ana'))
    gym.sessions = SimpleNamespace(validate_configuration=lambda: None)
    with pytest.raises(ValueError, match='Solo se permiten correos'):
        ClientsService(gym).register_public_client({**VALID, 'correo': 'ana@company.org', 'google_credential': 'fake'})
    assert gym.state['clientes'] == []
    assert gym.state['membresia'] == []


@pytest.mark.parametrize('method,identity', [('upsert_usuario', 'id_usuario'), ('upsert_cliente', 'id_usuario')])
@pytest.mark.parametrize('field', ['correo', 'dni'])
def test_duplicate_accounts_fail_without_mutation_and_allow_editing_self(method, identity, field):
    gym = LocalGymService()
    save = getattr(gym, method)
    first = save({**VALID, 'rol': 'staff', 'estado': 'EN_TRAMITE'})
    before = deepcopy(gym.state)
    second = {**VALID, 'nombre': 'Otra', 'correo': 'otra@hotmail.com', 'dni': '87654321', 'rol': 'staff', 'estado': 'EN_TRAMITE'}
    second[field] = first[field]
    with pytest.raises(ValueError, match='Ya existe una cuenta'):
        save(second)
    assert gym.state == before
    assert save({**first, 'password': '', 'nombre': 'Ana editada'})[identity] == first[identity]


def test_plan_price_preserves_cents_from_http_schema_through_domain_save():
    payload = PlanMembresiaInput(nombre_plan='Especial', duracion='30 dias', precio=79.90)
    saved = LocalGymService().upsert_plan_membresia(payload.model_dump())
    assert saved['precio'] == 79.90


@pytest.mark.parametrize('field,value,expected', [('cliente_correo', 'ana@example.org', 'Solo se permiten correos'),
                                                 ('cliente_dni', '123abc', 'exactamente 8')])
def test_order_customer_details_reject_invalid_email_and_dni(field, value, expected):
    from domain.models.gym import PedidoTiendaInput, PedidoTiendaCheckoutInput
    for model in (PedidoTiendaInput, PedidoTiendaCheckoutInput):
        with pytest.raises(ValidationError, match=expected):
            model.model_validate({field: value, 'items': [{'id_producto': 1, 'cantidad': 1}]})
