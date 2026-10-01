import pytest
from pydantic import ValidationError

from models.gym import MembresiaInput
from services.clients_service import ClientsService
from services.local_gym_service import LocalGymService
from services.supabase_gym_service import SupabaseGymService


def test_registration_payment_activation_and_expiry_use_only_three_states(monkeypatch):
    monkeypatch.setattr('services.gym_domain_service._today_iso', lambda: '2026-10-01')
    gym = LocalGymService()
    result = ClientsService(gym).register_admin_client({
        'nombre': 'Estados Cliente', 'correo': 'estados@example.com',
        'dni': '12345678', 'password': 'secreto123', 'plan': 'MENSUAL',
    })
    client_id = result['cliente']['id_cliente']
    membership = gym.state['membresia'][0]
    assert membership['estado'] == 'EN_TRAMITE'
    assert membership['estado_pago'] == 'PENDIENTE'
    gym.confirmar_pago_manual_cliente(client_id)
    assert membership['estado'] == 'EN_TRAMITE'
    assert membership['estado_pago'] == 'PAGADO'
    gym.activar_membresia_cliente(client_id)
    assert membership['estado'] == 'ACTIVO'
    membership['fecha_fin'] = '2026-09-30'
    gym.expire_memberships()
    assert membership['estado'] == 'VENCIDA'
    assert membership['estado_pago'] == 'PAGADO'
    assert gym.clientes_normalized()[0]['membership_status'] == 'VENCIDA'


@pytest.mark.parametrize('state', ['INACTIVO', 'PENDIENTE_PAGO', 'BLOQUEADA', 'OTRO'])
def test_membership_input_rejects_fourth_states(state):
    with pytest.raises(ValidationError):
        MembresiaInput(id_cliente=1, id_pm=1, fecha_inicio='', fecha_fin='', estado=state)


def test_legacy_pending_state_does_not_become_paid_when_normalized():
    gym = object.__new__(SupabaseGymService)
    membership = gym._map_membership({
        'id_membresia': 1, 'id_cliente': 1, 'Estado': 'PENDIENTE_PAGO',
    })
    assert membership['estado'] == 'EN_TRAMITE'
    assert membership['estado_pago'] == 'PENDIENTE'
    remote = gym._membership_to_remote(membership)
    assert remote['Estado'] == 'EN_TRAMITE'
    assert remote['estado_pago'] == 'PENDIENTE'


def test_new_membership_stays_in_progress_until_paid_and_activated():
    gym = LocalGymService()
    result = ClientsService(gym).register_admin_client({
        'nombre': 'Renovacion Cliente', 'correo': 'renovacion@example.com',
        'dni': '87654321', 'password': 'secreto123', 'plan': 'MENSUAL',
    })
    membership = gym.crear_membresia({
        'id_cliente': result['cliente']['id_cliente'],
        'id_pm': result['membresia']['id_pm'], 'estado': 'ACTIVO',
    })
    assert membership['estado'] == 'EN_TRAMITE'
    assert membership['estado_pago'] == 'PENDIENTE'
    with pytest.raises(ValueError, match='sin pago confirmado'):
        gym.activar_membresia_cliente(result['cliente']['id_cliente'])


def test_editing_or_loading_expired_client_does_not_create_an_active_renewal(monkeypatch):
    monkeypatch.setattr('services.gym_domain_service._today_iso', lambda: '2026-10-01')
    gym = LocalGymService()
    client = gym.upsert_cliente({
        'nombre': 'Cliente Anterior', 'correo': 'anterior@example.com',
        'dni': '11223344', 'estado': 'ACTIVO', 'password': 'secreto123',
    })
    membership = gym.state['membresia'][0]
    assert membership['estado'] == 'EN_TRAMITE'
    assert membership['estado_pago'] == 'PENDIENTE'
    membership.update(estado='Activa', estado_pago='PAGADO', fecha_fin='2026-09-30')
    client['estado'] = 'ACTIVO'
    normalized = gym._normalize(gym.state)
    assert len(normalized['membresia']) == 1
    assert normalized['membresia'][0]['fecha_fin'] == '2026-09-30'
    gym.state = normalized
    gym.expire_memberships()
    assert membership['estado'] == 'VENCIDA'
    assert gym.state['clientes'][0]['estado'] == 'VENCIDA'
