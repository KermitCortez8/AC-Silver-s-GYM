"""Adaptador local del mismo contrato paginado de historial."""
from copy import deepcopy
from application.read_models import AttendancePage, AttendanceSummaryData
from domain.services.client_identifiers import parse_client_id


def attendance_summary(state, day, client_id=None):
    valid = [row for row in state.get("asistencia", []) if not row.get("anulado")
             and (client_id is None or parse_client_id(row.get("id_cliente_num") or row.get("id_cliente")) == client_id)]
    today = sorted((row for row in valid if row.get("fecha") == day),
                   key=lambda row: (row.get("hora_entrada") or row.get("hora", ""), row["id_asistencia"]), reverse=True)
    inside = [row for row in valid if not row.get("hora_salida")]
    inside.sort(key=lambda row: (row.get("fecha", ""), row.get("hora_entrada") or row.get("hora", ""), row["id_asistencia"]), reverse=True)
    recent = today[:8]
    ids = {parse_client_id(row.get("id_cliente_num") or row.get("id_cliente")) for row in [*inside, *recent]}
    return AttendanceSummaryData(len(today),
        sum(bool(row.get("hora_salida")) and (row.get("fecha_salida") or row.get("fecha")) == day for row in valid),
        deepcopy(inside), deepcopy(recent), [deepcopy(row) for row in state.get("clientes", []) if row["id_cliente"] in ids])


def attendance_page(state, criteria, request):
    parse_id = parse_client_id
    clients = {int(row["id_cliente"]): row for row in state.get("clientes", [])}
    selected = []
    for row in state.get("asistencia", []):
        client_id = parse_id(row.get("id_cliente_num") or row.get("id_cliente"))
        status = "anulada" if row.get("anulado") else "completada" if row.get("hora_salida") else "dentro"
        kind = "general" if row.get("servicio") == "gimnasio" else "horario"
        if ((criteria.client_id is not None and client_id != criteria.client_id)
                or (not criteria.include_annulled and row.get("anulado"))
                or (criteria.dni and clients.get(client_id, {}).get("dni") != criteria.dni)
                or (criteria.since and row.get("fecha", "") < criteria.since)
                or (criteria.until and row.get("fecha", "") > criteria.until)
                or (criteria.service and row.get("servicio") != criteria.service)
                or (criteria.status and status != criteria.status)
                or (criteria.kind and kind != criteria.kind)):
            continue
        selected.append(row)
    selected.sort(key=lambda row: (row.get("fecha", ""), row.get("hora_entrada") or row.get("hora", ""), row["id_asistencia"]), reverse=True)
    page = deepcopy(selected[request.offset:request.offset + request.page_size])
    ids = {parse_id(row.get("id_cliente_num") or row.get("id_cliente")) for row in page}
    return AttendancePage(page, [deepcopy(clients[id_]) for id_ in ids if id_ in clients], len(selected))
