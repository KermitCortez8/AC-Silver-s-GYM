"""Verifica scripts Spec Kit y el hook único en copias sin red ni credenciales."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gym_validation", SOURCE / ".codex/hooks/validate.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spec kit con espacios ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / ".specify"
        shutil.copytree(SOURCE, self.base, ignore=shutil.ignore_patterns(
            ".venv", "__pycache__", "feature.json", "AGENTS.local.md"))
        for name in ["README.md", "AGENTS.md"]:
            shutil.copy2(SOURCE.parent / name, self.root / name)
        # Copiar solo los destinos locales que los documentos enlazan.
        for document in validation.documents(SOURCE.parent):
            for target in validation.local_targets(document, document.read_text()):
                if not target.is_relative_to(SOURCE.parent) or target.is_relative_to(SOURCE):
                    continue
                destination = self.root / target.relative_to(SOURCE.parent)
                if target.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif target.is_file():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, destination)
        native = self.root / ".agents/skills"
        native.mkdir(parents=True, exist_ok=True)
        for folder in (self.base / ".codex/skills").iterdir():
            (native / folder.name).symlink_to("../../.specify/.codex/skills/" + folder.name,
                                             target_is_directory=True)

    def command(self, *arguments, cwd=None, check=True, **environment):
        env = os.environ.copy()
        for key in ["SPECIFY_FEATURE", "SPECIFY_FEATURE_DIRECTORY", "SPECIFY_INIT_DIR", "SPECIFY_FEATURE_NO_PERSIST"]:
            env.pop(key, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.update(environment)
        return subprocess.run(arguments, cwd=cwd or self.root, env=env, text=True,
                              capture_output=True, check=check)

    def script(self, name, *arguments, **environment):
        return self.command("bash", str(self.base / "scripts/bash" / name),
                            *arguments, **environment)

    def create(self, *arguments, **environment):
        result = self.script("create-new-feature.sh", "--json", "--short-name", "prueba",
                             *arguments, "Cambio de prueba aislada", **environment)
        return json.loads(result.stdout)

    def fill_context_and_spec(self, directory):
        sections = []
        for index, title in enumerate(validation.COMPONENTS, 1):
            body = "Contenido sintético verificable."
            if index == 3:
                body = ("1. **CA-01.** Dado un fixture, se puede verificar su estructura.\n\n"
                        "| Criterio | Evidencia |\n| --- | --- |\n"
                        "| CA-01 | [Base](../../../AGENTS.md). |")
            sections.append(f"## {index}. {title}\n\n{body}\n")
        (directory / "spec.md").write_text("# Fixture\n\n" + "\n".join(sections))
        names = ["AGENTS.md", ".specify/memory/constitution.md",
                 ".specify/specs/000-base-implementada/spec.md", ".specify/base/modulos/README.md",
                 ".specify/docs/arquitectura.md", ".specify/docs/diseno.md",
                 ".specify/.codex/rules/seguridad.md", ".specify/docs/DoD.md"]
        links = [f"- [Base](<{os.path.relpath(self.root / name, directory)}>)." for name in names]
        content = "# Contexto\n\n## Base obligatoria\n\n" + "\n".join(links)
        content += ("\n\n## Módulos afectados\n\n"
                    "- **SDD**: [Flujo](../../guias/spec-driven.md).\n\n"
                    "## Código y pruebas existentes\n\n"
                    "[Pruebas aisladas](../../tests/test_integration.py).\n\n"
                    "## Restricciones que se deben contrastar\n\nSolo estructura, sin producto.\n\n"
                    "## Evaluación específica del cambio\n\nSe verifican los scripts reales y sus fallos.\n")
        (directory / "context.md").write_text(content)

    def complete(self):
        directory = Path(self.create()["SPEC_FILE"]).parent
        self.fill_context_and_spec(directory)
        self.script("setup-plan.sh", "--json")
        (directory / "plan.md").write_text("# Plan\n\n[Contexto](context.md).\n")
        (directory / "tasks.md").write_text("# Tareas\n\n- [x] T001 CA-01 Comprobar estructura.\n")
        (directory / "validation.md").write_text("# Evidencia\n\nFixture aislado comprobado.\n")
        return directory

    def hook(self, *arguments, **options):
        return self.command(sys.executable, str(self.base / ".codex/hooks/validate.py"),
                            *arguments, **options)

    def test_native_creation_from_subdirectory_prepares_context_without_branch_change(self):
        self.command("git", "init", "--quiet")
        before = self.command("git", "branch", "--show-current").stdout
        directory = Path(self.create(cwd=self.root / "frontend")["SPEC_FILE"]).parent
        self.assertEqual(directory.parent, self.base / "specs")
        self.assertEqual((directory / "context.md").read_text(),
                         (self.base / "templates/overrides/context-template.md").read_text())
        self.assertEqual(before, self.command("git", "branch", "--show-current").stdout)
        self.assertFalse(os.path.lexists(self.root / "specs"))

    def test_reusing_feature_preserves_existing_context(self):
        data = self.create()
        directory = Path(data["SPEC_FILE"]).parent
        (directory / "context.md").write_text("Análisis propio que debe conservarse.\n")
        self.create("--number", data["FEATURE_NUM"], "--allow-existing-branch")
        self.assertEqual((directory / "context.md").read_text(), "Análisis propio que debe conservarse.\n")

    def test_dry_run_does_not_write_and_number_conflicts_preserve_base(self):
        before = set(self.base.rglob("*"))
        self.assertTrue(self.create("--dry-run")["DRY_RUN"])
        self.assertEqual(before, set(self.base.rglob("*")))
        baseline = self.base / "specs/000-base-implementada/spec.md"
        original = baseline.read_bytes()
        first = self.create("--number", "0")
        second = self.create()
        self.assertGreater(int(first["FEATURE_NUM"]), 0)
        self.assertEqual(int(second["FEATURE_NUM"]), int(first["FEATURE_NUM"]) + 1)
        self.assertEqual(baseline.read_bytes(), original)

    def test_plan_hook_blocks_incomplete_context_before_creating_plan(self):
        directory = Path(self.create()["SPEC_FILE"]).parent
        result = self.script("setup-plan.sh", "--json", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evaluación específica", result.stderr)
        self.assertFalse((directory / "plan.md").exists())
        self.fill_context_and_spec(directory)
        result = json.loads(self.script("setup-plan.sh", "--json").stdout)
        self.assertEqual(Path(result["IMPL_PLAN"]), directory / "plan.md")

    def test_tasks_and_prerequisites_use_official_templates_and_same_hook(self):
        directory = self.complete()
        tasks = json.loads(self.script("setup-tasks.sh", "--json").stdout)
        self.assertIn("T001", tasks["TASKS_TEMPLATE_CONTENT"])
        result = self.script("check-prerequisites.sh", "--json", "--require-tasks", "--include-tasks")
        self.assertIn("tasks.md", json.loads(result.stdout)["AVAILABLE_DOCS"])
        self.assertIn("Precondiciones de implement correctas", result.stderr)
        (directory / "tasks.md").write_text("- [ ] T001 Sin criterio\n")
        result = self.script("check-prerequisites.sh", "--json", "--require-tasks", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CA-01", result.stderr)

    def test_stage_validation_requires_context_module_and_closed_tasks(self):
        directory = self.complete()
        for stage in ["plan", "implement", "close"]:
            self.assertEqual(self.hook("--feature", directory.name, "--stage", stage).returncode, 0)
        path = directory / "context.md"
        original = path.read_text()
        path.write_text(original.replace("**SDD**", "**MOD-99**"))
        self.assertIn("módulo desconocido", self.hook("--feature", directory.name, check=False).stderr)
        path.write_text(original)
        (directory / "tasks.md").write_text("- [ ] T001 CA-01 Sin terminar\n")
        self.assertIn("tareas abiertas", self.hook("--feature", directory.name, "--stage", "close", check=False).stderr)

    def test_legacy_pointer_migration_and_read_only_resolution(self):
        directory = self.complete()
        pointer = self.base / "feature.json"
        pointer.write_text(json.dumps({"feature_directory": "specs/" + directory.name}))
        original = pointer.read_bytes()
        result = self.script("check-prerequisites.sh", "--paths-only", "--json", cwd=self.root / "backend")
        self.assertEqual(Path(json.loads(result.stdout)["FEATURE_DIR"]), directory)
        self.assertEqual(pointer.read_bytes(), original)
        self.script("setup-plan.sh", "--json")
        self.assertEqual(json.loads(pointer.read_text())["feature_directory"], ".specify/specs/" + directory.name)
        self.assertFalse(os.path.lexists(self.root / "specs"))

    def test_external_feature_paths_are_rejected_before_state_changes(self):
        self.complete()
        pointer = self.base / "feature.json"
        original = pointer.read_bytes()
        result = self.script("setup-plan.sh", "--json", check=False,
                             SPECIFY_FEATURE_DIRECTORY=str(self.root / "outside"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(pointer.read_bytes(), original)
        with tempfile.TemporaryDirectory() as outside:
            (self.base / "specs/999-escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                validation.feature_directory(self.root, "999-escape")

    def test_settings_reject_malformed_missing_and_external_resources(self):
        path = self.base / ".codex/settings.json"
        original = path.read_text()
        for kind in ["json", "regla", "etapa"]:
            config = json.loads(original)
            if kind == "regla":
                config["rules"][0]["document"] = "rules/ausente.md"
            if kind == "etapa":
                config["hooks"]["plan"]["required"] = ["spec.md"]
            path.write_text("{" if kind == "json" else json.dumps(config))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validation.load_settings(self.root)
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "externo.md"
            external.write_text("No debe cargarse.\n")
            (self.base / ".codex/agents/externo.md").symlink_to(external)
            config = json.loads(original)
            config["reviews"]["close"] = "agents/externo.md"
            path.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                validation.load_settings(self.root)

    def test_structure_checks_skills_docs_and_no_root_aliases(self):
        self.assertEqual(validation.check_structure(self.root), [])
        (self.base / "docs/extra.md").write_text("No pertenece a docs.\n")
        self.assertTrue(validation.check_structure(self.root))
        (self.base / "docs/extra.md").unlink()
        (self.root / "docs").symlink_to(".specify/docs", target_is_directory=True)
        self.assertTrue(validation.check_structure(self.root))
        (self.root / "docs").unlink()
        (self.root / ".agents/skills/gym-spec-driven").unlink()
        self.assertTrue(validation.check_structure(self.root))

    def test_document_index_is_the_only_module_catalog_and_preamble_is_shared(self):
        contracts = validation.module_contracts(self.root)
        self.assertEqual(len(contracts), 12)
        self.assertEqual(contracts["MOD-09"].name, "09-tienda-pedidos.md")
        for path in (self.base / ".codex/skills").glob("speckit-*/SKILL.md"):
            self.assertIn("[preámbulo común](../../preamble.md)", path.read_text())
            self.assertNotIn("## Un solo flujo", path.read_text())
        self.assertEqual(validation.load_settings(self.root)["reviews"]["analyze"], "agents/revisor.md")
        for old in ["sdd.py", "base/modules.json", "scripts/validate_docs.py", ".codex/hooks/check-stage.py", "workflows"]:
            self.assertFalse((self.base / old).exists())

    def test_upstream_hashes_and_registered_adaptations_match(self):
        manifest = json.loads((self.base / "integrations/speckit.manifest.json").read_text())
        local = json.loads((self.base / "integrations/project-overrides.json").read_text())
        for name, expected in manifest["files"].items():
            if name in local["files"]:
                self.assertEqual(local["files"][name]["upstream_sha256"], expected)
                expected = local["files"][name]["project_sha256"]
            self.assertEqual(hashlib.sha256((self.root / name).read_bytes()).hexdigest(), expected, name)

    def test_hooks_do_not_generate_caches_or_require_cli_installation(self):
        directory = self.complete()
        self.hook("--feature", directory.name, "--stage", "close")
        self.assertFalse((self.base / ".venv").exists())
        self.assertEqual(list(self.base.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
