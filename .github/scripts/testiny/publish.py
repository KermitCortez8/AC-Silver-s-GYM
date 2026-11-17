#!/usr/bin/env python3
"""Normaliza JUnit por módulo/tipo; solo --publish permite contactar a Testiny."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
CLI_ENTRY = Path(__file__).parent / "node_modules/@testiny/cli/testiny-importer.js"
SOURCES = {
    "backend": "gym-backend",
    "frontend": "gym-frontend",
    "postgres": "gym-postgres",
    "schedule-emails": "gym-notificaciones-deno",
    "casos-documentados": "gym-casos-documentados",
}
LEVELS = {
    "unitarias": "Unitarias", "integracion": "Integración",
    "interfaz": "Funcionales de interfaz", "arquitectura": "Arquitectura",
    "postgres": "Integración PostgreSQL",
}
MAX_REPORT_BYTES = 10 * 1024 * 1024
MAX_CASES = 20_000
ATTACHMENT = re.compile(r"\[\[ATTACHMENT\|.*?\]\]", re.DOTALL | re.IGNORECASE)


def module_registry(root: Path = ROOT) -> dict[str, str]:
    """Reutiliza el índice central; no mantiene otro catálogo de módulos."""
    result = {}
    text = (root / ".specify/base/modulos/README.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 6 or not re.fullmatch(r"MOD-\d{2}", cells[1]):
            continue
        match = re.search(r"\((\d{2}-[\w-]+)\.md\)", cells[-2])
        if match:
            slug = match[1][3:].replace("-", "_")
            result[slug] = f"{cells[1]} - {cells[2]}"
    if len(result) != 11:
        raise ValueError("No se pudo resolver el índice de los once módulos")
    return result


def clean_text(value: str | None, limit: int = 8_192) -> str:
    # No aceptar los marcadores que el importador interpreta como archivos adjuntos.
    return ATTACHMENT.sub("[adjunto omitido]", value or "")[:limit]


def case_identity(case: ET.Element, component: str, modules: dict[str, str], ancestors=()):
    original_name = case.get("name", "").strip()
    if not original_name:
        raise ValueError("Caso JUnit sin nombre")
    identifier = case.get("classname", "")
    name = original_name
    if component == "frontend":
        if "::" not in original_name:
            raise ValueError("El JUnit del frontend no incluye el archivo; usar node-junit.mjs")
        identifier, name = original_name.split("::", 1)
        name = " / ".join([*ancestors, name])
    tokens = re.split(r"[./\\:]", identifier + "/" + original_name)
    module = next((modules[token] for token in tokens if token in modules), "Transversales")
    level = next((LEVELS[token] for token in tokens if token in LEVELS), "Integración")
    if component == "schedule-emails":
        module, level = modules["notificaciones"], "Integración Deno"
    if component == "postgres":
        level = "Integración PostgreSQL"
    filename = Path(identifier.replace("\\", "/")).name or "suite"
    if component in {"backend", "postgres"}:
        filename = identifier.split(".")[-1] or "colección"
    filename = re.sub(r"[^\w-]", "_", filename)[:180]
    # La clave no es TC-N: un test técnico no aprueba un caso manual de aceptación.
    digest = hashlib.sha256(f"{component}\n{identifier}\n{original_name}\n{'/'.join(ancestors)}".encode()).hexdigest()
    return clean_text(name, 2_000), f"{module}.{level}.{filename}", f"gym-{component}-{digest}"


def normalize_report(source: Path, destination: Path, component: str, modules: dict[str, str], evidence=None):
    if source.is_symlink() or source.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError(f"Informe no admitido: {source.name}")
    data = source.read_bytes().decode("utf-8-sig")
    if "\x00" in data or "<!DOCTYPE" in data.upper() or "<!ENTITY" in data.upper():
        raise ValueError("No se admiten DTD ni entidades XML en resultados")
    original = ET.fromstring(data)
    if original.tag not in {"testsuites", "testsuite"}:
        raise ValueError("El archivo no es un informe JUnit")
    cases = list(original.iter("testcase"))
    parents = {child: parent for parent in original.iter() for child in parent}
    if not cases or len(cases) > MAX_CASES:
        raise ValueError("Informe vacío o cantidad de casos fuera del límite")
    root = ET.Element("testsuites")
    suites: dict[str, ET.Element] = {}
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    identities = set()
    for case in cases:
        ancestors = []
        parent = parents.get(case)
        while parent is not None and component == "frontend":
            if parent.tag == "testsuite" and parent.get("name"):
                ancestors.append(parent.get("name").split("::", 1)[-1])
            parent = parents.get(parent)
        name, folder, key = case_identity(case, component, modules, tuple(reversed(ancestors)))
        if key in identities:
            raise ValueError(f"Identidad duplicada en JUnit: {name}")
        identities.add(key)
        duration = float(case.get("time", "0"))
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("Duración JUnit inválida")
        if folder not in suites:
            suites[folder] = ET.SubElement(root, "testsuite", name=folder)
        suite = suites[folder]
        result = ET.SubElement(suite, "testcase", name=name, classname=folder, time=f"{duration:.6f}")
        properties = ET.SubElement(result, "properties")
        ET.SubElement(properties, "property", name="testkey", value=key)
        totals["tests"] += 1
        # Copiar solo el resultado; ignorar adjuntos, propiedades y rutas del artefacto.
        for tag, counter in [("error", "errors"), ("failure", "failures"), ("skipped", "skipped")]:
            outcome = case.find(tag)
            if outcome is not None:
                node = ET.SubElement(result, tag, message=clean_text(outcome.get("message"), 512))
                node.text = clean_text("".join(outcome.itertext()))
                totals[counter] += 1
                break
        else:
            status = case.get("status", "passed").lower()
            if status in {"skipped", "disabled", "notrun", "untested", "blocked"}:
                ET.SubElement(result, "skipped", message=f"Estado original: {status}")
                totals["skipped"] += 1
            elif status not in {"passed", "pass", "success", "run"}:
                raise ValueError(f"Estado JUnit sin resultado interpretable: {status}")
        if evidence is not None:
            identifier = case.get("classname", "")
            original_name = case.get("name", "")
            if component == "frontend":
                identifier, original_name = original_name.split("::", 1)
            outcome = next((tag for tag in ("error", "failure", "skipped")
                            if result.find(tag) is not None), "passed")
            evidence.append({"componente": component, "clase": identifier,
                             "prueba": original_name, "ancestros": list(reversed(ancestors)),
                             "estado": outcome, "duracion": duration})
    for suite in suites.values():
        children = suite.findall("testcase")
        suite.set("tests", str(len(children)))
        for tag, counter in [("failure", "failures"), ("error", "errors"), ("skipped", "skipped")]:
            suite.set(counter, str(sum(child.find(tag) is not None for child in children)))
        suite.set("time", f"{sum(float(child.get('time')) for child in children):.6f}")
    for key, value in totals.items():
        root.set(key, str(value))
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    return totals


def prepare_reports(incoming: Path, output: Path, documented=False) -> list[dict]:
    modules = module_registry()
    prepared = []
    evidence = []
    for component in SOURCES:
        if component == "casos-documentados":
            continue  # Siempre se calcula desde pruebas reales; no aceptar XML ajeno para este resumen.
        source = incoming / f"{component}.xml"
        if not source.is_file():
            continue
        if not source.resolve().is_relative_to(incoming.resolve()):
            raise ValueError("Informe fuera del directorio de artefactos")
        destination = output / f"{component}.xml"
        report = {"component": component, "file": str(destination),
                  **normalize_report(source, destination, component, modules, evidence)}
        metadata = source.with_suffix(".metadata.json")
        if metadata.is_file():
            if (metadata.is_symlink() or not metadata.resolve().is_relative_to(incoming.resolve())
                    or metadata.stat().st_size > 262_144):
                raise ValueError("Metadatos del informe fuera de límite")
            report["metadata"] = json.loads(metadata.read_text(encoding="utf-8"))
        prepared.append(report)
    if not prepared:
        raise ValueError("No hay informes JUnit de estas suites; no se creará una ejecución vacía")
    if documented:
        spec = importlib.util.spec_from_file_location("gym_documented_cases", Path(__file__).with_name("documented_cases.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report, summary = module.build_report(ROOT, output, evidence, prepared)
        print(f"Casos documentados ejecutados: {summary['ejecutados']}/{summary['total_documentados']} "
              f"({summary['porcentaje_ejecutado']} %)")
        prepared.append(report)
    output.mkdir(parents=True, exist_ok=True)
    (output / "resumen.json").write_text(json.dumps(prepared, indent=2, ensure_ascii=False), encoding="utf-8")
    return prepared


def run_fields(event: dict) -> dict[str, str]:
    run = event.get("workflow_run") or {}
    if not run:
        pr = event.get("pull_request") or {}
        if (os.environ.get("GITHUB_EVENT_NAME") != "pull_request"
                or os.environ.get("GITHUB_WORKFLOW") != "CI/CD Pipeline GYM"
                or event.get("action") != "closed" or pr.get("merged") is not True
                or (pr.get("base") or {}).get("ref") != "main"):
            raise ValueError("Solo se publica el merge a main del pipeline CI/CD")
        repository = (event.get("repository") or {}).get("full_name", "")
        run = {
            "id": os.environ["GITHUB_RUN_ID"], "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
            "name": "CI/CD Pipeline GYM", "conclusion": "success",
            "head_repository": {"full_name": repository},
            "head_sha": pr.get("merge_commit_sha", ""), "head_branch": "main",
            "html_url": f"{os.environ['GITHUB_SERVER_URL']}/{repository}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        }
    repository = (event.get("repository") or {}).get("full_name", "")
    head_repository = (run.get("head_repository") or {}).get("full_name", "")
    if not repository or repository != head_repository:
        raise ValueError("Solo se publican ejecuciones originadas en este repositorio")
    if run.get("name") not in {"Validar PR", "CI/CD Pipeline GYM"}:
        raise ValueError("Workflow de origen no admitido")
    if run.get("conclusion") not in {"success", "failure", "timed_out"}:
        raise ValueError("La ejecución de origen no terminó con resultados publicables")
    if not re.fullmatch(r"[0-9a-f]{40}", run.get("head_sha", "")):
        raise ValueError("Commit de origen inválido")
    values = {
        "ci_repository": repository, "ci_run_id": str(int(run["id"])),
        "ci_retry": str(int(run["run_attempt"])), "ci_build_url": run["html_url"],
        "ci_workflow_name": run["name"], "vc_ref": run["head_branch"], "vc_commit": run["head_sha"],
    }
    return {key: str(value).replace(",", "%2C").replace("\n", " ")[:1_000]
            for key, value in values.items()}


def report_fields(report: dict, origin: dict[str, str]) -> dict[str, str]:
    metadata = report.get("metadata")
    if not isinstance(metadata, dict) or any([
        metadata.get("component") != report["component"],
        metadata.get("repository") != origin["ci_repository"],
        str(metadata.get("run_id")) != origin["ci_run_id"],
        str(metadata.get("run_attempt")) != origin["ci_retry"],
        not re.fullmatch(r"[0-9a-f]{40}", str(metadata.get("commit", ""))),
    ]):
        raise ValueError("Faltan metadatos coherentes con el workflow de origen")
    # Un PR comprueba su merge provisional, no necesariamente head_sha del evento.
    return {**origin, "vc_source_commit": origin["vc_commit"], "vc_commit": metadata["commit"]}


def import_command(report: dict, project: str, fields: dict[str, str], node: str):
    source = SOURCES[report["component"]]
    # Convención del proyecto compatible con isValidAutomationSourceName de la CLI:
    # sin espacios ni acentos, con prefijo propio que evita nombres reservados.
    if not re.fullmatch(r"gym-[a-z0-9]+(?:-[a-z0-9]+)*", source):
        raise ValueError(f"Fuente de Testiny inválida: {source!r}; "
                         "usar gym- y palabras en minúsculas separadas por guiones")
    command = [node, str(CLI_ENTRY), "automation", "--project", project,
            "--source", source, "--no-attachments",
            "--junit-classname-as-folder", "nested", "--junit-duration-unit", "sec",
            "--run-fields", "ci_repository,ci_run_id,ci_retry",
            "--run-title-pattern", "%{ci_workflow_name} - %{vc_ref} - %{ci_run_id} (%{ci_retry})",
            "--field-values", ",".join(f"{key}={value}" for key, value in fields.items()),
            "--junit", report["file"]]
    if report["component"] == "casos-documentados":
        command.extend(["--custom-result-fields", "rf,cus,manual_case_url,testiny_case_id,tipo_documentado"])
    return command


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incoming", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--event", type=Path, default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--project", default=os.environ.get("TESTINY_PROJECT", "SILVE"))
    parser.add_argument("--publish", action="store_true", help="Importa en Testiny; por defecto solo prepara XML")
    parser.add_argument("--documented", action="store_true", help="Exige ejecutar al menos el 50 % de casos documentados revisados")
    args = parser.parse_args(argv)
    try:
        reports = prepare_reports(args.incoming, args.output, args.documented)
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        if not args.publish:
            print("Solo preparación local. No se contactó a Testiny.")
            return 0
        if not os.environ.get("TESTINY_API_KEY"):
            raise ValueError("Falta TESTINY_API_KEY en GitHub Settings > Secrets and variables > Actions")
        if not args.event or not args.project.strip():
            raise ValueError("Falta el evento de GitHub o TESTINY_PROJECT")
        fields = run_fields(json.loads(args.event.read_text(encoding="utf-8")))
        node = shutil.which("node")
        if not node or not CLI_ENTRY.is_file():
            raise ValueError("Instalar Node >=22.17 y ejecutar npm ci en .github/scripts/testiny")
        commands = [import_command(report, args.project, report_fields(report, fields), node)
                    for report in reports]
        for command in commands:
            # Sin shell, sin clave en argumentos y sin reintentos de publicación automática.
            subprocess.run(command, check=True, timeout=180)
        return 0
    except (ValueError, KeyError, ET.ParseError, OSError, subprocess.SubprocessError) as error:
        print(f"Error de integración Testiny: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
