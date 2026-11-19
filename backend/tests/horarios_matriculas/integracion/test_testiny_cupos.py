"""TC-135: reducción según la sesión más ocupada, sin sumar semanas."""
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from application.services.attendance_service import AttendanceService, LIMA
from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


@pytest.mark.parametrize("invalid", [0, -1, 2.5, "texto"])
def test_tc051_tc052_capacidad_valida_se_aplica_al_aforo_y_rechaza_valores_invalidos(documented_api, invalid, monkeypatch):
    api = documented_api
    url = "/api/gym/configuracion"
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-07")
    before = api.client.get(url).json()
    invalid_response = api.client.post(url, json={"capacidad_total": invalid, "capacidad_por_hora": 1})
    assert invalid_response.status_code == 422 and "capacidad_total" in invalid_response.text
    assert api.client.get(url).json() == before

    changed = {"capacidad_total": 1, "capacidad_por_hora": 1}
    assert api.client.post(url, json=changed).json() == changed
    assert api.client.get(url).json() == changed
    attendance = AttendanceService(api.gym, clock=lambda: datetime(2026, 10, 7, 10, tzinfo=LIMA))
    actor = SimpleNamespace(role="admin", id_usuario="SGADM001", name="Administrador QA")
    first = attendance.enter_general("11111111", str(uuid4()), actor)
    assert attendance.summary(actor)["disponibles"] == 0
    with pytest.raises(ValueError, match="aforo"):
        attendance.enter_general("22222222", str(uuid4()), actor)
    assert len(api.gym.state["asistencia"]) == 1
    attendance.exit(first["id_asistencia"], actor)
    assert attendance.summary(actor)["disponibles"] == 1


def test_tc135_limite_de_capacidad_compara_maximo_por_fecha(documented_api, monkeypatch):
    api = documented_api
    monkeypatch.setattr("domain.services.gym_domain_service._today_iso", lambda: "2026-10-07")
    routine = api.gym.upsert_rutina({"nombre_rutina": "Cupos QA", "servicio": "fitness", "zonas_musculares": "Core"})
    saved = api.gym.upsert_horario_servicio({"servicio": "fitness", "id_rutina": routine["id_rutina"],
        "codigo_dia": "LUN", "dia": "lunes", "hora_inicio": "10:00", "hora_fin": "11:00", "cupos": 3, "activo": True})
    api.gym.state["matriculas_horario"] = [
        {"id_matricula": 1, "id_cliente": 1, "id_horario_servicio": saved["id_horario_servicio"], "fecha_clase": "2026-10-12", "estado": "ACTIVA"},
        {"id_matricula": 2, "id_cliente": 2, "id_horario_servicio": saved["id_horario_servicio"], "fecha_clase": "2026-10-12", "estado": "ACTIVA"},
        {"id_matricula": 3, "id_cliente": 1, "id_horario_servicio": saved["id_horario_servicio"], "fecha_clase": "2026-10-19", "estado": "ACTIVA"},
    ]
    before = business_state(api)
    with pytest.raises(ValueError, match="reducir cupos"):
        api.gym.upsert_horario_servicio({**saved, "cupos": 1})
    assert business_state(api) == before
    result = api.gym.upsert_horario_servicio({**saved, "cupos": 2})
    assert result["cupos"] == 2
    [loaded] = api.gym.horarios_servicio()
    assert loaded["ocupacion_por_fecha"] == {"2026-10-12": 2, "2026-10-19": 1}
    assert loaded["cupos"] - loaded["ocupacion_por_fecha"]["2026-10-12"] == 0
    assert loaded["cupos"] - loaded["ocupacion_por_fecha"]["2026-10-19"] == 1
    assert api.gym.state["matriculas_horario"] == before["matriculas_horario"]
