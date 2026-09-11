"""Asistencia administrada, con reloj de Perú e historial propio para el cliente."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")
DAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


class AttendanceConflict(ValueError):
    pass


class AttendanceService:
    def __init__(self, gym, clock=None):
        self.gym = gym
        self.clock = clock or (lambda: datetime.now(LIMA))

    def now(self):
        return self.clock().astimezone(LIMA).replace(microsecond=0)

    def client_id(self, row):
        return self.gym._parse_cliente_id(row.get("id_cliente_num") or row.get("id_cliente"))

    @staticmethod
    def status(row):
        return "anulada" if row.get("anulado") else "completada" if row.get("hora_salida") else "dentro"

    def present(self, row, admin=True, client=None):
        if client is None:
            client = self.gym.get_cliente(self.client_id(row)) or {}
        result = {**deepcopy(row), "cliente_nombre": client.get("nombre", "Cliente"),
                  "cliente_dni": client.get("dni", ""), "estado": self.status(row),
                  "version": int(row.get("version") or 0)}
        if not admin:
            for key in ("auditoria", "id_usuario_registra"):
                result.pop(key, None)
        return result

    def records(self, user, desde=None, hasta=None, dni="", servicio="", estado=""):
        if desde and hasta and desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final.")
        admin = user.role == "admin"
        if not admin and not user.id_cliente:
            raise ValueError("No encontramos tu cliente vinculado.")
        rows = []
        with self.gym.lock:
            source = deepcopy(self.gym.state.get("asistencia", []))
            clients = {int(c["id_cliente"]): deepcopy(c) for c in self.gym.state.get("clientes", [])}
        for row in source:
            if not admin and (self.client_id(row) != user.id_cliente or row.get("anulado")):
                continue
            if desde and row.get("fecha", "") < str(desde):
                continue
            if hasta and row.get("fecha", "") > str(hasta):
                continue
            if servicio and row.get("servicio") != servicio:
                continue
            if estado and self.status(row) != estado:
                continue
            item = self.present(row, admin, clients.get(self.client_id(row), {}))
            if dni and item["cliente_dni"] != dni:
                continue
            rows.append(item)
        return sorted(rows, key=lambda r: (r.get("fecha", ""), r.get("hora_entrada") or r.get("hora", ""), r["id_asistencia"]), reverse=True)

    def summary(self, user):
        today = self.now().date().isoformat()
        rows = [r for r in self.records(user) if not r.get("anulado")]
        inside = [r for r in rows if not r.get("hora_salida")]
        return {"fecha": today, "server_now": self.now().isoformat(),
                "entradas": sum(r["fecha"] == today for r in rows),
                "salidas": sum(bool(r.get("hora_salida")) and (r.get("fecha_salida") or r["fecha"]) == today for r in rows),
                "dentro": len({self.client_id(r) for r in inside}), "pendientes": inside,
                "recientes": [r for r in rows if r["fecha"] == today][:8]}

    def membership(self, client_id, day):
        return next((m for m in self.gym.state.get("membresia", [])
                     if int(m.get("id_cliente") or 0) == client_id
                     and str(m.get("estado", "")).upper() in {"ACTIVA", "ACTIVO"}
                     and str(m.get("estado_pago", "")).upper() == "PAGADO"
                     and str(m.get("fecha_inicio", "")) <= day <= str(m.get("fecha_fin", ""))), None)

    def entry_context(self, enrollment, now):
        client_id = int(enrollment.get("id_cliente") or 0)
        client = self.gym.get_cliente(client_id)
        if not client or str(client.get("estado", "")).upper() != "ACTIVO":
            raise ValueError("La cuenta debe estar activada por el administrador.")
        member = self.membership(client_id, now.date().isoformat())
        if not member:
            raise ValueError("El cliente necesita una membresía activa, pagada y vigente.")
        if enrollment.get("estado") != "ACTIVA":
            raise ValueError("La matrícula no está activa.")
        schedule = self.gym.get_horario_servicio(int(enrollment.get("id_horario_servicio") or 0))
        if not schedule or not schedule.get("activo"):
            raise ValueError("El horario no está disponible.")
        if schedule.get("dia") != DAYS[now.weekday()]:
            raise ValueError("Este horario no corresponde a hoy.")
        start, end = time.fromisoformat(schedule["hora_inicio"]), time.fromisoformat(schedule["hora_fin"])
        if not start <= now.time() < end:
            raise ValueError(f"La entrada se habilita de {schedule['hora_inicio'][:5]} a {schedule['hora_fin'][:5]} (hora de Perú).")
        inside = [r for r in self.gym.state.get("asistencia", []) if not r.get("anulado") and not r.get("hora_salida")]
        if any(self.client_id(r) == client_id for r in inside):
            raise ValueError("El cliente tiene una entrada sin salida. Registra su salida primero.")
        capacity = int(self.gym.state.get("configuracion_gimnasio", {}).get("capacidad_total") or 30)
        if len({self.client_id(r) for r in inside}) >= capacity:
            raise ValueError("El gimnasio alcanzó su aforo. Registra una salida antes de otra entrada.")
        return client, member, schedule

    def lookup(self, dni):
        client = self.gym.get_cliente_by_dni(dni)
        if not client:
            raise ValueError("No se encontró un cliente con ese DNI.")
        now = self.now()
        client_id = int(client["id_cliente"])
        member = self.membership(client_id, now.date().isoformat())
        schedules = []
        for enrollment in self.gym.state.get("matriculas_horario", []):
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
                              "hoy": schedule.get("dia") == DAYS[now.weekday()],
                              "asistencia": self.present(record) if record else None,
                              "puede_entrar": not record and not reason,
                              "motivo": "Asistencia de hoy completada." if record and record.get("hora_salida") else reason})
        schedules.sort(key=lambda s: (not s["hoy"], DAYS.index(s["dia"]) if s.get("dia") in DAYS else 7, s.get("hora_inicio", "")))
        return {"cliente": {k: client.get(k) for k in ("id_cliente", "nombre", "dni", "plan", "estado")},
                "membresia": {k: member.get(k) for k in ("fecha_inicio", "fecha_fin", "estado", "estado_pago")} if member else None,
                "horarios": schedules, "fecha": now.date().isoformat(), "server_now": now.isoformat()}

    def existing(self, enrollment, day):
        return next((r for r in self.gym.state.get("asistencia", []) if not r.get("anulado")
                     and self.client_id(r) == int(enrollment["id_cliente"])
                     and r.get("id_matricula") == enrollment["id_matricula"] and r.get("fecha") == day), None)

    def enter(self, payload, actor):
        now = self.now()
        enrollment_id = payload.get("id_matricula")
        if not enrollment_id:
            client_id = self.gym._resolve_cliente_for_attendance(payload)
            matches = [e for e in self.gym.state.get("matriculas_horario", [])
                       if int(e.get("id_cliente") or 0) == client_id and e.get("estado") == "ACTIVA"
                       and (not payload.get("id_horario_servicio") or e["id_horario_servicio"] == payload["id_horario_servicio"])
                       and (self.gym.get_horario_servicio(e["id_horario_servicio"]) or {}).get("dia") == DAYS[now.weekday()]
                       and (not payload.get("servicio") or (self.gym.get_horario_servicio(e["id_horario_servicio"]) or {}).get("servicio") == payload["servicio"])]
            if len(matches) != 1:
                raise ValueError("Selecciona el horario matriculado para registrar la entrada.")
            enrollment_id = matches[0]["id_matricula"]
        enrollment = next((e for e in self.gym.state.get("matriculas_horario", []) if e["id_matricula"] == enrollment_id), None)
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
               "id_usuario_registra": actor.id_usuario or actor.id, "anulado": False}
        return self.save(row, None, "entrada", actor)

    def get(self, record_id):
        row = next((r for r in self.gym.state.get("asistencia", []) if r["id_asistencia"] == record_id), None)
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

    def save(self, row, expected, operation, actor, reason=""):
        audit = {"accion": operation, "fecha": self.now().isoformat(), "actor_id": actor.id_usuario or actor.id,
                 "actor_nombre": actor.name, "motivo": reason}
        if hasattr(self.gym, "save_attendance"):
            return self.present(self.gym.save_attendance(row, expected, audit))

        def change(state):
            rows = state.setdefault("asistencia", [])
            old = next((r for r in rows if r.get("id_asistencia") == row.get("id_asistencia")), None)
            if expected is None:
                duplicate = next((r for r in rows if not r.get("anulado") and self.client_id(r) == self.client_id(row)
                                  and r.get("id_matricula") == row.get("id_matricula") and r.get("fecha") == row["fecha"]), None)
                if duplicate:
                    return duplicate
                enrollment = next(e for e in state["matriculas_horario"] if e["id_matricula"] == row["id_matricula"])
                self.entry_context(enrollment, self.now())
                row["id_asistencia"] = max((r["id_asistencia"] for r in rows), default=0) + 1
            elif not old or int(old.get("version") or 0) != expected:
                if operation == "salida" and old and old.get("hora_salida") and not old.get("anulado"):
                    return old
                raise AttendanceConflict("El registro cambió. Actualiza el historial e inténtalo de nuevo.")
            if not row.get("anulado"):
                for other in rows:
                    if other.get("id_asistencia") == row.get("id_asistencia") or other.get("anulado") or self.client_id(other) != self.client_id(row):
                        continue
                    if (row.get("id_matricula") and other.get("id_matricula") == row["id_matricula"] and other["fecha"] == row["fecha"]) or (not row.get("hora_salida") and not other.get("hora_salida")):
                        raise AttendanceConflict("El cliente ya tiene una asistencia para ese horario y día, o una entrada sin salida.")
            fields = ("fecha", "hora_entrada", "hora_salida", "fecha_salida", "anulado")
            audit["antes"] = {k: old.get(k) for k in fields} if old else None
            audit["despues"] = {k: row.get(k) for k in fields}
            row["auditoria"] = [*(old or {}).get("auditoria", []), audit]
            row["version"] = int((old or {}).get("version") or 0) + 1
            if old:
                rows[rows.index(old)] = deepcopy(row)
            else:
                rows.insert(0, deepcopy(row))
            return row

        return self.present(self.gym._mutate(change))
