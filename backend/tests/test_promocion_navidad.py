import pytest
import threading
from datetime import datetime, timezone
from services.gym_domain_service import GymDomainService, _today_iso

class MockSupabaseService(GymDomainService):
    def __init__(self):
        self.lock = threading.Lock()
        self.state = self._seed()
        self.saved_states = []

    def _load(self):
        return self.state

    def _save(self):
        self.saved_states.append(self.state)

def test_prevent_promocion_overlap():
    service = MockSupabaseService()
    today = _today_iso()

    # Promo 1: 20% en Plan Anual (id_pm=3)
    promo1 = service.upsert_promocion({
        "nombre": "Navidad 1",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 20.0,
        "fecha_inicio": today,
        "fecha_fin": "",
        "activo": True,
        "planes_aplicables": [3]
    })
    assert promo1["id_promocion"] > 0

    # Promo 2 con solapamiento: Intentar crear otra promo activa en plan Anual (id_pm=3) -> debe fallar (400)
    with pytest.raises(ValueError, match="Ya existe una promoción vigente"):
        service.upsert_promocion({
            "nombre": "Navidad 2",
            "tipo_descuento": "monto",
            "valor_descuento": 50.0,
            "fecha_inicio": today,
            "fecha_fin": "",
            "activo": True,
            "planes_aplicables": [3]
        })

    # Promo en plan Mensual (id_pm=1) -> debe permitirse porque no comparte planes
    promo_mensual = service.upsert_promocion({
        "nombre": "Promo Mensual",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 10.0,
        "fecha_inicio": today,
        "fecha_fin": "",
        "activo": True,
        "planes_aplicables": [1]
    })
    assert promo_mensual["id_promocion"] > 0

def test_promociones_vigentes_publicas_and_autoapply():
    service = MockSupabaseService()
    today = _today_iso()

    service.upsert_promocion({
        "nombre": "Navidad Especial",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 20.0,
        "fecha_inicio": today,
        "fecha_fin": "",
        "activo": True,
        "planes_aplicables": [3]
    })

    vigentes = service.promociones_vigentes_publicas()
    assert len(vigentes) == 1
    assert vigentes[0]["nombre"] == "Navidad Especial"
    assert vigentes[0]["valor_descuento"] == 20.0
    assert vigentes[0]["planes_aplicables"] == [3]

    # Test auto-aplicación en registro público del plan ANUAL
    result = service.registrar_cliente_publico({
        "nombre": "Cliente Navidad",
        "correo": "navidad@gym.com",
        "telefono": "999888777",
        "dni": "87654321",
        "password": "password123",
        "plan": "ANUAL",
    })

    # Plan Anual base es 699, con 20% OFF debe dar 559.2 (round(699 * 0.8, 2) = 559.2)
    assert result["membresia"]["monto_pago"] == 559.2
    assert result["cliente"]["promocion"] == "Navidad Especial"
