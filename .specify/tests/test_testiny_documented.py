"""Regresión del porcentaje por casos y de su trazabilidad; sin Testiny remoto."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("gym_documented_cases_tests", ROOT / ".github/scripts/testiny/documented_cases.py")
documented = importlib.util.module_from_spec(spec)
spec.loader.exec_module(documented)


class DocumentedCasesTests(unittest.TestCase):
    def test_revision_del_repositorio_coincide_con_las_pruebas_actuales(self):
        # Detectar revisiones obsoletas al validar el PR, antes de publicar.
        documented.load_review(ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gym cobertura ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root / ".specify/base/testiny"
        self.base.mkdir(parents=True)
        self.source = self.root / "backend/tests/test_qa.py"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("# Fixture de contrato; no se ejecuta.\n", encoding="utf-8")
        self.cases = {i: {"id": i, "codigo": f"SG-RF01-QA{i}", "titulo": f"Caso {i}", "huella": f"case-{i}",
                           "modulo": "MOD-01", "nombre_modulo": "Identidad y acceso", "rf": ["RF01"],
                           "cus": "CUS01", "tipo": "Funcional", "url": f"https://app.testiny.io/SILVE/testcases/tc/{i}/edit",
                           "pasos": [{"accion": "Actuar", "esperado": "Estado correcto"}, {"accion": "Consultar", "esperado": "Sin cambios ajenos"}]}
                      for i in (1, 2, 3)}
        self.catalog = {"proyecto": "SILVE", "total": 3, "casos": list(self.cases.values())}
        self.proofs = {f"proof-{i}": {"componente": "backend", "clase": "tests.test_qa", "prueba": f"test_case_{i}",
                                      "archivo": "backend/tests/test_qa.py", "sha256": documented.source_fingerprint(self.source),
                                      "minimo_variantes": 1} for i in (1, 2)}
        self.entries = [{"id": i, "huella": f"case-{i}", "revision": "Oráculos revisados contra las aserciones",
                         "pasos": [{"paso": step, "pruebas": [f"proof-{i}"], "verificacion": "Comparar el estado y su relectura"}
                                   for step in (1, 2)]} for i in (1, 2)]
        self.records = [{"componente": "backend", "clase": "tests.test_qa", "prueba": f"test_case_{i}",
                         "estado": "passed", "duracion": 0.1, "ancestros": []} for i in (1, 2)]
        self.review = {"catalogo_sha256": documented.fingerprint(self.catalog), "minimo_porcentaje": 50,
                       "pruebas": self.proofs, "casos": self.entries}
        self.write()

    def write(self):
        (self.base / "catalogo.json").write_text(json.dumps(self.catalog), encoding="utf-8")
        (self.base / "automatizacion.json").write_text(json.dumps(self.review), encoding="utf-8")

    def test_porcentaje_cuenta_casos_unicos_y_redondea_el_minimo_hacia_arriba(self):
        report, summary = documented.build_report(self.root, self.root / "out", self.records, [])
        self.assertEqual((summary["ejecutados"], summary["total_documentados"], summary["minimo_requerido"]), (2, 3, 2))
        self.assertEqual(summary["porcentaje_ejecutado"], 66.67)
        self.assertEqual(report["tests"], 2)  # Solo revisados; el catálogo completo sigue en el resumen.

    def test_cien_variantes_de_una_prueba_no_acreditan_otro_caso(self):
        records = [{**self.records[0], "prueba": f"test_case_1[{i}]"} for i in range(100)]
        with self.assertRaisesRegex(ValueError, "1/3"):
            documented.build_report(self.root, self.root / "out", records, [])
        summary = json.loads((self.root / "out/cobertura-documentada.json").read_text())
        self.assertEqual(summary["ejecutados"], 1)

    def test_una_omision_no_es_aprobacion_ni_ejecucion_completa(self):
        records = deepcopy(self.records)
        records[1]["estado"] = "skipped"
        with self.assertRaisesRegex(ValueError, "Cobertura documentada insuficiente"):
            documented.build_report(self.root, self.root / "out", records, [])

    def test_fallo_real_se_conserva_y_no_se_convierte_en_pass(self):
        self.records[1]["estado"] = "failure"
        report, summary = documented.build_report(self.root, self.root / "out", self.records, [])
        self.assertEqual((summary["ejecutados"], summary["aprobados"], report["failures"]), (2, 1, 1))
        self.assertIsNotNone(ET.parse(report["file"]).find(".//testcase/failure"))

    def test_todas_las_variantes_del_oraculo_son_obligatorias(self):
        self.proofs["proof-1"]["minimo_variantes"] = 2
        self.write()
        with self.assertRaisesRegex(ValueError, "insuficiente"):
            documented.build_report(self.root, self.root / "out", self.records, [])

    def test_cambiar_el_catalogo_exige_revisar_la_correspondencia(self):
        self.catalog["casos"][0]["titulo"] = "Contrato nuevo"
        self.write()
        with self.assertRaisesRegex(ValueError, "catálogo actualizado"):
            documented.load_review(self.root)

    def test_cambiar_la_prueba_invalida_su_revision(self):
        self.source.write_text("# Prueba modificada\n")
        with self.assertRaisesRegex(ValueError, "cambió"):
            documented.load_review(self.root)

    def test_huellas_revisadas_aceptan_lf_y_crlf_del_mismo_codigo(self):
        expected = documented.source_fingerprint(self.source)
        self.source.write_bytes(self.source.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(documented.source_fingerprint(self.source), expected)
        documented.load_review(self.root)

    def test_informe_de_ci_debe_acreditar_las_aserciones_del_commit_probado(self):
        metadata = {"repository": "equipo/gym", "run_id": "1", "run_attempt": "1", "commit": "a" * 40,
                    "sources": {"backend/tests/test_qa.py": documented.source_fingerprint(self.source)}}
        reports = [{"component": "backend", "metadata": metadata}]
        _report, summary = documented.build_report(self.root, self.root / "out", self.records, reports)
        self.assertEqual(summary["ejecutados"], 2)
        metadata["sources"]["backend/tests/test_qa.py"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "aserciones revisadas"):
            documented.build_report(self.root, self.root / "out", self.records, reports)

    def test_no_admite_revisiones_parciales_de_los_pasos(self):
        self.entries[0]["pasos"].pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "resultados esperados"):
            documented.load_review(self.root)

    def test_rechaza_duplicados_y_no_permite_bajar_el_porcentaje(self):
        self.entries.append(deepcopy(self.entries[0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "duplicado"):
            documented.load_review(self.root)
        self.entries.pop()
        self.review["minimo_porcentaje"] = 1
        self.write()
        with self.assertRaisesRegex(ValueError, "mínimo del 50"):
            documented.load_review(self.root)

    def test_no_usa_las_pruebas_del_integrador_como_pruebas_del_producto(self):
        target = self.root / ".specify/tests/test_qa.py"
        target.parent.mkdir(parents=True)
        target.write_bytes(self.source.read_bytes())
        self.proofs["proof-1"]["archivo"] = ".specify/tests/test_qa.py"
        self.write()
        with self.assertRaisesRegex(ValueError, "revisión válida"):
            documented.load_review(self.root)

    def test_archivo_y_selector_junit_deben_corresponder(self):
        self.proofs["proof-1"]["clase"] = "tests.otra_prueba"
        self.write()
        with self.assertRaisesRegex(ValueError, "no corresponde"):
            documented.load_review(self.root)

    def test_no_mezcla_ejecuciones_ni_commits(self):
        data = {"repository": "equipo/gym", "run_id": "1", "run_attempt": "1", "commit": "a" * 40}
        reports = [{"metadata": data}, {"metadata": {**data, "commit": "b" * 40}}]
        with self.assertRaisesRegex(ValueError, "revisiones"):
            documented.origin_metadata(reports)
        self.assertEqual(documented.origin_metadata([{"metadata": data}])["component"], "casos-documentados")

    def test_junit_conserva_ids_rf_cus_tipo_y_enlace_manual_sin_modificar_runs(self):
        report, _summary = documented.build_report(self.root, self.root / "out", self.records, [])
        node = ET.parse(report["file"]).find(".//testcase")
        properties = {p.get("name"): p.get("value") for p in node.findall("properties/property")}
        self.assertEqual(properties["testkey"], "SILVE-TC-1")
        self.assertEqual(properties["rf"], "RF01")
        self.assertEqual(properties["cus"], "CUS01")
        self.assertEqual(properties["tipo_documentado"], "Funcional")
        self.assertTrue(properties["manual_case_url"].endswith("/tc/1/edit"))

    def test_estado_de_evidencia_desconocido_no_se_interpreta_como_pass(self):
        self.records[0]["estado"] = "unknown"
        with self.assertRaisesRegex(ValueError, "no interpretable"):
            documented.assess(self.cases, self.proofs, {c["id"]: c for c in self.entries}, self.records)


if __name__ == "__main__":
    unittest.main()
