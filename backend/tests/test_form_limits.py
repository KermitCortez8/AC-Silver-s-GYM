"""Fronteras de escritura: no se recortan silenciosamente peticiones a la API."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from domain.models.attendance import AttendanceAnnulment, AttendanceCorrection
from domain.models.gym import (
    ClienteInput, UsuarioInput, RegistroPublicoClienteInput,
    PlanMembresiaInput, PromocionInput, HorarioServicioInput,
    InventarioInput, MovimientoInventarioInput, MovimientoInventarioUpdateInput,
)
from infrastructure.services.local_gym_service import LocalGymService


ACCOUNT = dict(nombre="Ana", correo="ana@example.com", dni="01234567",
               telefono="012345678", password="secreto", rol="staff")
PLAN = dict(nombre_plan="Plan", duracion="30 días", precio=80)
PROMOTION = dict(nombre="Oferta", valor_descuento=10)
SCHEDULE = dict(servicio="fitness", id_rutina=1)
INVENTORY = dict(nombre_item="Pesa", tipo="Equipo", cantidad_stock=1)
MOVEMENT = dict(id_item=1, id_usuario=1, tipo_movimiento="entrada")


@pytest.mark.parametrize("model,payload,field,maximum", [
    *[(model, ACCOUNT, "nombre", 50) for model in
      (ClienteInput, UsuarioInput, RegistroPublicoClienteInput)],
    (PlanMembresiaInput, PLAN, "nombre_plan", 50),
    (PlanMembresiaInput, PLAN, "descripcion", 150),
    (PlanMembresiaInput, PLAN, "beneficios", 150),
    (PromocionInput, PROMOTION, "nombre", 50),
    (PromocionInput, PROMOTION, "descripcion", 150),
    (PromocionInput, PROMOTION, "palabra_clave", 50),
    (HorarioServicioInput, SCHEDULE, "codigo_dia", 50),
    (InventarioInput, INVENTORY, "nombre_item", 40),
    (InventarioInput, INVENTORY, "tipo", 40),
    (InventarioInput, INVENTORY, "ubicacion", 40),
    (InventarioInput, INVENTORY, "unidad_venta", 40),
    (InventarioInput, INVENTORY, "observaciones", 100),
    (MovimientoInventarioInput, MOVEMENT, "descripcion", 100),
    (MovimientoInventarioUpdateInput, {}, "descripcion", 100),
    (AttendanceAnnulment, {"version": 0}, "motivo", 150),
    (AttendanceCorrection, {"version": 0, "fecha": "2026-11-02", "hora_entrada": "10:00"}, "motivo", 150),
])
def test_field_accepts_limit_and_rejects_one_more(model, payload, field, maximum):
    valid = model.model_validate({**payload, field: "Á" * maximum})
    assert getattr(valid, field) == "Á" * maximum
    with pytest.raises(ValidationError):
        model.model_validate({**payload, field: "Á" * (maximum + 1)})


@pytest.mark.parametrize("model", [ClienteInput, UsuarioInput, RegistroPublicoClienteInput])
def test_account_identity_keeps_leading_zeroes_and_requires_nine_phone_digits(model):
    valid = model.model_validate(ACCOUNT)
    assert valid.dni == "01234567"
    assert valid.telefono == "012345678"
    for phone in ("1234567", "12345678", "1234567890", "12345abcd"):
        with pytest.raises(ValidationError):
            model.model_validate({**ACCOUNT, "telefono": phone})
    for length in (50, 51):
        email = "a" * (length - 12) + "@example.com"
        if length == 50:
            assert model.model_validate({**ACCOUNT, "correo": email}).correo == email
        else:
            with pytest.raises(ValidationError):
                model.model_validate({**ACCOUNT, "correo": email})


@pytest.mark.parametrize("method,payload", [
    ("upsert_cliente", {**ACCOUNT, "nombre": "A" * 51}),
    ("upsert_usuario", {**ACCOUNT, "nombre": "A" * 51}),
    ("upsert_plan_membresia", {**PLAN, "nombre_plan": "P" * 51}),
    ("upsert_plan_membresia", {**PLAN, "descripcion": "D" * 151}),
    ("upsert_promocion", {**PROMOTION, "nombre": "P" * 51}),
    ("upsert_promocion", {**PROMOTION, "descripcion": "D" * 151}),
])
def test_direct_commands_cannot_bypass_limits_or_mutate_state(method, payload):
    gym = LocalGymService()
    before = deepcopy(gym.state)
    with pytest.raises(ValueError, match="superar"):
        getattr(gym, method)(payload)
    assert {key: value for key, value in gym.state.items() if not key.startswith("_")} == before
