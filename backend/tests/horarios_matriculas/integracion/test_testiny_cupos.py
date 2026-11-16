"""TC-135: reducción según la sesión más ocupada, sin sumar semanas."""
import pytest

from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


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
