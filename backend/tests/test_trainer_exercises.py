import unittest
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


if __name__ == "__main__":
    unittest.main()
