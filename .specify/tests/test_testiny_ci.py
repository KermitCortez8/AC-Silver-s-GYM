"""Comprueba informes, aislamiento y publicación simulada; no accede a Testiny."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/testiny/publish.py"
spec = importlib.util.spec_from_file_location("gym_testiny_ci", SCRIPT)
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class TestinyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gym testiny ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.incoming = self.root / "incoming"
        self.output = self.root / "normalized"
        self.modules = integration.module_registry()
        self.event = {
            "repository": {"full_name": "equipo/gym"},
            "workflow_run": {
                "id": 123, "run_attempt": 2, "name": "Validar PR", "conclusion": "failure",
                "head_repository": {"full_name": "equipo/gym"}, "head_sha": "a" * 40,
                "head_branch": "feature/reporte", "html_url": "https://github.com/equipo/gym/actions/runs/123",
            },
        }

    def report(self, body, component="backend", metadata=True):
        path = self.incoming / f"{component}.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        if metadata:
            path.with_suffix(".metadata.json").write_text(json.dumps({
                "component": component, "repository": "equipo/gym", "run_id": "123",
                "run_attempt": "2", "commit": "b" * 40,
            }), encoding="utf-8")
        return path

    def basic_report(self):
        return self.report('<testsuites><testsuite><testcase name="caso" '
                           'classname="tests.clientes.unitarias.test_lookup" time="0.1"/>'
                           '</testsuite></testsuites>')

    def invoke(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return integration.main(["--incoming", str(self.incoming), "--output", str(self.output), *args])

    def test_usa_el_indice_central_de_los_once_modulos(self):
        self.assertEqual(len(self.modules), 11)
        self.assertEqual(self.modules["clientes"], "MOD-02 - Clientes")
        self.assertEqual(self.modules["notificaciones"], "MOD-11 - Notificaciones")

    def test_fuentes_distintas_respetan_el_formato_de_la_api_testiny(self):
        sources = []
        for component in integration.SOURCES:
            with self.subTest(component=component):
                command = integration.import_command({"component": component, "file": "informe.xml"}, "SILVE", {}, "node")
                source = command[command.index("--source") + 1]
                # Regla de la API incluida en la CLI 1.43.1; los espacios causaron
                # API_INVALID_INPUT_DATA en la primera ejecución de GitHub.
                self.assertRegex(source, r"(?i)^[$a-z][$a-z0-9_.-]*$")
                sources.append(source)
        self.assertEqual(len(sources), len(set(sources)))

    def test_fuente_invalida_detiene_toda_publicacion_antes_de_enviar(self):
        self.basic_report()
        self.report('<testsuite><testcase name="tests/clientes/unitarias/test.mjs::caso"/></testsuite>', "frontend")
        event = self.root / "event.json"
        event.write_text(json.dumps(self.event), encoding="utf-8")
        cli = self.root / "cli.js"
        cli.touch()
        with mock.patch.dict(os.environ, {"TESTINY_API_KEY": "clave-sintetica"}), \
                mock.patch.dict(integration.SOURCES, {"frontend": "GYM - Frontend"}), \
                mock.patch.object(integration, "CLI_ENTRY", cli), \
                mock.patch.object(integration.shutil, "which", return_value="node"), \
                mock.patch.object(integration.subprocess, "run") as execute:
            self.assertEqual(self.invoke("--publish", "--event", str(event)), 1)
            execute.assert_not_called()

    def test_preserva_fallos_errores_omisiones_y_claves_estables(self):
        source = self.report('''<testsuites><testsuite name="pytest">
          <testcase name="correcto" classname="tests.clientes.unitarias.test_lookup" time="0.3"/>
          <testcase name="fallo" classname="tests.clientes.integracion.test_client" time="1"><failure message="falló">detalle</failure></testcase>
          <testcase name="error" classname="tests.transversales.test_server"><error>error</error></testcase>
          <testcase name="omitido" classname="tests.clientes.postgres.test_db"><skipped message="sin PostgreSQL"/></testcase>
        </testsuite></testsuites>''')
        destination = self.output / "backend.xml"
        counts = integration.normalize_report(source, destination, "backend", self.modules)
        self.assertEqual(counts, {"tests": 4, "failures": 1, "errors": 1, "skipped": 1})
        document = ET.parse(destination)
        cases = document.findall(".//testcase")
        self.assertIn("MOD-02 - Clientes.Unitarias", cases[0].get("classname"))
        first_key = cases[0].find("properties/property").get("value")
        self.assertTrue(first_key.startswith("gym-backend-"))
        integration.normalize_report(source, destination, "backend", self.modules)
        self.assertEqual(first_key, ET.parse(destination).find(".//testcase/properties/property").get("value"))
        self.assertEqual(document.find(".//testcase[@name='fallo']/failure").text, "detalle")

    def test_no_copia_adjuntos_rutas_ni_propiedades_del_artefacto(self):
        source = self.report('''<testsuites><testcase name="caso" classname="tests.tienda_pedidos.integracion.test_images">
          <properties><property name="attachment" value="../../private"/></properties>
          <failure message="[[ATTACHMENT|/private|nombre]]">[[ATTACHMENT|file:///private|nombre]]</failure>
          <system-out>[[ATTACHMENT|./secret|nombre]]</system-out>
        </testcase></testsuites>''')
        destination = self.output / "backend.xml"
        integration.normalize_report(source, destination, "backend", self.modules)
        text = destination.read_text(encoding="utf-8")
        for forbidden in ["ATTACHMENT|", "file://", "../../private", "./secret", 'name="attachment"']:
            self.assertNotIn(forbidden, text)
        self.assertIn("Resultado obtenido: failure", text)

    def test_carpetas_y_recuentos_derivan_de_la_ruta_del_archivo(self):
        self.report('''<testsuite>
          <testcase name="tests/transversales/interfaz/comun.test.js::consulta.clientes.unitarias"/>
          <testcase name="tests/inventario/unitarias/stock.test.js::consulta tienda_pedidos"/>
        </testsuite>''', "frontend")
        reports = integration.prepare_reports(self.incoming, self.output)
        cases = ET.parse(reports[0]["file"]).findall(".//testcase")
        self.assertEqual([case.get("classname") for case in cases], [
            "Transversales.Funcionales de interfaz.comun_test_js",
            "MOD-08 - Inventario.Unitarias.stock_test_js",
        ])
        summary = json.loads((self.output / "resumen.json").read_text(encoding="utf-8"))
        self.assertEqual(summary[0]["modulos"], {"MOD-08 - Inventario": 1, "Transversales": 1})

    def test_rechaza_dtd_entidades_utf16_estados_ambiguos_y_reportes_vacios(self):
        variants = [
            '<!DOCTYPE testsuites [<!ENTITY x "contenido">]><testsuites/>',
            '<testsuites/>',
            '<testsuites><testcase name="caso" status="failed"/></testsuites>',
            '<testsuites><testcase name="caso" time="NaN"/></testsuites>',
            '<testsuites><testcase name="caso" time="-1"/></testsuites>',
        ]
        for text in variants:
            with self.subTest(text=text):
                source = self.report(text)
                with self.assertRaises(ValueError):
                    integration.normalize_report(source, self.output / "bad.xml", "backend", self.modules)
        source.write_bytes(variants[0].encode("utf-16"))
        with self.assertRaises(ValueError):
            integration.normalize_report(source, self.output / "bad.xml", "backend", self.modules)

    def test_rechaza_identidades_duplicadas_en_lugar_de_fusionar_pruebas(self):
        source = self.report('<testsuites><testcase name="igual"/><testcase name="igual"/></testsuites>')
        with self.assertRaisesRegex(ValueError, "duplicada"):
            integration.normalize_report(source, self.output / "bad.xml", "backend", self.modules)

    def test_ignora_archivos_ajenos_y_no_publica_ejecuciones_vacias(self):
        (self.incoming / "ajeno").mkdir(parents=True)
        (self.incoming / "ajeno/other.xml").write_text('<testsuites><testcase name="otro"/></testsuites>')
        with self.assertRaisesRegex(ValueError, "No hay informes"):
            integration.prepare_reports(self.incoming, self.output)

    def test_no_lee_informes_fuera_del_directorio_de_artefactos(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "backend.xml").write_text('<testsuites><testcase name="otro"/></testsuites>')
        self.incoming.mkdir()
        try:
            (self.incoming / "backend.xml").symlink_to(outside / "backend.xml")
        except OSError as error:
            self.skipTest(f"El sistema no permite enlaces: {error}")
        with self.assertRaisesRegex(ValueError, "fuera"):
            integration.prepare_reports(self.incoming, self.output)

    def test_postgres_y_deno_se_ordenan_por_su_modulo_y_tipo_real(self):
        self.report('<testsuite><testcase name="transaccion" '
                    'classname="tests.asistencias.postgres.test_atomic"/></testsuite>', "postgres")
        self.report('<testsuite><testcase name="recordatorio"/></testsuite>', "schedule-emails")
        reports = integration.prepare_reports(self.incoming, self.output)
        self.assertEqual(len(reports), 2)
        expected = {
            "postgres": "MOD-06 - Asistencias.Integración PostgreSQL",
            "schedule-emails": "MOD-11 - Notificaciones.Integración Deno",
        }
        for report in reports:
            case = ET.parse(report["file"]).find(".//testcase")
            self.assertIn(expected[report["component"]], case.get("classname"))

    def test_commit_probado_y_workflow_de_origen_no_se_confunden_con_el_publicador(self):
        self.basic_report()
        report = integration.prepare_reports(self.incoming, self.output)[0]
        fields = integration.report_fields(report, integration.run_fields(self.event))
        self.assertEqual(fields["vc_commit"], "b" * 40)
        self.assertEqual(fields["vc_source_commit"], "a" * 40)
        self.assertEqual(fields["ci_run_id"], "123")
        self.assertEqual(fields["ci_retry"], "2")
        self.assertEqual(fields["ci_workflow_name"], "Validar PR")
        report["metadata"]["run_id"] = "otro"
        with self.assertRaises(ValueError):
            integration.report_fields(report, integration.run_fields(self.event))

    def test_rechaza_forks_workflows_ajenos_y_ejecuciones_canceladas(self):
        for key, value in [("name", "ajeno"), ("conclusion", "cancelled"),
                           ("head_repository", {"full_name": "externo/fork"})]:
            event = json.loads(json.dumps(self.event))
            event["workflow_run"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                integration.run_fields(event)

    def test_publica_merge_del_pipeline_con_su_revision_e_intento(self):
        event = {"repository": {"full_name": "equipo/gym"}, "action": "closed",
                 "pull_request": {"merged": True, "merge_commit_sha": "b" * 40,
                                  "base": {"ref": "main"}}}
        environment = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_WORKFLOW": "CI/CD Pipeline GYM",
                       "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2",
                       "GITHUB_SERVER_URL": "https://github.com"}
        with mock.patch.dict(os.environ, environment, clear=True):
            fields = integration.run_fields(event)
            self.assertEqual(fields["vc_commit"], "b" * 40)
            self.assertEqual(fields["ci_run_id"], "123")
            self.assertEqual(fields["ci_retry"], "2")
            self.assertEqual(fields["ci_workflow_name"], "CI/CD Pipeline GYM")
            for change in ({"merged": False}, {"base": {"ref": "develop"}}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    integration.run_fields({**event, "pull_request": {**event["pull_request"], **change}})
            with mock.patch.dict(os.environ, {"GITHUB_WORKFLOW": "Validar PR"}):
                with self.assertRaises(ValueError):
                    integration.run_fields(event)

    def test_workflow_publica_solo_el_merge_a_main_y_usa_sus_artefactos(self):
        workflow = (ROOT / ".github/workflows/ci-cd.yml").read_text(encoding="utf-8")
        trigger = workflow.split("permissions:", 1)[0]
        self.assertNotIn("workflow_run:", trigger)
        self.assertIn("branches: [main]", trigger)
        self.assertIn("types: [closed]", trigger)
        publication = workflow.split("\n  testiny:", 1)[1]
        self.assertIn("github.event.pull_request.merged == true", publication)
        self.assertIn("github.event.pull_request.base.ref == 'main'", publication)
        self.assertIn("run-id: ${{ github.run_id }}", publication)
        self.assertIn("pattern: gym-junit-*-${{ github.run_attempt }}", publication)
        self.assertNotIn("github.event.workflow_run", publication)

    def test_preparacion_local_no_contacta_testiny_aunque_exista_una_clave(self):
        self.basic_report()
        with mock.patch.dict(os.environ, {"TESTINY_API_KEY": "clave-sintetica"}), \
                mock.patch.object(integration.subprocess, "run") as execute:
            self.assertEqual(self.invoke(), 0)
            execute.assert_not_called()

    def test_publicacion_exige_clave_y_no_expone_su_valor_en_argumentos(self):
        self.basic_report()
        event_file = self.root / "event.json"
        event_file.write_text(json.dumps(self.event), encoding="utf-8")
        cli = self.root / "cli.js"
        cli.write_text("// doble local; no se ejecuta", encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(integration.subprocess, "run") as execute:
            self.assertEqual(self.invoke("--publish", "--event", str(event_file)), 1)
            execute.assert_not_called()
        with mock.patch.dict(os.environ, {"TESTINY_API_KEY": "clave-sintetica"}), \
                mock.patch.object(integration, "CLI_ENTRY", cli), \
                mock.patch.object(integration.shutil, "which", return_value="node"), \
                mock.patch.object(integration.subprocess, "run") as execute:
            self.assertEqual(self.invoke("--publish", "--event", str(event_file)), 0)
            command = execute.call_args.args[0]
            self.assertNotIn("clave-sintetica", " ".join(command))
            self.assertIn("--no-attachments", command)
            self.assertIn("automation", command)
            self.assertEqual(command[command.index("--junit-classname-as-folder") + 1], "nested")
            self.assertNotIn("testrun", command)
            self.assertNotIn("shell", execute.call_args.kwargs)

    def test_error_del_importador_no_se_oculta_ni_se_reintenta(self):
        self.basic_report()
        event = self.root / "event.json"
        event.write_text(json.dumps(self.event))
        cli = self.root / "cli.js"
        cli.touch()
        with mock.patch.dict(os.environ, {"TESTINY_API_KEY": "clave-sintetica"}), \
                mock.patch.object(integration, "CLI_ENTRY", cli), \
                mock.patch.object(integration.shutil, "which", return_value="node"), \
                mock.patch.object(integration.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "node")) as execute:
            self.assertEqual(self.invoke("--publish", "--event", str(event)), 1)
            self.assertEqual(execute.call_count, 1)

    def test_reporter_real_de_node_conserva_archivo_fallo_omision_y_suites_anidadas(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node no está instalado")
        test_file = self.root / "tests/identidad_acceso/unitarias/reporter.test.mjs"
        test_file.parent.mkdir(parents=True)
        test_file.write_text('''import { test, describe } from 'node:test';
          import assert from 'node:assert/strict';
          test('correcto á & <', () => assert.equal(1,1));
          test('fallo', () => assert.fail('fallo intencional'));
          test('omitido', {skip:true}, () => {});
          describe('grupo A', () => { test('repetido', () => {}); });
          describe('grupo B', () => { test('repetido', () => {}); });
        ''', encoding="utf-8")
        reporter = ROOT / ".github/scripts/testiny/node-junit.mjs"
        result = subprocess.run([node, "--test", f"--test-reporter={reporter.as_uri()}", str(test_file)],
                                cwd=self.root, capture_output=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 1, result.stderr)
        source = self.report(result.stdout, "frontend")
        counts = integration.normalize_report(source, self.output / "frontend.xml", "frontend", self.modules)
        self.assertEqual(counts, {"tests": 5, "failures": 1, "errors": 0, "skipped": 1})
        cases = ET.parse(self.output / "frontend.xml").findall(".//testcase")
        self.assertTrue(all("MOD-01 - Identidad y acceso.Unitarias" in case.get("classname") for case in cases))
        keys = [case.find("properties/property").get("value") for case in cases]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(any("grupo A" in case.get("name") for case in cases))


if __name__ == "__main__":
    unittest.main()
