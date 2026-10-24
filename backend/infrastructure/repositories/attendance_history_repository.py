"""Historial filtrado y paginado en PostgREST, independiente de la caché global."""
from application.read_models import AttendanceCriteria, AttendancePage, AttendanceSummaryData, PageRequest
from infrastructure.repositories.mappers.attendance import _map_attendance
from infrastructure.repositories.mappers.accounts import _map_client


class AttendanceHistoryRepository:
    def __init__(self, database):
        self.database = database

    def summary(self, day: str, client_id: int | None = None) -> AttendanceSummaryData:
        valid = {"or": "(anulado.is.null,anulado.eq.false)"}
        if client_id is not None:
            valid["id_cliente"] = f"eq.{client_id}"
        entries = self.database.count("ASISTENCIA", {**valid, "Fecha": f"eq.{day}"})
        exits = self.database.count("ASISTENCIA", {**valid, "hora_salida": "not.is.null",
            "and": f"(or(fecha_salida.eq.{day},and(fecha_salida.is.null,Fecha.eq.{day})))"})
        inside = self.database.select_filtered("ASISTENCIA", {**valid, "hora_salida": "is.null"},
                                               order="Fecha.desc,Hora.desc.nullslast,id_asistencia.desc")
        recent = self.database.select_page("ASISTENCIA", {**valid, "Fecha": f"eq.{day}"},
            order="Fecha.desc,Hora.desc.nullslast,id_asistencia.desc", offset=0, limit=8).rows
        ids = sorted({int(row["id_cliente"]) for row in [*inside, *recent]})
        clients = self.database.select_filtered("CLIENTES", {"id_cliente": "in.(" + ",".join(map(str, ids)) + ")"},
                                               order="id_cliente.asc") if ids else []
        return AttendanceSummaryData(entries, exits, [_map_attendance(row) for row in inside],
                                     [_map_attendance(row) for row in recent], [_map_client(row) for row in clients])

    def page(self, criteria: AttendanceCriteria, request: PageRequest) -> AttendancePage:
        filters, conditions = {}, []
        client_ids = None
        if criteria.dni:
            clients = self.database.select_filtered("CLIENTES", {"DNI": f"eq.{criteria.dni}"}, order="id_cliente.asc")
            client_ids = [int(row["id_cliente"]) for row in clients]
        if criteria.client_id is not None:
            client_ids = [criteria.client_id] if client_ids is None or criteria.client_id in client_ids else []
        if client_ids == []:
            return AttendancePage([], [], 0)
        if client_ids is not None:
            filters["id_cliente"] = "in.(" + ",".join(map(str, client_ids)) + ")"
        if criteria.since:
            conditions.append(f"Fecha.gte.{criteria.since}")
        if criteria.until:
            conditions.append(f"Fecha.lte.{criteria.until}")
        if criteria.service:
            filters["servicio"] = f"eq.{criteria.service}"
        if criteria.kind:
            conditions.append("servicio.eq.gimnasio" if criteria.kind == "general" else "or(servicio.is.null,servicio.neq.gimnasio)")
        if not criteria.include_annulled or criteria.status in {"dentro", "completada"}:
            conditions.append("or(anulado.is.null,anulado.eq.false)")
        if criteria.status == "anulada":
            conditions.append("anulado.eq.true")
        elif criteria.status == "dentro":
            conditions.append("hora_salida.is.null")
        elif criteria.status == "completada":
            conditions.append("hora_salida.not.is.null")
        if conditions:
            filters["and"] = "(" + ",".join(conditions) + ")"
        page = self.database.select_page("ASISTENCIA", filters,
            order="Fecha.desc,Hora.desc.nullslast,id_asistencia.desc", offset=request.offset, limit=request.page_size)
        ids = sorted({int(row["id_cliente"]) for row in page.rows})
        clients = self.database.select_filtered("CLIENTES", {"id_cliente": "in.(" + ",".join(map(str, ids)) + ")"},
                                               order="id_cliente.asc") if ids else []
        return AttendancePage([_map_attendance(row) for row in page.rows], [_map_client(row) for row in clients], page.total)
