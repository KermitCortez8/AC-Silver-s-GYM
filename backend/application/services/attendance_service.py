"""Asistencia administrada, con reloj de Perú e historial propio para el cliente."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")
DAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


from domain.errors import AttendanceConflict
from domain.services.membership_lifecycle import membership_current
from domain.services.attendance_status import attendance_status, LATE_EXIT_MESSAGE
from domain.services.schedule_sessions import enrollment_session, next_session
from application.read_models import AttendanceCriteria, PageRequest


class AttendanceService:
    def __init__(self, gym, clock=None):
        self.gym = gym
        self.clock = clock or (lambda: datetime.now(LIMA))

    def now(self):
        return self.clock().astimezone(LIMA).replace(microsecond=0)

    def client_id(self, row):
        return self.gym.parse_client_id(row.get("id_cliente_num") or row.get("id_cliente"))

    def status(self, row):
        return attendance_status(row, self.now())

    @staticmethod
    def kind(row):
        # Los registros históricos conservan su servicio; general usa el nuevo valor.
        return "general" if row.get("servicio") == "gimnasio" else "horario"

    def present(self, row, admin=True, client=None):
        if client is None:
            client = self.gym.get_cliente(self.client_id(row)) or {}
        result = {**deepcopy(row), "cliente_nombre": client.get("nombre", "Cliente"),
                  "cliente_dni": client.get("dni", ""), "estado": self.status(row),
                  "version": int(row.get("version") or 0), "tipo": self.kind(row)}
        result["aviso"] = LATE_EXIT_MESSAGE if result["estado"] == "incompleta" else ""
        if not admin:
            for key in ("auditoria", "id_usuario_registra"):
                result.pop(key, None)
        return result

    def records(self, user, desde=None, hasta=None, dni="", servicio="", estado="", tipo=""):
        # Los contratos de listado y exportación conservan la lista completa,
        # pero el filtrado y cada lectura acotada ocurren en persistencia.
        rows, page = [], 1
        while True:
            batch = self.history(user, page=page, page_size=100, desde=desde, hasta=hasta,
                                 dni=dni, servicio=servicio, estado=estado, tipo=tipo)
            rows.extend(batch["items"])
            if not batch["items"] or len(rows) >= batch["total"]:
                return rows
            page += 1

    def history(self, user, *, page=1, page_size=15, desde=None, hasta=None, dni="", servicio="", estado="", tipo=""):
        if desde and hasta and desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final.")
        admin = user.role == "admin"
        if not admin and not user.id_cliente:
            raise ValueError("No encontramos tu cliente vinculado.")
        criteria = AttendanceCriteria(client_id=None if admin else user.id_cliente, dni=dni,
            since=str(desde) if desde else "", until=str(hasta) if hasta else "",
            service=servicio, status=estado, kind=tipo, include_annulled=admin, at=self.now().isoformat())
        result = self.gym.attendance_page(criteria, PageRequest(page, page_size))
        clients = {int(row["id_cliente"]): row for row in result.clients}
        return {"items": [self.present(row, admin, clients.get(self.client_id(row), {})) for row in result.records],
                "total": result.total, "page": page, "page_size": page_size}

    def summary(self, user):
        today = self.now().date().isoformat()
        admin = user.role == "admin"
        if not admin and not user.id_cliente:
            raise ValueError("No encontramos tu cliente vinculado.")
        data = self.gym.attendance_summary(today, None if admin else user.id_cliente)
        clients = {int(row["id_cliente"]): row for row in data.clients}
        present = lambda row: self.present(row, admin, clients.get(self.client_id(row), {}))
        inside = [present(row) for row in data.inside]
        occupancy = len({self.client_id(row) for row in inside})
        capacity = self.capacity()
        return {"fecha": today, "server_now": self.now().isoformat(),
                "entradas": data.entries, "salidas": data.exits,
                "dentro": occupancy, "pendientes": inside, "capacidad": capacity,
                "disponibles": max(0, capacity - occupancy), "recientes": [present(row) for row in data.recent]}

    def membership(self, client_id, day):
        return next((m for m in self.gym.membresias_por_cliente(client_id)
                     if int(m.get("id_cliente") or 0) == client_id
                     and membership_current(m, day)), None)

    def capacity(self):
        return int(self.gym.configuracion_gimnasio().get("capacidad_total") or 30)

    def client_context(self, client_id, now):
        client = self.gym.get_cliente(client_id)
        if client and str(client.get("estado", "")).upper() == "VENCIDA":
            raise ValueError("El cliente necesita una membresía activa, pagada y vigente.")
        if not client or str(client.get("estado", "")).upper() != "ACTIVO":
            raise ValueError("La cuenta debe estar activada por el administrador.")
        member = self.membership(client_id, now.date().isoformat())
        if not member:
            raise ValueError("El cliente necesita una membresía activa, pagada y vigente.")
        return client, member

    def check_occupancy(self, client_id):
        inside = [r for r in self.gym.asistencia() if not r.get("anulado") and not r.get("hora_salida")]
        if any(self.client_id(r) == client_id for r in inside):
            raise ValueError("El cliente tiene una entrada sin salida. Registra su salida primero.")
        if len({self.client_id(r) for r in inside}) >= self.capacity():
            raise ValueError("El gimnasio alcanzó su aforo. Registra una salida antes de otra entrada.")

    def general_context(self, client_id, now):
        client, member = self.client_context(client_id, now)
        self.check_occupancy(client_id)
        return client, member

    def entry_context(self, enrollment, now):
        client_id = int(enrollment.get("id_cliente") or 0)
        client, member = self.client_context(client_id, now)
        if enrollment.get("estado") != "ACTIVA":
            raise ValueError("La matrícula no está activa.")
        schedule = self.gym.get_horario_servicio(int(enrollment.get("id_horario_servicio") or 0))
        if not schedule or not schedule.get("activo"):
            raise ValueError("El horario no está disponible.")
        if enrollment_session(enrollment, schedule) != now.date().isoformat():
            raise ValueError("La matrícula no corresponde a la fecha de esta clase.")
        if schedule.get("dia") != DAYS[now.weekday()]:
            raise ValueError("Este horario no corresponde a hoy.")
        try:
            start, end = time.fromisoformat(str(schedule["hora_inicio"])), time.fromisoformat(str(schedule["hora_fin"]))
        except (ValueError, KeyError) as error:
            raise ValueError("El horario tiene una hora inválida. Corrígela en el módulo de horarios.") from error
        if now.time() >= end:
            raise ValueError("La hora de esta clase ya pasó. No se puede registrar la asistencia.")
        if now.time() < start:
            raise ValueError(f"La entrada se habilita de {schedule['hora_inicio'][:5]} a {schedule['hora_fin'][:5]} (hora de Perú).")
        self.check_occupancy(client_id)
        return client, member, schedule

    def lookup(self, dni):
        client = self.gym.get_cliente_by_dni(dni)
        if not client:
            raise ValueError("No se encontró un cliente con ese DNI.")
        now = self.now()
        client_id = int(client["id_cliente"])
        member = self.membership(client_id, now.date().isoformat())
        schedules = []
        for enrollment in self.gym.attendance_enrollments():
            if int(enrollment.get("id_cliente") or 0) != client_id or enrollment.get("estado") != "ACTIVA":
                continue
            schedule = self.gym.get_horario_servicio(int(enrollment["id_horario_servicio"])) or {}
            record = self.existing(enrollment, now.date().isoformat())
            reason = ""
            try:
                self.entry_context(enrollment, now)
            except ValueError as error:
                reason = str(error)
            schedules.append({**schedule, "id_matricula": enrollment["id_matricula"],
                              "fecha_clase": enrollment_session(enrollment, schedule),
                              "hoy": enrollment_session(enrollment, schedule) == now.date().isoformat(),
                              "asistencia": self.present(record) if record else None,
                              "puede_entrar": not record and not reason,
                              "motivo": LATE_EXIT_MESSAGE if record and self.status(record) == "incompleta"
                              else "Asistencia de hoy completada." if record and record.get("hora_salida") else reason})
        schedules.sort(key=lambda s: (not s["hoy"], DAYS.index(s["dia"]) if s.get("dia") in DAYS else 7, s.get("hora_inicio", "")))
        open_record = next((r for r in self.gym.asistencia() if self.client_id(r) == client_id
                            and not r.get("anulado") and not r.get("hora_salida")), None)
        reason = ""
        try:
            self.general_context(client_id, now)
        except ValueError as error:
            reason = str(error)
        return {"cliente": {k: client.get(k) for k in ("id_cliente", "nombre", "dni", "plan", "estado")},
                "membresia": {k: member.get(k) for k in ("fecha_inicio", "fecha_fin", "estado", "estado_pago")} if member else None,
                "general": {"puede_entrar": not reason, "motivo": reason,
                            "asistencia_abierta": self.present(open_record) if open_record else None},
                "horarios": schedules, "fecha": now.date().isoformat(), "server_now": now.isoformat()}

    def general_retry(self, rows, client_id, request_id):
        return next((r for r in rows if self.client_id(r) == client_id and self.kind(r) == "general"
                     and any(e.get("request_id") == request_id for e in r.get("auditoria", []))), None)

    def schedules(self):
        now = self.now()
        schedules = [{**s, "hoy": s.get("dia") == DAYS[now.weekday()],
                      "matriculados": s.get("ocupacion_por_fecha", {}).get(next_session(s, now.date()), 0)}
                     for s in self.gym.horarios_servicio() if s.get("activo")]
        schedules.sort(key=lambda s: (not s["hoy"], DAYS.index(s["dia"]) if s.get("dia") in DAYS else 7,
                                      s.get("hora_inicio", ""), s["id_horario_servicio"]))
        return {"horarios": schedules, "fecha": now.date().isoformat(), "server_now": now.isoformat()}

    def roster(self, schedule_id, fecha=None):
        now = self.now()
        day = date.fromisoformat(str(fecha)).isoformat() if fecha else now.date().isoformat()
        schedule = self.gym.get_horario_servicio(schedule_id)
        if not schedule or not schedule.get("activo"):
            raise ValueError("El horario no está disponible.")
        students = []
        for enrollment in self.gym.attendance_enrollments():
            if enrollment.get("id_horario_servicio") != schedule_id or enrollment.get("estado") != "ACTIVA":
                continue
            if enrollment_session(enrollment, schedule) != day:
                continue
            client = self.gym.get_cliente(int(enrollment["id_cliente"])) or {}
            record = self.existing(enrollment, day)
            reason = ""
            if not record:
                if day != now.date().isoformat():
                    reason = "La entrada se habilita el día de esta sesión (hora de Perú)."
                else:
                    try:
                        self.entry_context(enrollment, now)
                    except ValueError as error:
                        reason = str(error)
            students.append({"id_matricula": enrollment["id_matricula"],
                "cliente": {k: client.get(k) for k in ("id_cliente", "nombre", "dni", "estado")},
                "asistencia": self.present(record, client=client) if record else None,
                "puede_entrar": not record and not reason, "motivo": reason})
        students.sort(key=lambda s: (str(s["cliente"].get("nombre") or "").casefold(), s["id_matricula"]))
        return {"horario": schedule, "clientes": students, "fecha": day, "server_now": now.isoformat()}

    @staticmethod
    def exit_deadline(schedule, day):
        return (datetime.combine(date.fromisoformat(day), time.fromisoformat(str(schedule["hora_fin"])), LIMA)
                + timedelta(hours=1)).isoformat()

    def enter_general(self, dni, request_id, actor):
        client = self.gym.get_cliente_by_dni(dni)
        if not client:
            raise ValueError("No se encontró un cliente con ese DNI.")
        client_id = int(client["id_cliente"])
        existing = self.general_retry(self.gym.asistencia(), client_id, request_id)
        if existing:
            return self.present(existing)
        now = self.now()
        client, member = self.general_context(client_id, now)
        row = {"id_cliente": client_id, "id_cliente_num": client_id, "id_membresia": member["id_membresia"],
               "id_matricula": None, "id_horario_servicio": None, "servicio": "gimnasio",
               "fecha": now.date().isoformat(), "hora": now.strftime("%H:%M:%S"),
               "hora_entrada": now.strftime("%H:%M:%S"), "hora_salida": "", "fecha_salida": None,
               "id_usuario_registra": actor.id_usuario or actor.id, "anulado": False}
        return self.save(row, None, "entrada", actor, request_id=request_id)

    def existing(self, enrollment, day):
        return next((r for r in self.gym.asistencia() if not r.get("anulado")
                     and self.client_id(r) == int(enrollment["id_cliente"])
                     and r.get("id_matricula") == enrollment["id_matricula"] and r.get("fecha") == day), None)

    def enter(self, payload, actor):
        now = self.now()
        enrollment_id = payload.get("id_matricula")
        if not enrollment_id:
            client_id = self.gym.resolve_attendance_client(payload)
            matches = [e for e in self.gym.attendance_enrollments()
                       if int(e.get("id_cliente") or 0) == client_id and e.get("estado") == "ACTIVA"
                       and (not payload.get("id_horario_servicio") or e["id_horario_servicio"] == payload["id_horario_servicio"])
                       and enrollment_session(e, self.gym.get_horario_servicio(e["id_horario_servicio"]) or {}) == now.date().isoformat()
                       and (self.gym.get_horario_servicio(e["id_horario_servicio"]) or {}).get("dia") == DAYS[now.weekday()]
                       and (not payload.get("servicio") or (self.gym.get_horario_servicio(e["id_horario_servicio"]) or {}).get("servicio") == payload["servicio"])]
            if len(matches) != 1:
                raise ValueError("Selecciona el horario matriculado para registrar la entrada.")
            enrollment_id = matches[0]["id_matricula"]
        enrollment = next((e for e in self.gym.attendance_enrollments() if e["id_matricula"] == enrollment_id), None)
        if not enrollment:
            raise ValueError("Matrícula no encontrada.")
        existing = self.existing(enrollment, now.date().isoformat())
        if existing:
            return self.present(existing)
        client, member, schedule = self.entry_context(enrollment, now)
        row = {"id_cliente": client["id_cliente"], "id_cliente_num": client["id_cliente"],
               "id_matricula": enrollment_id, "id_horario_servicio": schedule["id_horario_servicio"],
               "id_membresia": member["id_membresia"], "servicio": schedule["servicio"],
               "fecha": now.date().isoformat(), "hora": now.strftime("%H:%M:%S"),
               "hora_entrada": now.strftime("%H:%M:%S"), "hora_salida": "", "fecha_salida": None,
               "limite_salida": self.exit_deadline(schedule, now.date().isoformat()),
               "id_usuario_registra": actor.id_usuario or actor.id, "anulado": False}
        return self.save(row, None, "entrada", actor)

    def get(self, record_id):
        row = next((r for r in self.gym.asistencia() if r["id_asistencia"] == record_id), None)
        if not row:
            raise ValueError("Asistencia no encontrada.")
        return deepcopy(row)

    def exit(self, record_id, actor):
        row = self.get(record_id)
        if row.get("anulado"):
            raise ValueError("La asistencia está anulada.")
        if row.get("hora_salida"):
            return self.present(row)
        now = self.now()
        row.update(hora_salida=now.strftime("%H:%M:%S"), fecha_salida=now.date().isoformat())
        self.validate_times(row)
        return self.save(row, int(row.get("version") or 0), "salida", actor)

    def validate_times(self, row):
        try:
            entry = datetime.combine(date.fromisoformat(row["fecha"]), time.fromisoformat(row.get("hora_entrada") or row["hora"]), LIMA)
            end = datetime.combine(date.fromisoformat(row.get("fecha_salida") or row["fecha"]), time.fromisoformat(row["hora_salida"]), LIMA) if row.get("hora_salida") else None
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("Revisa la fecha y las horas del registro.") from error
        if entry > self.now() or (end and end > self.now()):
            raise ValueError("La asistencia no puede tener fechas u horas futuras.")
        if end and end < entry:
            raise ValueError("La salida no puede ser anterior a la entrada.")
        if row.get("fecha_salida") and not row.get("hora_salida"):
            raise ValueError("Indica también la hora de salida.")

    def correct(self, record_id, payload, actor, annul=False):
        row = self.get(record_id)
        if row.get("anulado"):
            raise ValueError("La asistencia ya está anulada.")
        expected = payload.pop("version")
        reason = payload.pop("motivo").strip()
        if len(reason) < 5:
            raise ValueError("Escribe un motivo de al menos 5 caracteres.")
        if annul:
            row["anulado"] = True
        else:
            row.update(payload)
            row["hora"] = row["hora_entrada"]
            self.validate_times(row)
            # Una corrección documentada permite reconstruir una visita histórica,
            # incluso si el horario o la membresía ya cambiaron después de ella.
        return self.save(row, expected, "anulacion" if annul else "correccion", actor, reason)

    def save(self, row, expected, operation, actor, reason="", request_id=None):
        audit = {"accion": operation, "fecha": self.now().isoformat(), "actor_id": actor.id_usuario or actor.id,
                 "actor_nombre": actor.name, "motivo": reason}
        if request_id:
            audit["request_id"] = request_id
        saved = self.gym.save_attendance(row, expected, audit)
        if saved is not None:
            return self.present(saved)

        return self.present(self.gym.apply_local_attendance(row, expected, audit, self.now()))
