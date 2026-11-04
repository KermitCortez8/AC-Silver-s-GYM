"""Genera láminas de revisión desde las ECU y capturas reales del prototipo."""
from pathlib import Path
import html
import json
import re

base = Path(__file__).resolve().parent
source = (base.parent / "casos-de-uso.md").read_text()
results = json.loads((base / "resultados.json").read_text())


def inline(text):
    value = html.escape(text)
    value = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"`(.*?)`", r"<code>\1</code>", value)
    return re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", value)


def markdown(text):
    output, paragraph, mode = [], [], None

    def flush():
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    for line in text.splitlines() + [""]:
        if not line.strip():
            flush()
            if mode:
                output.append(f"</{mode}>")
                mode = None
        elif line.startswith("#"):
            flush()
            if mode:
                output.append(f"</{mode}>")
                mode = None
            heading = re.match(r"^(#+)\s+(.*)", line)
            level = min(len(heading[1]) + 1, 6)
            output.append(f"<h{level}>" + inline(heading[2]) + f"</h{level}>")
        elif line.startswith("|"):
            flush()
            if re.match(r"\|\s*[-:]+", line):
                continue
            if mode != "table":
                output.append("<table>")
                mode = "table"
            output.append("<tr>" + "".join("<td>" + inline(cell.strip()) + "</td>" for cell in line.strip("|").split("|")) + "</tr>")
        elif re.match(r"^\d+\. ", line) or line.startswith("- "):
            flush()
            kind = "ol" if re.match(r"^\d+\. ", line) else "ul"
            if mode != kind:
                if mode:
                    output.append(f"</{mode}>")
                output.append(f"<{kind}>")
                mode = kind
            output.append("<li>" + inline(re.sub(r"^(?:\d+\.|-) ", "", line)) + "</li>")
        else:
            paragraph.append(line)
    return "\n".join(output)


parts = re.split(r"^## (CU-CHAT-\d+[^\n]*)$", source, flags=re.M)
cases = "".join(
    '<section class="sheet ecu"><div class="folio">SPEC 002 · CASO DE USO Y ECU</div><h2>'
    + html.escape(parts[index]) + "</h2>" + markdown(parts[index + 1].split("## Qué demuestra")[0]) + "</section>"
    for index in range(1, len(parts), 2)
)
full_spec = '<section class="sheet ecu full-spec"><div class="folio">SPEC 002 · ESPECIFICACIÓN COMPLETA</div>' + markdown((base.parent / 'spec.md').read_text()) + '</section>'
programming = '<section class="sheet ecu full-spec"><div class="folio">SPEC 002 · PROGRAMACIÓN DE LOS PROTOTIPOS</div>' + markdown((base.parent / 'programacion-prototipos.md').read_text()) + '</section>'

mapping = {
    "p01": ("CU-CHAT-01 · Preregistro", "CA-01 · CA-02", "Consultar planes y comenzar el recorrido."),
    "p02": ("CU-CHAT-01 · Preregistro", "CA-02 · CA-07 · CA-08", "Completar datos en el formulario y respetar sus límites."),
    "p03": ("CU-CHAT-01 · Preregistro", "CA-02", "Diferenciar solicitud pendiente, pago y activación."),
    "p04": ("CU-CHAT-02 · Acceso", "CA-03 · CA-07", "Usar el formulario de acceso fuera de la conversación."),
    "p05": ("CU-CHAT-02 · Acceso", "CA-03", "Mantener el bloqueo de una cuenta no habilitada."),
    "p06": ("CU-CHAT-02 · Acceso", "CA-03", "Mostrar acciones propias tras el ingreso simulado."),
    "p07": ("CU-CHAT-03 · Horarios y matrícula", "CA-04", "Buscar una sesión por servicio y fecha concreta."),
    "p08": ("CU-CHAT-03 · Horarios y matrícula", "CA-05", "Revisar y confirmar con una acción explícita del cliente."),
    "p09": ("CU-CHAT-03 · Horarios y matrícula", "CA-05 · CA-06", "Mostrar una única inscripción local de ejemplo."),
    "p10": ("CU-CHAT-03 · Horarios y matrícula", "CA-06", "Resolver falta de cupo y respuesta incierta sin anunciar éxito falso."),
    "ayuda": ("Estado transversal · Ayuda guiada", "CA-08 · CA-09", "Mantener disponibles las acciones cuando falla la IA."),
}
plates = []
for name in results["captures"]:
    key = name.split("-")[0]
    case, criteria, purpose = mapping[key]
    mobile = "-movil" in name
    plates.append(
        '<section class="sheet plate"><div class="folio">SPEC 002 · PROTOTIPO '
        + ("MÓVIL" if mobile else "ESCRITORIO") + "</div><h2>" + case + "</h2>"
        + '<p class="caption"><strong>' + criteria + "</strong> · " + purpose + "</p>"
        + '<a href="capturas/' + name + '"><img class="' + ("mobile" if mobile else "desktop")
        + '" src="capturas/' + name + '" alt="' + html.escape(name.removesuffix(".png").replace("-", " ")) + '"></a></section>'
    )

document = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Specs, ECU y prototipos · Chatbot Silver</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9edef;color:#1d2a33;font:14px/1.6 Arial,sans-serif}.toolbar{background:#172027;color:white;padding:18px 30px;display:flex;gap:25px;align-items:center}.toolbar a{color:white;text-decoration:none}.toolbar button{margin-left:auto;border:0;background:#d9252c;color:white;padding:11px 18px;border-radius:6px;cursor:pointer}.sheet{background:white;margin:24px auto;padding:35px 42px;width:min(1100px,96%);box-shadow:0 5px 20px #2336450c}.folio{font-size:10px;letter-spacing:1.5px;color:#b62b33;font-weight:bold;margin-bottom:14px}h1{font-size:44px;line-height:1.1;letter-spacing:-1.7px;margin:15px 0 25px}h2{font-size:23px;letter-spacing:-.5px;margin:0 0 16px}.cover{min-height:550px;padding:70px}.cover p{max-width:680px;color:#627480}.cover .badge{display:inline-block;border:1px solid #e1c8ca;background:#fff4f4;color:#b82d37;padding:8px 12px;border-radius:6px;font-size:12px;margin-top:20px}.summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:35px}.summary div{padding:18px;border:1px solid #dde5e9;border-radius:8px;font-size:12px}.summary strong{display:block;color:#213743;margin-bottom:8px}table{border-collapse:collapse;width:100%;margin:12px 0 18px;font-size:12px}td{border:1px solid #e0e6e9;padding:6px 9px;vertical-align:top}td:first-child{width:24%;font-weight:bold;background:#f6f8f9}tr:first-child td{background:#eaf0f3}.ecu p{font-size:12px;margin:10px 0}.ecu li{font-size:12px;line-height:1.5;margin:3px 0}.ecu ol,.ecu ul{padding-left:20px}.caption{font-size:12px;color:#74848e}.caption strong{color:#b22e36}img{display:block;max-width:100%;height:auto;margin:20px auto}.mobile{max-width:360px}.plate{page-break-inside:avoid}.cover small{display:block;color:#8e9ca4;margin-top:30px}@page{size:A4 landscape;margin:10mm}@media print{body{background:white}.toolbar{display:none}.sheet{margin:0;padding:4mm 6mm;width:100%;height:186mm;box-shadow:none;break-after:page;overflow:hidden}.sheet:last-child{break-after:auto}.folio{font-size:8px;margin-bottom:6px}h2{font-size:18px;margin-bottom:6px}.cover{padding:20mm}.cover h1{font-size:40px}.cover p{font-size:13px}.summary{margin-top:20px}.ecu td{font-size:11px;padding:5px 8px}.ecu p,.ecu li{font-size:11px;line-height:1.5;margin:4px 0}.ecu ol,.ecu ul{margin:5px 0}.ecu table{margin:7px 0 9px}.plate h2{font-size:17px}.plate .caption{font-size:10px;margin:6px 0}.plate img{margin:5px auto 0;max-height:156mm;width:auto;max-width:100%;object-fit:contain}.plate img.mobile{max-height:153mm}}@media(max-width:700px){.sheet{padding:25px}.summary{display:block}.summary div{margin-bottom:10px}h1{font-size:32px}.toolbar{font-size:12px;padding:15px;gap:12px}.toolbar button{padding:8px}.cover{padding:35px}}
</style></head><body><nav class="toolbar"><strong>Specs + prototipos</strong><a href="index.html">Abrir demostración ↗</a><button onclick="print()">Imprimir / guardar PDF</button></nav>
<section class="sheet cover"><div class="folio">AC SILVER’S GYM · REVISIÓN DE DISEÑO</div><h1>Un asistente.<br>Todo el recorrido<br>del cliente.</h1><p>Specs, casos de uso y prototipos del chatbot: desde conocer un plan hasta revisar y confirmar una matrícula. Material para validar la propuesta antes de integrar la IA y los servicios.</p><span class="badge">Prototipos con datos simulados · Integración productiva pendiente</span><div class="summary"><div><strong>01 · Preregistro</strong>Planes, formulario y continuidad al pago.</div><div><strong>02 · Acceso</strong>Ingreso, activación pendiente y membresía vencida.</div><div><strong>03 · Horarios y matrícula</strong>Búsqueda, confirmación y resultados alternativos.</div></div><small>3 de noviembre de 2026 · 3 ECU · 16 capturas · 18 comprobaciones del prototipo.<br>Estas comprobaciones no equivalen a pruebas de la integración real con IA.</small></section>
'''
extra_style = '<style>.full-spec{height:auto;overflow:visible}.full-spec h3{font-size:15px;margin:20px 0 9px}.full-spec h4{font-size:12px;margin:12px 0 6px}@media print{.full-spec{height:auto;overflow:visible;min-height:186mm}.full-spec h3{font-size:12px;margin:12px 0 6px;break-after:avoid}.full-spec h4{font-size:10px;margin:8px 0 4px;break-after:avoid}.full-spec tr{break-inside:avoid}}</style>'
(base / "laminas.html").write_text(document + extra_style + full_spec + cases + programming + "".join(plates) + "</body></html>\n")
print(f"Láminas generadas: tres ECU y {len(plates)} capturas.")
