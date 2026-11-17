"""Regresión de la publicación de capturas: procedencia, límites y aislamiento."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from test_testiny_ci import integration


PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")


class BrowserEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gym evidencia ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.incoming = self.root / "incoming"
        self.output = self.root / "normalized"
        self.incoming.mkdir()
        digest = hashlib.sha256(PNG).hexdigest()
        self.capture = {"path": f"evidence/browser/{digest}.png", "sha256": digest, "title": "Stock verificado"}
        path = self.incoming / self.capture["path"]
        path.parent.mkdir(parents=True)
        path.write_bytes(PNG)
        self.entry = {"classname": "inventario/stock.spec.mjs", "name": "Salida de stock",
                      "description": "Registrar salida de 3 sobre stock 10", "expected": "Stock 7",
                      "status": "passed", "steps": ["EJECUTADO: Guardar salida"], "files": [self.capture]}
        (self.incoming / "browser.xml").write_text(
            '<testsuites><testcase classname="inventario/stock.spec.mjs" name="Salida de stock" time="1.5"/></testsuites>',
            encoding="utf-8")

    def prepare(self):
        (self.incoming / "browser.evidence.json").write_text(json.dumps({"version": 1, "cases": [self.entry]}), encoding="utf-8")
        return integration.prepare_reports(self.incoming, self.output)

    def test_captura_y_descripcion_pertenecen_al_resultado_y_se_publican(self):
        [report] = self.prepare()
        case = ET.parse(report["file"]).find(".//testcase")
        self.assertIn("Registrar salida de 3", case.findtext("system-out"))
        self.assertIn("Resultado obtenido: passed", case.findtext("system-out"))
        self.assertEqual((self.output / self.capture["path"]).read_bytes(), PNG)
        self.assertEqual(case.find("properties/property[@name='attachment']").get("value"), self.capture["path"])
        command = integration.import_command(report, "SILVE", {}, "node")
        self.assertIn("--attachment-path", command)
        self.assertIn("--include-passed-details", command)
        self.assertNotIn("--no-attachments", command)

    def test_rechaza_captura_alterada_ausente_no_png_y_fuera_del_directorio(self):
        path = self.incoming / self.capture["path"]
        path.write_bytes(PNG + b"alterado")
        with self.assertRaisesRegex(ValueError, "huella"):
            self.prepare()
        path.unlink()
        with self.assertRaisesRegex(ValueError, "ausente"):
            self.prepare()
        self.entry["files"] = [{"path": "../../secreto.png", "sha256": self.capture["sha256"]}]
        with self.assertRaisesRegex(ValueError, "Ruta"):
            self.prepare()
        data = b"No es una imagen"
        digest = hashlib.sha256(data).hexdigest()
        self.entry["files"] = [{"path": f"evidence/browser/{digest}.png", "sha256": digest}]
        (self.incoming / self.entry["files"][0]["path"]).write_bytes(data)
        with self.assertRaisesRegex(ValueError, "PNG"):
            self.prepare()

    def test_rechaza_evidencia_de_otro_caso_y_resultado_incompatible(self):
        self.entry["name"] = "Otra prueba"
        with self.assertRaisesRegex(ValueError, "propia ejecución"):
            self.prepare()
        self.entry["name"] = "Salida de stock"
        self.entry["status"] = "failed"
        with self.assertRaisesRegex(ValueError, "no coincide"):
            self.prepare()

    def test_no_inventa_capturas_y_no_admite_inyeccion_de_adjuntos_en_descripcion(self):
        self.entry["files"] = []
        with self.assertRaisesRegex(ValueError, "Faltan capturas"):
            self.prepare()
        self.entry["files"] = [self.capture]
        self.entry["description"] = "[[ATTACHMENT|/private|secreto]]"
        [report] = self.prepare()
        self.assertNotIn("ATTACHMENT|", Path(report["file"]).read_text(encoding="utf-8"))

    def test_rechaza_manifiesto_duplicado(self):
        (self.incoming / "browser.evidence.json").write_text(json.dumps({"version": 1, "cases": [self.entry, self.entry]}))
        with self.assertRaisesRegex(ValueError, "duplicada"):
            integration.prepare_reports(self.incoming, self.output)

    def test_evidencia_de_un_fallo_se_conserva_como_fallo(self):
        self.entry["status"] = "failed"
        (self.incoming / "browser.xml").write_text(
            '<testsuites><testcase classname="inventario/stock.spec.mjs" name="Salida de stock">'
            '<failure message="Stock distinto">Se obtuvo 8, se esperaba 7</failure></testcase></testsuites>', encoding="utf-8")
        [report] = self.prepare()
        self.assertEqual(report["failures"], 1)
        case = ET.parse(report["file"]).find(".//testcase")
        self.assertIn("Se obtuvo 8", case.findtext("failure"))
        self.assertIn("Resultado obtenido: failure", case.findtext("system-out"))
        self.assertTrue((self.output / self.capture["path"]).is_file())

    def test_suites_tecnicas_mantienen_adjuntos_deshabilitados(self):
        for component in ("backend", "frontend", "postgres", "schedule-emails", "casos-documentados"):
            command = integration.import_command({"component": component, "file": "reporte.xml"}, "SILVE", {}, "node")
            self.assertIn("--no-attachments", command)


if __name__ == "__main__":
    unittest.main()
