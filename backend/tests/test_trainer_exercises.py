import unittest
from copy import deepcopy
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dependencies import get_gym_service, require_internal_viewer
from routes.trainer_routes import router
from services.supabase_gym_service import SupabaseGymService
from services.local_gym_service import LocalGymService


class TestTrainerExercises(unittest.TestCase):
    def setUp(self):
        self.service = LocalGymService()

    def test_upsert_rutina_with_ejercicios(self):
        payload = {
            "servicio": "musculacion",
            "nombre_rutina": "Hipertrofia Pecho y Triceps",
            "zonas_musculares": "Pectorales, Triceps",
            "color": "Azul",
            "ejercicios": [
                {
                    "nombre_ejercicio": "Press de Banca Plano",
                    "series": 4,
                    "repeticiones": "10-12",
                    "descanso_segundos": 90,
                    "peso_sugerido_kg": 60.0,
                    "notas": "Técnica estricta",
                },
                {
                    "nombre_ejercicio": "Press Inclinado con Mancuernas",
                    "series": 3,
                    "repeticiones": "12",
                    "descanso_segundos": 60,
                    "peso_sugerido_kg": 22.5,
                    "notas": "Mantener codos a 45 grados",
                },
            ],
        }
        created = self.service.upsert_rutina(payload)
        self.assertIsNotNone(created.get("id_rutina"))
        self.assertEqual(len(created.get("ejercicios", [])), 2)
        self.assertEqual(created["ejercicios"][0]["nombre_ejercicio"], "Press de Banca Plano")
        self.assertEqual(created["ejercicios"][0]["series"], 4)

    def test_registrar_progreso_rutina_with_ejercicios_detalle(self):
        # 1. Crear rutina
        routine = self.service.upsert_rutina({
            "servicio": "fitness",
            "nombre_rutina": "Rutina Funcional",
            "zonas_musculares": "Core, Piernas",
            "ejercicios": [
                {"nombre_ejercicio": "Sentadillas", "series": 3, "repeticiones": "15", "descanso_segundos": 45}
            ]
        })
        # 2. Asignar matricula
        state = self.service.state
        state["matriculas_horario"] = [
            {
                "id_matricula": 10,
                "id_cliente": 1,
                "id_horario_servicio": 1,
                "id_rutina": routine["id_rutina"],
                "estado": "ACTIVA",
            }
        ]
        # 3. Registrar progreso con detalle
        progreso_payload = {
            "fecha": "2026-10-01",
            "observacion": "Completó la sesión con buen ritmo",
            "ejercicios_detalle": [
                {
                    "nombre_ejercicio": "Sentadillas",
                    "completado": True,
                    "series_completadas": 3,
                    "repeticiones_logradas": "15",
                    "peso_utilizado_kg": 30.0,
                    "observaciones": "Buena profundidad",
                }
            ],
        }
        res = self.service.registrar_progreso_rutina(10, progreso_payload)
        self.assertEqual(res["id_matricula"], 10)
        self.assertEqual(len(res.get("ejercicios_detalle", [])), 1)
        self.assertEqual(res["ejercicios_detalle"][0]["nombre_ejercicio"], "Sentadillas")
        self.assertTrue(res["ejercicios_detalle"][0]["completado"])


def test_trainer_api_preserves_exercises_in_catalog_and_session_history():
    gym = LocalGymService()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_gym_service] = lambda: gym
    app.dependency_overrides[require_internal_viewer] = lambda: None
    client = TestClient(app)
    exercises = [{
        "id_ejercicio": "press", "nombre_ejercicio": "Press banca", "series": 4,
        "repeticiones": "8-12", "descanso_segundos": 90, "peso_sugerido_kg": 30,
    }]
    response = client.post("/trainer/rutinas", json={
        "servicio": "musculacion", "nombre_rutina": "Fuerza",
        "zonas_musculares": "Pecho", "ejercicios": exercises,
    })
    assert response.status_code == 200
    routine = response.json()
    assert routine["ejercicios"][0]["id_ejercicio"] == "press"
    assert routine["ejercicios"][0]["series"] == 4
    overview = client.get("/trainer/overview").json()
    assert overview["routines"][0]["ejercicios"] == routine["ejercicios"]
    gym.state["matriculas_horario"] = [{
        "id_matricula": 10, "id_cliente": 1, "id_horario_servicio": 1,
        "id_rutina": routine["id_rutina"], "estado": "ACTIVA",
    }]
    progress = client.post("/trainer/matriculas/10/progreso", json={
        "fecha": "2026-10-01", "estado": "REALIZADO", "observacion": "Sesión completa",
        "ejercicios_detalle": [{
            "id_ejercicio": "press", "nombre_ejercicio": "Press banca", "completado": True,
            "series_completadas": 4, "repeticiones_logradas": "10", "peso_utilizado_kg": 30,
        }],
    })
    assert progress.status_code == 200
    saved = progress.json()
    assert saved["estado"] == "REALIZADO"
    assert saved["ejercicios_detalle"][0]["peso_utilizado_kg"] == 30
    # Simulate reloading persisted state to ensure details survive normalization.
    gym.state = gym._normalize(deepcopy(gym.state))
    assert gym.state["rutina_progreso"][0]["ejercicios_detalle"] == saved["ejercicios_detalle"]


def test_supabase_exercise_data_survives_json_serialization_and_legacy_rows():
    service = object.__new__(SupabaseGymService)
    routine = {
        "id_rutina": 1, "nombre_rutina": "Fuerza", "servicio": "musculacion",
        "ejercicios": [{"nombre_ejercicio": "Press", "series": 4}],
    }
    remote = service._routine_to_remote(routine)
    remote["ejercicios"] = json.dumps(remote["ejercicios"])
    assert service._map_routine(remote)["ejercicios"] == routine["ejercicios"]
    progress = {
        "id_progreso": 1, "id_matricula": 10, "id_rutina": 1, "fecha": "2026-10-01",
        "estado": "REALIZADO", "ejercicios_detalle": [{"series_completadas": 4}],
    }
    remote = service._routine_progress_to_remote(progress)
    remote["ejercicios_detalle"] = json.dumps(remote["ejercicios_detalle"])
    assert service._map_routine_progress(remote)["ejercicios_detalle"] == progress["ejercicios_detalle"]
    assert service._map_routine({"id_rutina": 1})["ejercicios"] == []
    assert service._map_routine_progress({"id_progreso": 1})["ejercicios_detalle"] == []


@pytest.mark.parametrize("table,column", [
    ("CATALOGO_RUTINA", "ejercicios"),
    ("RUTINA_PROGRESO", "ejercicios_detalle"),
])
def test_missing_exercise_migration_does_not_silently_discard_data(table, column):
    service = object.__new__(SupabaseGymService)
    service.remote_columns = {table: {"id_rutina"}}
    with pytest.raises(RuntimeError, match="012_trainer_exercises.sql"):
        service._filter_remote_columns(table, {column: [{"nombre_ejercicio": "Press"}]})


def test_assignment_does_not_swallow_unknown_database_errors(monkeypatch):
    from services.gym_domain_service import GymDomainService
    service = object.__new__(SupabaseGymService)

    def fail(*args):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(GymDomainService, "asignar_rutina_matricula", fail)
    with pytest.raises(RuntimeError, match="database unavailable"):
        service.asignar_rutina_matricula(10, 1)
