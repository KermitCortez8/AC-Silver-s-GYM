"""Casos documentados de rutinas: API, reglas y relectura del estado QA."""

import pytest

from tests.soporte.testiny_api import business_state, documented_api  # noqa: F401


ROUTINE = {"nombre_rutina": "Rutina QA", "servicio": "fitness", "zonas_musculares": "Piernas", "color": "Azul",
           "ejercicios": [{"id_ejercicio": "sentadilla", "nombre_ejercicio": "Sentadilla", "series": 3,
                           "peso_sugerido_kg": 0}]}


def routine(api, **changes):
    response = api.client.post("/api/trainer/rutinas", json={**ROUTINE, **changes})
    assert response.status_code == 200, response.text
    return response.json()


def enrollment(api, assigned=True, active=True):
    saved = routine(api)
    api.gym.state["horarios_servicio"] = [{"id_horario_servicio": 7, "servicio": "fitness", "activo": True,
                                           "dia": "miercoles", "hora_inicio": "10:00", "hora_fin": "11:00", "cupos": 5}]
    api.gym.state["matriculas_horario"] = [{"id_matricula": 10, "id_cliente": 1, "id_horario_servicio": 7,
                                           "id_rutina": saved["id_rutina"] if assigned else None,
                                           "estado": "ACTIVA" if active else "CANCELADA", "fecha_clase": "2026-10-07"}]
    return saved


def test_tc109_panel_consolida_cliente_matricula_rutina_y_horario(documented_api):
    api = documented_api
    api.login("trainer")
    saved = enrollment(api)
    before = business_state(api)
    response = api.client.get("/api/trainer/overview")
    assert response.status_code == 200, response.text
    overview = response.json()
    assert overview["stats"]["clientes_en_horario"] == 1
    assert overview["stats"]["matriculas_activas"] == 1
    assert overview["stats"]["rutinas"] == 1
    assert overview["routine_supervision"][0]["id_cliente"] == 1
    assert overview["routine_supervision"][0]["rutina_nombre"] == saved["nombre_rutina"]
    assert overview["schedule_monitor"][0]["id_horario_servicio"] == 7
    assert business_state(api) == before


def test_tc110_panel_vacio_no_inventa_pendientes_ni_escribe(documented_api):
    api = documented_api
    api.login("trainer")
    before = business_state(api)
    overview = api.client.get("/api/trainer/overview").json()
    assert overview["routine_supervision"] == overview["schedule_monitor"] == overview["routines"] == []
    assert all(value == 0 for value in overview["stats"].values())
    assert business_state(api) == before


def test_tc112_tc113_crear_y_reconsultar_rutina_con_ejercicios(documented_api):
    api = documented_api
    api.login("trainer")
    saved = routine(api)
    before = business_state(api)
    [loaded] = api.client.get("/api/trainer/overview").json()["routines"]
    assert loaded["id_rutina"] == saved["id_rutina"]
    assert loaded["nombre_rutina"] == "Rutina QA" and loaded["zonas_musculares"] == "Piernas"
    assert loaded["ejercicios"] == saved["ejercicios"]
    assert loaded["ejercicios"][0]["peso_sugerido_kg"] == 0
    assert business_state(api) == before


def test_tc114_editar_rutina_conserva_identidad_y_otra_rutina(documented_api):
    api = documented_api
    api.login("trainer")
    saved = routine(api)
    control = routine(api, nombre_rutina="Control QA")
    updated = routine(api, **{**saved, "nombre_rutina": "Rutina actualizada", "zonas_musculares": "Core"})
    assert updated["id_rutina"] == saved["id_rutina"]
    catalog = api.client.get("/api/trainer/overview").json()["routines"]
    assert len(catalog) == 2
    assert next(row for row in catalog if row["id_rutina"] == updated["id_rutina"])["zonas_musculares"] == "Core"
    assert next(row for row in catalog if row["id_rutina"] == control["id_rutina"])["nombre_rutina"] == "Control QA"


@pytest.mark.parametrize("field", ["nombre_rutina", "servicio"])
def test_tc080_tc115_rutina_incompleta_no_se_guarda(documented_api, field):
    api = documented_api
    before = business_state(api)
    response = api.client.post("/api/trainer/rutinas", json={**ROUTINE, field: ""})
    assert response.status_code == 422, response.text
    assert business_state(api) == before


def test_tc080_programacion_incompleta_no_se_guarda(documented_api):
    api = documented_api
    before = business_state(api)
    response = api.client.post("/api/gym/horarios", json={"id_cliente": 1})
    assert response.status_code == 422, response.text
    assert business_state(api) == before


@pytest.mark.parametrize("changes", [{"servicio": "otro"}, {"ejercicios": [{"nombre_ejercicio": "", "peso_sugerido_kg": 1}]},
                                      {"ejercicios": [{"nombre_ejercicio": "Sentadilla", "peso_sugerido_kg": -1}]}])
def test_tc116_datos_invalidos_de_rutina_no_modifican_catalogo(documented_api, changes):
    api = documented_api
    saved = routine(api)
    before = business_state(api)
    response = api.client.post("/api/trainer/rutinas", json={**saved, **changes})
    assert response.status_code == 422, response.text
    assert business_state(api) == before


def test_tc117_asignacion_compatible_persiste_en_matricula(documented_api):
    api = documented_api
    api.login("trainer")
    saved = enrollment(api, assigned=False)
    result = api.client.post("/api/trainer/matriculas/10/rutina", json={"id_rutina": saved["id_rutina"]})
    assert result.status_code == 200, result.text
    [loaded] = api.client.get("/api/trainer/clientes-rutinas?dni=11111111").json()["matriculas"]
    assert loaded["id_rutina"] == saved["id_rutina"]
    assert loaded["id_cliente"] == 1 and loaded["id_horario_servicio"] == 7


def test_tc118_no_asigna_a_matricula_cancelada(documented_api):
    api = documented_api
    saved = enrollment(api, assigned=False, active=False)
    before = business_state(api)
    response = api.client.post("/api/trainer/matriculas/10/rutina", json={"id_rutina": saved["id_rutina"]})
    assert response.status_code == 400 and "ACTIVA" in response.text
    assert business_state(api) == before


def test_tc119_rechaza_rutina_de_otro_servicio_y_conserva_matricula(documented_api):
    api = documented_api
    enrollment(api, assigned=False)
    wrong = routine(api, servicio="baile", nombre_rutina="Baile QA")
    before = business_state(api)
    response = api.client.post("/api/trainer/matriculas/10/rutina", json={"id_rutina": wrong["id_rutina"]})
    assert response.status_code == 400 and "no corresponde" in response.text
    assert business_state(api) == before


def test_tc120_consulta_dni_recupera_solo_su_rutina_y_progreso(documented_api):
    api = documented_api
    saved = enrollment(api)
    api.gym.state["rutina_progreso"] = [{"id_progreso": 1, "id_matricula": 10, "id_rutina": saved["id_rutina"],
                                        "fecha": "2026-10-07", "estado": "REALIZADO", "observacion": "QA"}]
    before = business_state(api)
    loaded = api.client.get("/api/trainer/clientes-rutinas?dni=11111111").json()
    assert loaded["cliente"]["dni"] == "11111111"
    [row] = loaded["matriculas"]
    assert row["id_rutina"] == saved["id_rutina"] and row["id_horario_servicio"] == 7
    assert row["progreso"][0]["estado"] == "REALIZADO"
    assert business_state(api) == before


def test_tc079_tc121_cliente_inexistente_no_se_asocia_ni_muestra_otro(documented_api):
    api = documented_api
    enrollment(api)
    before = business_state(api)
    response = api.client.get("/api/trainer/clientes-rutinas?dni=99999999")
    assert response.status_code == 404 and "Cliente no encontrado" in response.text
    assert business_state(api) == before


def test_tc122_cliente_sin_asignaciones_tiene_consulta_vacia(documented_api):
    api = documented_api
    before = business_state(api)
    result = api.client.get("/api/trainer/clientes-rutinas?dni=11111111").json()
    assert result["cliente"]["dni"] == "11111111" and result["matriculas"] == []
    assert business_state(api) == before


def test_tc123_tc143_progreso_persiste_detalle_y_autor_de_sesion(documented_api):
    api = documented_api
    api.login("trainer")
    enrollment(api)
    payload = {"fecha": "2026-10-07", "estado": "REALIZADO", "observacion": "Sesión QA",
               "id_usuario": "SGUSU999", "ejercicios_detalle": [
                   {"id_ejercicio": "sentadilla", "nombre_ejercicio": "Sentadilla", "completado": True,
                    "peso_utilizado_kg": 0, "series_completadas": 3, "repeticiones_logradas": "12"}]}
    response = api.client.post("/api/trainer/matriculas/10/progreso", json=payload)
    assert response.status_code == 200, response.text
    loaded = api.client.get("/api/trainer/clientes-rutinas?dni=11111111").json()["matriculas"][0]["progreso"][0]
    assert loaded["estado"] == "REALIZADO" and loaded["observacion"] == "Sesión QA"
    assert loaded["id_usuario"] == "SGADM001"
    assert loaded["ejercicios_detalle"][0]["peso_utilizado_kg"] == 0
    assert loaded["ejercicios_detalle"][0]["completado"] is True


def test_tc124_no_registra_progreso_sin_rutina_asignada(documented_api):
    api = documented_api
    enrollment(api, assigned=False)
    before = business_state(api)
    response = api.client.post("/api/trainer/matriculas/10/progreso", json={"estado": "REALIZADO"})
    assert response.status_code == 400 and "rutina asignada" in response.text
    assert business_state(api) == before


@pytest.mark.parametrize("details", [[{"id_ejercicio": "sentadilla", "peso_utilizado_kg": -1}],
                                    [{"nombre_ejercicio": "", "series_completadas": 3}]])
def test_tc125_datos_invalidos_de_progreso_no_se_guardan(documented_api, details):
    api = documented_api
    enrollment(api)
    before = business_state(api)
    response = api.client.post("/api/trainer/matriculas/10/progreso", json={"ejercicios_detalle": details})
    assert response.status_code == 422, response.text
    assert business_state(api) == before
