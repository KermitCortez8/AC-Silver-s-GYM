"""Relaciona resultados reales con los oráculos revisados del catálogo de Testiny."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


COMPONENT = "casos-documentados"
COMPONENTS = {"backend", "frontend", "postgres", "schedule-emails"}


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def source_fingerprint(source: Path) -> str:
    # Un checkout CRLF de Windows representa las mismas aserciones que LF en CI.
    return hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_review(root: Path):
    base = root / ".specify/base/testiny"
    catalog = json.loads((base / "catalogo.json").read_text(encoding="utf-8"))
    review = json.loads((base / "automatizacion.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in catalog["casos"]}
    if (catalog.get("proyecto") != "SILVE" or catalog.get("total") != len(cases)
            or len(cases) != len(catalog["casos"]) or not cases):
        raise ValueError("Catálogo Testiny inconsistente")
    if review.get("catalogo_sha256") != fingerprint(catalog) or review.get("minimo_porcentaje") != 50:
        raise ValueError("Revisar el catálogo actualizado y mantener el mínimo del 50 %")
    proofs = review["pruebas"]
    for key, proof in proofs.items():
        source = (root / proof["archivo"]).resolve()
        test_root = {"backend": "backend/tests", "postgres": "backend/tests",
                     "frontend": "frontend/tests", "schedule-emails": "supabase/tests"}.get(proof["componente"])
        if (proof["componente"] not in COMPONENTS or not source.is_relative_to(root.resolve())
                or not source.is_relative_to((root / test_root).resolve())
                or not source.is_file() or source.is_symlink()
                or proof["sha256"] != source_fingerprint(source)
                or not proof.get("prueba") or proof.get("minimo_variantes", 0) < 1):
            raise ValueError(f"La prueba {key} cambió o no tiene una revisión válida")
        relative = Path(proof["archivo"]).as_posix().split("/", 1)[1]
        expected = relative.removesuffix(".py").replace("/", ".") if proof["componente"] in {"backend", "postgres"} else relative
        if proof["componente"] != "schedule-emails" and not (proof["clase"] == expected or proof["clase"].startswith(expected + ".")):
            raise ValueError(f"La clase JUnit de {key} no corresponde a su archivo revisado")
    for name, expected_hash in review.get("soporte", {}).items():
        source = (root / name).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file() or source_fingerprint(source) != expected_hash:
            raise ValueError(f"El soporte de pruebas {name} requiere revisión")
    selected = {}
    for entry in review["casos"]:
        identity = entry["id"]
        if identity not in cases or identity in selected:
            raise ValueError("Caso revisado inexistente o duplicado")
        case = cases[identity]
        if entry["huella"] != case["huella"] or not entry.get("revision"):
            raise ValueError(f"TC-{identity}: falta revisar su contrato actual")
        steps = entry["pasos"]
        if sorted(step["paso"] for step in steps) != list(range(1, len(case["pasos"]) + 1)):
            raise ValueError(f"TC-{identity}: faltan resultados esperados por revisar")
        for step in steps:
            if not step.get("pruebas") or not step.get("verificacion"):
                raise ValueError(f"TC-{identity}: oráculo sin prueba ni justificación")
            if any(key not in proofs for key in step["pruebas"]):
                raise ValueError(f"TC-{identity}: referencia de prueba inexistente")
        selected[identity] = entry
    minimum = math.ceil(len(cases) / 2)
    if len(selected) < minimum:
        raise ValueError(f"Solo hay {len(selected)} casos revisados; se necesitan {minimum}/{len(cases)}")
    return cases, proofs, selected


def matches(record: dict, proof: dict) -> bool:
    name = record["prueba"]
    target = proof["prueba"]
    return (record["componente"] == proof["componente"]
            and record["clase"] == proof["clase"]
            and record.get("ancestros", []) == proof.get("ancestros", [])
            and (name == target or name.startswith(target + "[")))


def assess(cases: dict, proofs: dict, selected: dict, records: list[dict]):
    if any(record.get("estado") not in {"passed", "failure", "error", "skipped"} for record in records):
        raise ValueError("Estado de evidencia no interpretable")
    outcomes = {}
    for key, proof in proofs.items():
        found = [record for record in records if matches(record, proof)]
        # Todas las variantes son obligatorias: un skip nunca acredita el caso.
        if len(found) < proof["minimo_variantes"] or any(r["estado"] == "skipped" for r in found):
            status = "skipped"
        elif any(r["estado"] in {"failure", "error"} for r in found):
            status = "failure"
        else:
            status = "passed"
        outcomes[key] = {"estado": status, "variantes": len(found),
                         "duracion": sum(r["duracion"] for r in found)}
    results = []
    for identity, case in sorted(cases.items()):
        entry = selected.get(identity)
        refs = sorted({key for step in entry["pasos"] for key in step["pruebas"]}) if entry else []
        pending = [key for key in refs if outcomes[key]["estado"] == "skipped"]
        failed = [key for key in refs if outcomes[key]["estado"] == "failure"]
        status = "skipped" if not entry or pending else "failure" if failed else "passed"
        results.append({"id": identity, "codigo": case["codigo"], "modulo": case["modulo"],
                        "rf": case["rf"], "cus": case["cus"], "tipo": case["tipo"],
                        "estado": status, "revisado": bool(entry), "pruebas": refs,
                        "pendientes": pending, "fallidas": failed,
                        "duracion": sum(outcomes[key]["duracion"] for key in refs),
                        "url": case["url"]})
    return results, outcomes


def origin_metadata(reports: list[dict]):
    metadata = [report.get("metadata") for report in reports]
    if not any(metadata):
        return None  # Preparación local; publicar seguirá exigiendo metadatos.
    fields = ("repository", "run_id", "run_attempt", "commit")
    if (not all(isinstance(value, dict) for value in metadata)
            or any(any(value.get(key) != metadata[0].get(key) for key in fields) for value in metadata)):
        raise ValueError("No se combinan casos documentados de revisiones o ejecuciones distintas")
    return {**metadata[0], "component": COMPONENT}


def build_report(root: Path, output: Path, records: list[dict], reports: list[dict]):
    cases, proofs, selected = load_review(root)
    metadata = origin_metadata(reports)
    if metadata:
        # Comparar las aserciones del checkout que ejecutó las pruebas con su revisión.
        by_component = {report["component"]: report["metadata"].get("sources", {}) for report in reports}
        if not all(isinstance(sources, dict) for sources in by_component.values()):
            raise ValueError("Huellas de origen inválidas")
        for proof in proofs.values():
            if by_component.get(proof["componente"], {}).get(proof["archivo"]) != proof["sha256"]:
                raise ValueError(f"La ejecución no acredita las aserciones revisadas de {proof['archivo']}")
        for name, expected_hash in json.loads((root / ".specify/base/testiny/automatizacion.json").read_text(encoding="utf-8")).get("soporte", {}).items():
            if by_component.get(name.split('/')[0], {}).get(name) != expected_hash:
                raise ValueError(f"La ejecución no acredita el soporte revisado {name}")
    results, outcomes = assess(cases, proofs, selected, records)
    reviewed_results = [result for result in results if result["revisado"]]
    counts = Counter(result["estado"] for result in reviewed_results)
    total = len(cases)
    executed = counts["passed"] + counts["failure"]
    summary = {"total_documentados": total, "minimo_requerido": math.ceil(total / 2),
               "revisados": len(selected), "ejecutados": executed,
               "aprobados": counts["passed"], "fallidos": counts["failure"],
               "sin_ejecucion_completa": counts["skipped"], "pendientes_de_automatizar": total - len(selected),
               "porcentaje_ejecutado": round(executed * 100 / total, 2),
               "casos": results, "pruebas": outcomes}
    output.mkdir(parents=True, exist_ok=True)
    (output / "cobertura-documentada.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "trazabilidad-documentada.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["id", "codigo", "modulo", "rf", "cus", "tipo", "estado", "pruebas", "url"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({**row, "rf": ", ".join(row["rf"]), "pruebas": " | ".join(row["pruebas"])} for row in results)
    xml = ET.Element("testsuites", tests=str(len(selected)), failures=str(counts["failure"]), errors="0", skipped=str(counts["skipped"]))
    suites = {}
    for result in reviewed_results:
        case = cases[result["id"]]
        folder = f"{case['modulo']} - {case['nombre_modulo']}.{case['tipo']}.{case['rf'][0]}"
        if folder not in suites:
            suites[folder] = ET.SubElement(xml, "testsuite", name=folder)
        node = ET.SubElement(suites[folder], "testcase", classname=folder,
                             name=f"TC-{case['id']} | {case['codigo']} | {case['titulo']}",
                             time=f"{result['duracion']:.6f}")
        properties = ET.SubElement(node, "properties")
        for key, value in {"testkey": f"SILVE-TC-{case['id']}", "testiny_case_id": case["id"],
                           "rf": ", ".join(case["rf"]), "cus": case["cus"],
                           "tipo_documentado": case["tipo"], "manual_case_url": case["url"]}.items():
            ET.SubElement(properties, "property", name=key, value=str(value))
        if result["estado"] == "skipped":
            message = "Automatización completa pendiente de revisión" if not result["revisado"] else "Pruebas obligatorias ausentes u omitidas: " + ", ".join(result["pendientes"])
            ET.SubElement(node, "skipped", message=message)
        elif result["estado"] == "failure":
            ET.SubElement(node, "failure", message="Fallaron pruebas del caso documentado").text = ", ".join(result["fallidas"])
    for suite in suites.values():
        children = suite.findall("testcase")
        suite.set("tests", str(len(children)))
        suite.set("failures", str(sum(child.find("failure") is not None for child in children)))
        suite.set("skipped", str(sum(child.find("skipped") is not None for child in children)))
        suite.set("errors", "0")
    destination = output / f"{COMPONENT}.xml"
    ET.ElementTree(xml).write(destination, encoding="utf-8", xml_declaration=True)
    report = {"component": COMPONENT, "file": str(destination), "tests": len(selected),
              "failures": counts["failure"], "errors": 0, "skipped": counts["skipped"]}
    if metadata:
        report["metadata"] = metadata
    if executed < summary["minimo_requerido"]:
        raise ValueError(f"Cobertura documentada insuficiente: {executed}/{total}; mínimo {summary['minimo_requerido']}. Consultar cobertura-documentada.json")
    return report, summary
