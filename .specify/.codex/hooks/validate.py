#!/usr/bin/env python3
"""Valida la base SDD sin dependencias, red ni credenciales de la aplicación.

Comprueba destinos locales, siete componentes y evidencia por criterio.
No comprueba anchors, URLs externas, comportamiento ni ejecución de pruebas.
"""
from __future__ import annotations

from pathlib import Path
import re
import argparse
import os
import sys
import json
from urllib.parse import unquote, urlsplit


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
COMPONENTS = (
    "Sprint Goal", "User Story", "Acceptance Criteria", "Technical Constraints",
    "Guardrails", "Edge Cases", "Definition of Done",
)
LINK = re.compile(r"!?\[[^\]\n]*\]\((<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)")
CRITERION = re.compile(r"^\d+\. \*\*(CA-\d{2,})\.\*\*", re.MULTILINE)
ROW = re.compile(r"^\|\s*(CA-\d{2,})\s*\|([^\n]+)\|\s*$", re.MULTILINE)


def resource(root: Path, name: str, folder: str = "") -> Path:
    if not isinstance(name, str) or not name:
        raise ValueError("Referencia inválida en .codex/settings.json")
    path = (root / ".specify/.codex" / name).resolve()
    boundary = root / (".specify/.codex/" + folder if folder else ".specify")
    if not path.is_relative_to(boundary) or not path.is_file():
        raise ValueError(f"Referencia inexistente o fuera de {boundary.relative_to(root)}: {name}")
    return path


def load_settings(root: Path) -> dict:
    config = json.loads((root / ".specify/.codex/settings.json").read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema_version") != 1 or config.get("consumer") != "hooks/validate.py":
        raise ValueError("Formato inválido de .codex/settings.json")
    resource(root, config.get("instructions"))
    rules = config.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("settings.json debe declarar reglas por rutas")
    identifiers = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or rule["id"] in identifiers:
            raise ValueError("Regla inválida o repetida")
        identifiers.add(rule["id"])
        resource(root, rule.get("document"), "rules")
        patterns = rule.get("paths")
        if not isinstance(patterns, list) or not patterns or not all(isinstance(p, str) and p for p in patterns):
            raise ValueError("Cada regla necesita patrones de rutas")
        if "always" in rule and not isinstance(rule["always"], bool):
            raise ValueError("always debe ser booleano")
    required = {"plan": {"spec.md", "context.md"},
                "implement": {"spec.md", "context.md", "plan.md", "tasks.md"},
                "close": {"spec.md", "context.md", "plan.md", "tasks.md", "validation.md"}}
    hooks = config.get("hooks")
    if not isinstance(hooks, dict) or set(hooks) != set(required):
        raise ValueError("Faltan las etapas plan, implement o close")
    for stage, minimum in required.items():
        entry = hooks[stage]
        files = entry.get("required") if isinstance(entry, dict) else None
        if (not isinstance(files, list) or not all(isinstance(name, str) and Path(name).name == name for name in files)
                or not minimum.issubset(files)):
            raise ValueError(f"Artefactos inválidos o incompletos para {stage}")
    reviews = config.get("reviews")
    if not isinstance(reviews, dict) or set(reviews) != {"analyze", "close"}:
        raise ValueError("Faltan los perfiles de revisión de análisis y cierre")
    for name in reviews.values():
        resource(root, name, "agents")
    return config


def module_contracts(root: Path) -> dict[str, Path]:
    """El índice documental es la única fuente del catálogo de módulos."""
    index = root / ".specify/base/modulos/README.md"
    result = {"SDD": root / ".specify/guias/spec-driven.md"}
    for line in index.read_text(encoding="utf-8").splitlines():
        cells = line.split("|")
        if len(cells) < 6 or not re.fullmatch(r"MOD-\d{2}", cells[1].strip()):
            continue
        match = LINK.search(cells[-2])
        if not match:
            raise ValueError("Contrato sin enlace en el índice de módulos")
        target = (index.parent / match.group(1).strip("<>")).resolve()
        if not target.is_file() or not target.is_relative_to(index.parent):
            raise ValueError("Contrato de módulo ausente o fuera de base/modulos")
        result[cells[1].strip()] = target
    if len(result) < 2:
        raise ValueError("El índice no declara módulos implementados")
    return result


def feature_directory(root: Path, identifier: str) -> Path:
    path = Path(identifier)
    directory = (root / ".specify/specs" / identifier if len(path.parts) == 1
                 else root / path).resolve()
    boundary = (root / ".specify/specs").resolve()
    if (not directory.is_dir() or directory.parent != boundary
            or not re.fullmatch(r"(?:\d{3,}|\d{8}-\d{6})-[a-zA-Z0-9][\w-]*", directory.name)):
        raise ValueError("Feature inexistente o fuera de .specify/specs")
    return directory


def check_structure(root: Path) -> list[str]:
    load_settings(root)
    module_contracts(root)
    errors = []
    for name in ["docs", "specs"]:
        if os.path.lexists(root / name):
            errors.append(f"No debe existir carpeta ni enlace {name}/ en la raíz")
    base = root / ".specify"
    if base.is_symlink() or (base / "specs").is_symlink():
        errors.append(".specify y su carpeta specs deben ser reales")
    names = {"arquitectura.md", "diseno.md", "DoD.md", "Backlog.md", "RETRO_ACTIONS.md"}
    if not (base / "docs").is_dir() or {p.name for p in (base / "docs").iterdir()} != names:
        errors.append("docs debe contener únicamente los cinco documentos del equipo")
    skills = ["gym-spec-driven", *("speckit-" + name for name in (
        "specify", "clarify", "plan", "tasks", "analyze", "implement", "converge",
        "constitution", "checklist", "taskstoissues"))]
    for name in skills:
        alias = root / ".agents/skills" / name
        expected = base / ".codex/skills" / name
        if not alias.is_symlink() or alias.resolve() != expected.resolve() or not (alias / "SKILL.md").is_file():
            errors.append(f"Skill no descubrible: {name}")
    return errors


def prose(content: str) -> str:
    """Los ejemplos de código no son enlaces documentales activos."""
    return re.sub(r"^```[^\n]*\n.*?^```\s*$", "", content, flags=re.MULTILINE | re.DOTALL)


def documents(root: Path) -> list[Path]:
    return sorted({
        root / "AGENTS.md", root / "README.md",
        root / ".specify/README.md", root / ".specify/UPSTREAM.md",
        root / ".specify/AGENTS.md", root / ".specify/.codex/preamble.md",
        *root.glob(".specify/docs/**/*.md"), *root.glob(".specify/specs/**/*.md"),
        *root.glob(".specify/base/**/*.md"), *root.glob(".specify/guias/**/*.md"),
        *root.glob(".specify/.codex/rules/**/*.md"),
        *root.glob(".specify/.codex/hooks/**/*.md"),
        *root.glob(".specify/.codex/agents/**/*.md"),
        *root.glob(".specify/memory/*.md"),
        *root.glob(".specify/templates/overrides/*.md"),
        root / ".specify/.codex/skills/gym-spec-driven/SKILL.md",
    })


def contracts(root: Path) -> list[Path]:
    return sorted({*root.glob(".specify/base/modulos/[0-9]*.md"),
                   *root.glob(".specify/specs/*/spec.md")})


def check_links(path: Path, content: str) -> list[str]:
    errors = []
    for match in LINK.finditer(prose(content)):
        destination = match.group(1).strip("<>")
        url = urlsplit(destination)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (path.parent / unquote(url.path)).resolve()
        if not target.exists():
            errors.append(f"enlace local inexistente: {destination}")
    return errors


def check_contract(content: str) -> list[str]:
    errors = []
    text = prose(content)
    headings = list(re.finditer(r"^## ([1-7])\. (.+)$", text, re.MULTILINE))
    expected = [(str(i), name) for i, name in enumerate(COMPONENTS, 1)]
    if [(h.group(1), h.group(2)) for h in headings] != expected:
        errors.append("se requieren los siete componentes, numerados y en orden")
    for heading in headings:
        remaining = text[heading.end():]
        next_heading = re.search(r"^## ", remaining, re.MULTILINE)
        body = remaining[:next_heading.start()] if next_heading else remaining
        if not body.strip():
            errors.append(f"componente vacío: {heading.group(2)}")
    criteria = CRITERION.findall(text)
    expected_ids = [f"CA-{i:02d}" for i in range(1, len(criteria) + 1)]
    if not criteria or criteria != expected_ids:
        errors.append("criterios CA-01… consecutivos, únicos y numerados requeridos")
    evidence = ROW.findall(text)
    if [row[0] for row in evidence] != criteria:
        errors.append("la tabla de evidencia debe tener una fila por criterio y en el mismo orden")
    for identifier, cell in evidence:
        if not LINK.search(cell):
            errors.append(f"{identifier} necesita un enlace a su evidencia local")
        elif not any(not urlsplit(m.group(1).strip('<>')).scheme
                     and urlsplit(m.group(1).strip('<>')).path
                     for m in LINK.finditer(cell)):
            errors.append(f"{identifier} necesita evidencia localizada en el repositorio")
    if re.search(r"\[NEEDS CLARIFICATION\b|\bTODO\b|\[NOMBRE DEL CAMBIO\]", text):
        errors.append("quedan marcadores sin resolver en el contrato")
    return errors


def local_targets(path: Path, content: str) -> set[Path]:
    targets = set()
    for match in LINK.finditer(prose(content)):
        url = urlsplit(match.group(1).strip("<>"))
        if not url.scheme and not url.netloc and url.path:
            targets.add((path.parent / unquote(url.path)).resolve())
    return targets


def check_feature(root: Path, directory: Path, *, stage: str = "implement") -> list[str]:
    """Comprueba trazabilidad de la base antes del plan/código/cierre; no ejecuta tests."""
    errors = []
    spec_path, context_path = directory / "spec.md", directory / "context.md"
    required = [directory / name for name in load_settings(root)["hooks"][stage]["required"]]
    for path in required:
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"falta artefacto requerido: {path.name}")
    if errors:
        return errors
    spec_content = spec_path.read_text(encoding="utf-8")
    errors.extend(check_contract(spec_content))
    errors.extend(check_links(spec_path, spec_content))
    content = context_path.read_text(encoding="utf-8")
    for heading in ["Base obligatoria", "Módulos afectados", "Código y pruebas existentes",
                    "Restricciones que se deben contrastar", "Evaluación específica del cambio"]:
        if f"## {heading}" not in content:
            errors.append(f"context.md: falta {heading}")
    if "Pendiente:" in content:
        errors.append("context.md: completar la evaluación específica antes del plan")
    modules = re.findall(r"\*\*(MOD-\d{2}|SDD)\*\*", content)
    registry = module_contracts(root)
    if not modules:
        errors.append("context.md: no identifica módulos del índice")
    targets = local_targets(context_path, content)
    base_names = ["AGENTS.md", ".specify/memory/constitution.md",
                  ".specify/specs/000-base-implementada/spec.md",
                  ".specify/base/modulos/README.md", ".specify/docs/arquitectura.md",
                  ".specify/docs/diseno.md", ".specify/.codex/rules/seguridad.md", ".specify/docs/DoD.md"]
    for name in base_names:
        if (root / name).resolve() not in targets:
            errors.append(f"context.md: no enlaza la base obligatoria {name}")
    for identifier in modules:
        if identifier not in registry:
            errors.append(f"context.md: módulo desconocido {identifier}")
            continue
        document = registry[identifier]
        if document not in targets:
            errors.append(f"context.md: falta el contrato de {identifier}")
    errors.extend(check_links(context_path, content))
    if stage in {"implement", "close"}:
        plan = directory / "plan.md"
        errors.extend(check_links(plan, plan.read_text(encoding="utf-8")))
        errors.extend(check_links(directory / "tasks.md", (directory / "tasks.md").read_text(encoding="utf-8")))
        if context_path.resolve() not in local_targets(plan, plan.read_text(encoding="utf-8")):
            errors.append("plan.md: debe enlazar context.md")
        criteria = set(CRITERION.findall(spec_content))
        task_content = (directory / "tasks.md").read_text(encoding="utf-8")
        missing = criteria - set(re.findall(r"CA-\d{2,}", task_content))
        if missing:
            errors.append("tasks.md: criterios sin tarea: " + ", ".join(sorted(missing)))
    if stage == "close":
        if re.search(r"^- \[ \]", task_content, re.MULTILINE):
            errors.append("tasks.md: quedan tareas abiertas")
        validation = (directory / "validation.md").read_text(encoding="utf-8")
        if "Pendiente" in validation or "pendiente de ejecución" in validation:
            errors.append("validation.md: falta evidencia de ejecución")
    return errors


def validate(root: Path) -> tuple[list[str], int, int]:
    errors = []
    files = documents(root)
    specs = contracts(root)
    if not specs:
        errors.append("no se encontraron contratos de módulos o especificaciones")
    for path in files:
        label = path.relative_to(root)
        if not path.is_file():
            errors.append(f"{label}: documento requerido inexistente")
            continue
        content = path.read_text(encoding="utf-8")
        for error in check_links(path, content):
            errors.append(f"{label}: {error}")
        if path in specs:
            for error in check_contract(content):
                errors.append(f"{label}: {error}")
            if path.parent.parent == root / ".specify/specs" and not path.parent.name.startswith("000-"):
                for error in check_feature(root, path.parent):
                    errors.append(f"{label}: {error}")
    return errors, len(files), len(specs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", help="Nombre o ruta de una feature existente")
    parser.add_argument("--stage", choices=["plan", "implement", "close"])
    args = parser.parse_args()
    if args.stage and not args.feature:
        parser.error("--stage requiere --feature")
    try:
        errors = check_structure(ROOT)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.feature:
            directory = feature_directory(ROOT, args.feature)
            stage = args.stage or "implement"
            errors += check_feature(ROOT, directory, stage=stage)
            summary = f"Precondiciones de {stage} correctas: {directory.name}."
        else:
            found, count, spec_count = validate(ROOT)
            errors += found
            summary = f"Documentación válida: {count} archivos, {spec_count} contratos de siete componentes."
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(summary)
        print("Comprueba estructura y trazabilidad; las pruebas funcionales se ejecutan por separado.")
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
