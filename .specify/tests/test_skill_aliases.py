"""Regresión del checkout Git sin symlinks de Windows; no necesita privilegios."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / ".codex/hooks/validate.py"
spec = importlib.util.spec_from_file_location("gym_skill_validation", SCRIPT)
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


class SkillAliasTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gym skills ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.alias = self.root / ".agents/skills/gym-spec-driven"
        self.expected = self.root / ".specify/.codex/skills/gym-spec-driven"
        self.alias.parent.mkdir(parents=True)
        self.expected.mkdir(parents=True)
        (self.expected / "SKILL.md").write_text("# Skill de prueba\n", encoding="utf-8")
        self.pointer = "../../.specify/.codex/skills/gym-spec-driven"

    def test_windows_acepta_el_destino_exacto_con_saltos_git(self):
        for ending in ("", "\n", "\r\n"):
            with self.subTest(ending=repr(ending)), mock.patch.object(validation.sys, "platform", "win32"):
                self.alias.write_bytes((self.pointer + ending).encode("utf-8"))
                self.assertTrue(validation.valid_skill_alias(self.alias, self.expected))

    def test_linux_rechaza_archivos_de_texto_en_lugar_de_enlaces(self):
        self.alias.write_text(self.pointer, encoding="utf-8")
        with mock.patch.object(validation.sys, "platform", "linux"):
            self.assertFalse(validation.valid_skill_alias(self.alias, self.expected))

    def test_windows_rechaza_destinos_alterados_y_archivos_invalidos(self):
        for content in ("../../externo", self.pointer + "/../otra", self.pointer + " ",
                        self.pointer + "\ninstrucciones", "x" * 513):
            with self.subTest(content=content), mock.patch.object(validation.sys, "platform", "win32"):
                self.alias.write_text(content, encoding="utf-8")
                self.assertFalse(validation.valid_skill_alias(self.alias, self.expected))
        self.alias.write_bytes(b"\xff")
        with mock.patch.object(validation.sys, "platform", "win32"):
            self.assertFalse(validation.valid_skill_alias(self.alias, self.expected))

    def test_windows_exige_skill_real_y_rechaza_directorios_copiados(self):
        self.alias.write_text(self.pointer, encoding="utf-8")
        (self.expected / "SKILL.md").unlink()
        with mock.patch.object(validation.sys, "platform", "win32"):
            self.assertFalse(validation.valid_skill_alias(self.alias, self.expected))
        self.alias.unlink()
        self.alias.mkdir()
        (self.alias / "SKILL.md").write_text("Copia", encoding="utf-8")
        with mock.patch.object(validation.sys, "platform", "win32"):
            self.assertFalse(validation.valid_skill_alias(self.alias, self.expected))

    def test_symlink_exige_destino_correcto_y_skill_accesible(self):
        # Simula solo las operaciones del enlace para cubrir esta rama sin
        # exigir privilegios de Windows; los destinos reales se validan arriba.
        alias = mock.Mock()
        alias.is_symlink.return_value = True
        alias.resolve.return_value = self.expected.resolve()
        alias.__truediv__ = mock.Mock(return_value=self.expected / "SKILL.md")
        self.assertTrue(validation.valid_skill_alias(alias, self.expected))
        alias.resolve.return_value = self.root / "externo"
        self.assertFalse(validation.valid_skill_alias(alias, self.expected))


if __name__ == "__main__":
    unittest.main()
