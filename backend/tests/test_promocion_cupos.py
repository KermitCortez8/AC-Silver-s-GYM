import pytest
from services.gym_domain_service import GymDomainService


def test_promocion_limite_cupos_exhaustion():
    service = GymDomainService.__new__(GymDomainService)
    service._save = lambda: None
    state = service._seed()

    # Normalización de promoción con límite de 2 cupos para el plan MENSUAL (id_pm: 1)
    promo = service._normalize_promocion({
        "id_promocion": 10,
        "nombre": "Flash Cupos",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 50.0,
        "planes_aplicables": [1],
        "limite_cupos": 2,
        "usos_actuales": 1,
        "activo": True
    }, fallback_id=10)

    state["promociones"] = [promo]

    assert promo["limite_cupos"] == 2
    assert promo["usos_actuales"] == 1

    # Verifica que la promo sigue vigente para el plan 1
    v = service.get_promocion_vigente_para_plan(state, 1)
    assert v is not None
    assert v["id_promocion"] == 10

    # Simular que se usa 1 cupo más (usos_actuales -> 2)
    promo["usos_actuales"] = 2

    # Ahora con usos_actuales (2) >= limite_cupos (2), debe ser ignorada por estar agotada
    v2 = service.get_promocion_vigente_para_plan(state, 1)
    assert v2 is None
