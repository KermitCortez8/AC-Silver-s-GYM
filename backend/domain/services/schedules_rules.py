"""Reglas de schedules sobre el agregado en memoria."""
from __future__ import annotations
from domain.validation import validate_exercises
from domain.errors import EntityNotFound, MembershipRequired, EnrollmentConflict

import re
from datetime import datetime
from typing import Any


class SchedulesRules:
    def _time_to_minutes(self, hora: str) -> int:
        value = str(hora or "").strip().lower()
        value = value.replace("a. m.", "am").replace("p. m.", "pm")
        value = value.replace("a.m.", "am").replace("p.m.", "pm")
        value = value.replace("a. m", "am").replace("p. m", "pm")
        match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", value)
        if not match:
            raise ValueError("Hora invalida")

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        suffix = match.group(3)
        if suffix == "pm" and hour < 12:
            hour += 12
        elif suffix == "am" and hour == 12:
            hour = 0
        if hour > 23 or minute > 59:
            raise ValueError("Hora invalida")
        return hour * 60 + minute

    def _date_day_name(self, fecha: str) -> str:
        names = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        try:
            return names[datetime.fromisoformat(str(fecha)).weekday()]
        except Exception:
            return ""

    def _normalize_day(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        return (
            normalized.replace("miércoles", "miercoles")
            .replace("sábado", "sabado")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )

    def _day_code(self, day: str) -> str:
        return {
            "lunes": "LUN",
            "martes": "MAR",
            "miercoles": "MIE",
            "jueves": "JUE",
            "viernes": "VIE",
            "sabado": "SAB",
            "domingo": "DOM",
        }.get(self._normalize_day(day), str(day or "DIA")[:3].upper())

    def _validate_short_service_schedule_range(self, hora_inicio: str, hora_fin: str) -> tuple[int, int]:
        start = self._time_to_minutes(hora_inicio)
        end = self._time_to_minutes(hora_fin)
        duration = end - start
        if duration not in {60, 120}:
            raise ValueError("Los horarios disponibles deben durar 1 o 2 horas")
        return start, end

    def _minutes_to_time(self, value: int) -> str:
        safe_value = max(0, min(23 * 60 + 59, int(value)))
        return f"{safe_value // 60:02d}:{safe_value % 60:02d}"

    def _short_service_schedule_range(self, hora_inicio: Any, hora_fin: Any) -> tuple[str, str]:
        start_value = str(hora_inicio or "06:00").strip()
        end_value = str(hora_fin or "07:00").strip()
        try:
            self._validate_short_service_schedule_range(start_value, end_value)
            return start_value, end_value
        except ValueError:
            start = self._time_to_minutes(start_value)
            return start_value, self._minutes_to_time(start + 120)

    def _normalize_horarios_servicio(self, rows: Any) -> list[dict[str, Any]]:
        allowed = {"fitness", "musculacion", "cardio", "baile"}
        normalized: list[dict[str, Any]] = []
        used_ids: set[int] = set()

        # Procesa esta operación.
        def next_id() -> int:
            current = 1
            while current in used_ids:
                current += 1
            used_ids.add(current)
            return current

        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            servicio = str(row.get("servicio") or "").strip().lower()
            if servicio not in allowed:
                continue

            raw_id = int(row.get("id_horario_servicio", 0) or 0)
            if raw_id <= 0 or raw_id in used_ids:
                raw_id = next_id()
            else:
                used_ids.add(raw_id)

            days = [self._normalize_day(day) for day in row.get("dias", []) if self._normalize_day(day)]
            if not days:
                days = [self._normalize_day(row.get("dia")) or "lunes"]

            for index, day in enumerate(days):
                item_id = raw_id if index == 0 else next_id()
                cupos = max(1, int(row.get("cupos") or row.get("capacidad") or row.get("capacidad_maxima") or 10))
                hora_inicio, hora_fin = self._short_service_schedule_range(row.get("hora_inicio"), row.get("hora_fin"))
                normalized.append(
                    {
                        "id_horario_servicio": item_id,
                        "servicio": servicio,
                        "id_rutina": int(row.get("id_rutina", 0) or 0),
                        "codigo_dia": str(row.get("codigo_dia") or self._day_code(day)).strip().upper(),
                        "dia": day,
                        "hora_inicio": hora_inicio,
                        "hora_fin": hora_fin,
                        "cupos": cupos,
                        "cupos_usados": max(0, int(row.get("cupos_usados") or 0)),
                        "activo": bool(row.get("activo", True)),
                    }
                )

        return sorted(normalized, key=lambda row: (str(row.get("dia")), str(row.get("hora_inicio")), str(row.get("servicio"))))

    def _normalize_matricula_horario(self, row: dict[str, Any], fallback_index: int) -> dict[str, Any]:
        return {
            "id_matricula": int(row.get("id_matricula", 0) or fallback_index),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0) or None,
            "fecha_matricula": str(row.get("fecha_matricula") or self.today()),
            "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
        }

    def _normalize_rutina_progreso(self, row: dict[str, Any], fallback_index: int) -> dict[str, Any]:
        ejercicios_detalle = row.get("ejercicios_detalle")
        if not isinstance(ejercicios_detalle, list):
            ejercicios_detalle = []
        return {
            "id_progreso": int(row.get("id_progreso", 0) or fallback_index),
            "id_matricula": int(row.get("id_matricula", 0) or 0),
            "id_rutina": int(row.get("id_rutina", 0) or 0),
            "fecha": str(row.get("fecha") or self.today())[:10],
            "estado": str(row.get("estado") or "REALIZADO").strip().upper(),
            "observacion": str(row.get("observacion") or "").strip(),
            "id_usuario": self._normalize_usuario_id(row.get("id_usuario")) if row.get("id_usuario") else None,
            "ejercicios_detalle": ejercicios_detalle,
        }

    def _recount_schedule_cupos(self, state: dict[str, Any]) -> None:
        counts: dict[int, int] = {}
        for enrollment in state.get("matriculas_horario", []):
            if str(enrollment.get("estado") or "").upper() != "ACTIVA":
                continue
            schedule_id = int(enrollment.get("id_horario_servicio", 0) or 0)
            counts[schedule_id] = counts.get(schedule_id, 0) + 1

        for schedule in state.get("horarios_servicio", []):
            schedule_id = int(schedule.get("id_horario_servicio", 0) or 0)
            schedule["cupos_usados"] = counts.get(schedule_id, 0)

    def _validate_service_schedule(self, state: dict[str, Any], servicio: str, fecha: str, hora: str) -> None:
        servicio = str(servicio or "fitness").strip().lower()
        schedules = [row for row in state.get("horarios_servicio", []) if row.get("servicio") == servicio and bool(row.get("activo", True))]
        if not schedules:
            return

        day_name = self._date_day_name(fecha)
        day_schedules = [row for row in schedules if self._normalize_day(row.get("dia")) == day_name]
        if day_name and not day_schedules:
            raise ValueError(f"El servicio {servicio} no permite registros los {day_name}")

        current = self._time_to_minutes(hora)
        for schedule in day_schedules or schedules:
            start = self._time_to_minutes(schedule.get("hora_inicio", "00:00"))
            end = self._time_to_minutes(schedule.get("hora_fin", "23:59"))
            in_range = start <= current <= end if start <= end else current >= start or current <= end
            if in_range:
                return

        ranges = ", ".join(f"{row.get('hora_inicio')}-{row.get('hora_fin')}" for row in day_schedules or schedules)
        raise ValueError(f"El servicio {servicio} solo registra en estos horarios: {ranges}")

    def tickets(self) -> list[dict[str, Any]]:
        return self.state["tickets_atencion"]

    def upsert_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_usuario = self._normalize_usuario_id(payload.get("id_usuario"))
        if not self.get_cliente(id_cliente):
            raise EntityNotFound("Cliente no encontrado")
        if not self.get_usuario(id_usuario):
            raise EntityNotFound("Usuario no encontrado")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_ticket")
            if item_id is None:
                item_id = self._next_int_id("tickets_atencion", "id_ticket")
            item["id_ticket"] = int(item_id)
            item["id_usuario"] = id_usuario
            item["fecha_emitido"] = self.safe_date(item.get("fecha_emitido", ""))
            idx = next((i for i, row in enumerate(state["tickets_atencion"]) if int(row.get("id_ticket", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["tickets_atencion"][idx] = item
            else:
                state["tickets_atencion"].insert(0, item)
            return item

        return self._change(_fn)

    def catalogo_rutina(self) -> list[dict[str, Any]]:
        return self.state["catalogo_rutina"]

    def upsert_rutina(self, payload: dict[str, Any]) -> dict[str, Any]:
        validate_exercises(payload.get("ejercicios"))
        servicio = str(payload.get("servicio") or "fitness").strip().lower()
        if servicio not in {"fitness", "musculacion", "cardio", "baile"}:
            raise ValueError("Servicio invalido para rutina")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_rutina")
            if item_id is None:
                item_id = self._next_int_id("catalogo_rutina", "id_rutina")
            item["id_rutina"] = int(item_id)
            item["servicio"] = servicio
            item["nombre_rutina"] = str(item.get("nombre_rutina") or "").strip()
            item["zonas_musculares"] = str(item.get("zonas_musculares") or "").strip()
            item["color"] = str(item.get("color") or "Azul").strip() or "Azul"
            raw_ejercicios = item.get("ejercicios")
            if isinstance(raw_ejercicios, list):
                item["ejercicios"] = raw_ejercicios
            else:
                item["ejercicios"] = []
            idx = next((i for i, row in enumerate(state["catalogo_rutina"]) if int(row.get("id_rutina", 0)) == int(item_id)), -1)

            if idx >= 0:
                state["catalogo_rutina"][idx] = item
            else:
                state["catalogo_rutina"].insert(0, item)
            return item

        return self._change(_fn)

    def horarios(self) -> list[dict[str, Any]]:
        return self.state["horario"]

    def upsert_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_rutina = int(payload.get("id_rutina", 0))
        if not self.get_cliente(id_cliente):
            raise EntityNotFound("Cliente no encontrado")
        if not next((r for r in self.state["catalogo_rutina"] if int(r.get("id_rutina", 0)) == id_rutina), None):
            raise EntityNotFound("Rutina no encontrada")

        dia = str(payload.get("dia_semana") or "Lunes").strip()
        hora_inicio = str(payload.get("hora_inicio") or "06:00").strip()
        hora_fin = str(payload.get("hora_fin") or "07:00").strip()
        capacidad_maxima = max(1, int(payload.get("capacidad_maxima") or 1))

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_horario")
            if item_id is None:
                item_id = self._next_int_id("horario", "id_horario")
            item_id = int(item_id)

            same_slot = [
                row for row in state["horario"]
                if int(row.get("id_horario", 0) or 0) != item_id
                and str(row.get("dia_semana", "")).strip().lower() == dia.lower()
                and str(row.get("hora_inicio", "")).strip() == hora_inicio
                and str(row.get("hora_fin", "")).strip() == hora_fin
            ]
            if any(int(row.get("id_cliente", 0) or 0) == id_cliente for row in same_slot):
                raise ValueError("El cliente ya tiene asignado ese horario")
            if len(same_slot) >= capacidad_maxima:
                raise ValueError("El horario seleccionado ya está lleno")

            item["id_horario"] = item_id
            item["id_cliente"] = id_cliente
            item["id_rutina"] = id_rutina
            item["dia_semana"] = dia
            item["hora_inicio"] = hora_inicio
            item["hora_fin"] = hora_fin
            item["capacidad_maxima"] = capacidad_maxima
            item["cupos_usados"] = len(same_slot) + 1
            idx = next((i for i, row in enumerate(state["horario"]) if int(row.get("id_horario", 0)) == item_id), -1)
            if idx >= 0:
                state["horario"][idx] = item
            else:
                state["horario"].insert(0, item)
            return item

        return self._change(_fn)

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return self.state.get("configuracion_gimnasio", {"capacidad_total": 30, "capacidad_por_hora": 10})

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            cfg = state.setdefault("configuracion_gimnasio", {})
            cfg["capacidad_total"] = max(1, int(payload.get("capacidad_total", cfg.get("capacidad_total", 30))))
            cfg["capacidad_por_hora"] = max(1, int(payload.get("capacidad_por_hora", cfg.get("capacidad_por_hora", 10))))
            return cfg

        return self._change(_fn)

    def horarios_servicio(self, solo_activos: bool = False) -> list[dict[str, Any]]:
        self._recount_schedule_cupos(self.state)
        routines_by_id = {
            int(routine.get("id_rutina", 0) or 0): routine
            for routine in self.state.get("catalogo_rutina", [])
        }
        result = []
        for schedule in self.state.get("horarios_servicio", []):
            if solo_activos and not bool(schedule.get("activo", True)):
                continue
            routine = routines_by_id.get(int(schedule.get("id_rutina", 0) or 0), {})
            cupos = max(1, int(schedule.get("cupos", 1) or 1))
            cupos_usados = max(0, int(schedule.get("cupos_usados", 0) or 0))
            cupos_disponibles = max(0, cupos - cupos_usados)
            result.append(
                {
                    **schedule,
                    "cupos": cupos,
                    "cupos_usados": cupos_usados,
                    "cupos_disponibles": cupos_disponibles,
                    "esta_lleno": cupos_disponibles == 0,
                    "rutina_nombre": routine.get("nombre_rutina", ""),
                    "zonas_musculares": routine.get("zonas_musculares", ""),
                    "rutina_color": routine.get("color", "Azul"),
                    "entrenador": str(schedule.get("entrenador") or routine.get("entrenador") or "").strip(),
                }
            )
        return result

    def get_horario_servicio(self, id_horario_servicio: int) -> dict[str, Any] | None:
        return next(
            (
                schedule
                for schedule in self.state.get("horarios_servicio", [])
                if int(schedule.get("id_horario_servicio", 0) or 0) == int(id_horario_servicio)
            ),
            None,
        )

    def upsert_horario_servicio(self, payload: dict[str, Any]) -> dict[str, Any]:
        servicio = str(payload.get("servicio") or "").strip().lower()
        if servicio not in {"fitness", "musculacion", "cardio", "baile"}:
            raise ValueError("Servicio invalido")

        hora_inicio = str(payload.get("hora_inicio") or "").strip()
        hora_fin = str(payload.get("hora_fin") or "").strip()
        self._validate_short_service_schedule_range(hora_inicio, hora_fin)
        dia = self._normalize_day(payload.get("dia") or (payload.get("dias") or [""])[0])
        if not dia:
            raise ValueError("Selecciona un dia")
        id_rutina = int(payload.get("id_rutina", 0) or 0)
        routine = next((r for r in self.state["catalogo_rutina"] if int(r.get("id_rutina", 0) or 0) == id_rutina), None)
        if not routine:
            raise ValueError("Selecciona una rutina valida para el servicio")
        routine_service = str(routine.get("servicio") or servicio).strip().lower()
        if routine_service != servicio:
            raise ValueError("La rutina seleccionada no corresponde al servicio")

        item = {
            "id_horario_servicio": int(payload.get("id_horario_servicio", 0) or 0),
            "servicio": servicio,
            "id_rutina": id_rutina,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "codigo_dia": str(payload.get("codigo_dia") or self._day_code(dia)).strip().upper(),
            "dia": dia,
            "cupos": max(1, int(payload.get("cupos") or 10)),
            "cupos_usados": 0,
            "activo": bool(payload.get("activo", True)),
        }

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            state["horarios_servicio"] = self._normalize_horarios_servicio(state.get("horarios_servicio", []))
            if item["id_horario_servicio"] <= 0:
                item["id_horario_servicio"] = self._next_int_id_in_state(state, "horarios_servicio", "id_horario_servicio")
            idx = next(
                (
                    i
                    for i, row in enumerate(state["horarios_servicio"])
                    if int(row.get("id_horario_servicio", 0) or 0) == int(item["id_horario_servicio"])
                ),
                -1,
            )
            current_used = int(state["horarios_servicio"][idx].get("cupos_usados", 0) or 0) if idx >= 0 else 0
            if current_used > item["cupos"]:
                raise ValueError("No puedes reducir cupos por debajo de los matriculados")
            item["cupos_usados"] = current_used
            if idx >= 0:
                state["horarios_servicio"][idx] = item
            else:
                state["horarios_servicio"].append(item)
            self._recount_schedule_cupos(state)
            return item

        return self._change(_fn)

    def delete_horario_servicio(self, id_horario_servicio: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            schedule_id = int(id_horario_servicio)
            if any(
                int(row.get("id_horario_servicio", 0) or 0) == schedule_id and str(row.get("estado") or "").upper() == "ACTIVA"
                for row in state.get("matriculas_horario", [])
            ):
                raise ValueError("No puedes eliminar un horario con matriculas activas")
            original = len(state.get("horarios_servicio", []))
            state["horarios_servicio"] = [
                row for row in state.get("horarios_servicio", []) if int(row.get("id_horario_servicio", 0) or 0) != schedule_id
            ]
            if len(state["horarios_servicio"]) == original:
                raise EntityNotFound("Horario no encontrado")

        self._change(_fn)

    def matriculas_horario(
        self,
        id_cliente: int | None = None,
        dni: str | None = None,
        solo_activas: bool = False,
    ) -> list[dict[str, Any]]:
        resolved_id = int(id_cliente or 0)
        if dni:
            cliente = self.get_cliente_by_dni(str(dni).strip())
            if not cliente:
                raise EntityNotFound("Cliente no encontrado")
            resolved_id = int(cliente["id_cliente"])

        result = []
        for enrollment in self.state.get("matriculas_horario", []):
            if resolved_id and int(enrollment.get("id_cliente", 0) or 0) != resolved_id:
                continue
            if solo_activas and str(enrollment.get("estado") or "").upper() != "ACTIVA":
                continue
            schedule = self.get_horario_servicio(int(enrollment.get("id_horario_servicio", 0) or 0)) or {}
            effective_routine_id = int(enrollment.get("id_rutina", 0) or 0) or int(schedule.get("id_rutina", 0) or 0)
            routine = next(
                (
                    r
                    for r in self.state.get("catalogo_rutina", [])
                    if int(r.get("id_rutina", 0) or 0) == effective_routine_id
                ),
                {},
            )
            cliente = self.get_cliente(int(enrollment.get("id_cliente", 0) or 0)) or {}
            result.append(
                {
                    **enrollment,
                    "cliente_nombre": cliente.get("nombre", ""),
                    "cliente_dni": cliente.get("dni", ""),
                    "cliente_codigo": cliente.get("id_usuario", ""),
                    "servicio": schedule.get("servicio", ""),
                    "id_rutina": effective_routine_id or None,
                    "rutina_origen": "cliente" if int(enrollment.get("id_rutina", 0) or 0) else "servicio",
                    "rutina_nombre": routine.get("nombre_rutina", ""),
                    "zonas_musculares": routine.get("zonas_musculares", ""),
                    "rutina_color": routine.get("color", "Azul"),
                    "codigo_dia": schedule.get("codigo_dia", ""),
                    "dia": schedule.get("dia", ""),
                    "hora_inicio": schedule.get("hora_inicio", ""),
                    "hora_fin": schedule.get("hora_fin", ""),
                    "asistencias": [
                        asistencia
                        for asistencia in self.state.get("asistencia", [])
                        if int(asistencia.get("id_matricula", 0) or 0) == int(enrollment.get("id_matricula", 0) or 0)
                        and self._parse_cliente_id(asistencia.get("id_cliente_num") or asistencia.get("id_cliente")) == int(enrollment.get("id_cliente", 0) or 0)
                        and not asistencia.get("anulado")
                    ],
                }
            )
        return sorted(result, key=lambda row: (str(row.get("dia")), str(row.get("hora_inicio"))))

    def get_matricula_horario(self, id_matricula: int) -> dict[str, Any] | None:
        return next(
            (
                enrollment
                for enrollment in self.state.get("matriculas_horario", [])
                if int(enrollment.get("id_matricula", 0) or 0) == int(id_matricula)
            ),
            None,
        )

    def asignar_rutina_matricula(self, id_matricula: int, id_rutina: int) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            idx = next(
                (
                    i
                    for i, row in enumerate(state.get("matriculas_horario", []))
                    if int(row.get("id_matricula", 0) or 0) == int(id_matricula)
                ),
                -1,
            )
            if idx < 0:
                raise EntityNotFound("Matricula no encontrada")

            enrollment = state["matriculas_horario"][idx]
            if str(enrollment.get("estado") or "").strip().upper() != "ACTIVA":
                raise ValueError("Solo se puede asignar una rutina a una matricula ACTIVA")

            schedule = next(
                (
                    row
                    for row in state.get("horarios_servicio", [])
                    if int(row.get("id_horario_servicio", 0) or 0) == int(enrollment.get("id_horario_servicio", 0) or 0)
                ),
                None,
            )
            if not schedule:
                raise EntityNotFound("Horario no encontrado")
            if not schedule.get("activo", False):
                raise ValueError("El horario de la matricula no esta activo")

            routine = next(
                (
                    row
                    for row in state.get("catalogo_rutina", [])
                    if int(row.get("id_rutina", 0) or 0) == int(id_rutina)
                ),
                None,
            )
            if not routine:
                raise EntityNotFound("Rutina no encontrada")
            if str(routine.get("servicio") or "").strip().lower() != str(schedule.get("servicio") or "").strip().lower():
                raise ValueError("La rutina no corresponde al servicio del cliente")

            state["matriculas_horario"][idx]["id_rutina"] = int(id_rutina)
            updated = next(
                (
                    row
                    for row in self.matriculas_horario(id_cliente=int(enrollment.get("id_cliente", 0) or 0))
                    if int(row.get("id_matricula", 0) or 0) == int(id_matricula)
                ),
                None,
            )
            return updated or state["matriculas_horario"][idx]

        return self._change(_fn)

    def trainer_rutinas_cliente(self, dni: str) -> dict[str, Any]:
        cliente = self.get_cliente_by_dni(str(dni or "").strip())
        if not cliente:
            raise EntityNotFound("Cliente no encontrado")
        enrollments = [
            row
            for row in self.matriculas_horario(id_cliente=int(cliente.get("id_cliente", 0) or 0))
            if str(row.get("estado") or "").strip().upper() == "ACTIVA"
        ]
        progress_by_enrollment: dict[int, list[dict[str, Any]]] = {}
        for row in self.state.get("rutina_progreso", []):
            progress_by_enrollment.setdefault(int(row.get("id_matricula", 0) or 0), []).append(row)

        return {
            "cliente": {
                "id_cliente": cliente.get("id_cliente"),
                "id_usuario": cliente.get("id_usuario"),
                "nombre": cliente.get("nombre"),
                "dni": cliente.get("dni"),
            },
            "matriculas": [
                {
                    **row,
                    "progreso": sorted(
                        progress_by_enrollment.get(int(row.get("id_matricula", 0) or 0), []),
                        key=lambda item: str(item.get("fecha") or ""),
                        reverse=True,
                    )[:10],
                }
                for row in enrollments
            ],
        }

    def registrar_progreso_rutina(self, id_matricula: int, payload: dict[str, Any]) -> dict[str, Any]:
        validate_exercises(payload.get("ejercicios_detalle"))
        fecha = str(payload.get("fecha") or self.today())[:10]
        observacion = str(payload.get("observacion") or "").strip()
        id_usuario = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            enrollment = next(
                (
                    row
                    for row in state.get("matriculas_horario", [])
                    if int(row.get("id_matricula", 0) or 0) == int(id_matricula)
                ),
                None,
            )
            if not enrollment:
                raise EntityNotFound("Matricula no encontrada")
            detail = next(
                (
                    row
                    for row in self.matriculas_horario(id_cliente=int(enrollment.get("id_cliente", 0) or 0))
                    if int(row.get("id_matricula", 0) or 0) == int(id_matricula)
                ),
                {},
            )
            id_rutina = int(detail.get("id_rutina", 0) or 0)
            if not id_rutina:
                raise ValueError("La matricula no tiene rutina asignada")

            existing_idx = next(
                (
                    i
                    for i, row in enumerate(state.setdefault("rutina_progreso", []))
                    if int(row.get("id_matricula", 0) or 0) == int(id_matricula)
                    and str(row.get("fecha") or "")[:10] == fecha
                ),
                -1,
            )
            ejercicios_detalle = payload.get("ejercicios_detalle")
            if not isinstance(ejercicios_detalle, list):
                ejercicios_detalle = []
            item = {
                "id_progreso": int(state["rutina_progreso"][existing_idx].get("id_progreso", 0) or 0) if existing_idx >= 0 else self._next_int_id_in_state(state, "rutina_progreso", "id_progreso"),
                "id_matricula": int(id_matricula),
                "id_rutina": id_rutina,
                "fecha": fecha,
                "estado": str(payload.get("estado") or "REALIZADO").strip().upper(),
                "observacion": observacion,
                "id_usuario": id_usuario,
                "ejercicios_detalle": ejercicios_detalle,
            }

            if existing_idx >= 0:
                state["rutina_progreso"][existing_idx] = item
            else:
                state["rutina_progreso"].insert(0, item)
            return item

        return self._change(_fn)

    def trainer_overview(self) -> dict[str, Any]:
        active_enrollments = [
            row
            for row in self.matriculas_horario()
            if str(row.get("estado") or "").upper() != "CANCELADA"
        ]
        routines_by_id = {
            int(routine.get("id_rutina", 0) or 0): routine
            for routine in self.state.get("catalogo_rutina", [])
        }

        routine_supervision = []
        for enrollment in active_enrollments:
            routine = routines_by_id.get(int(enrollment.get("id_rutina", 0) or 0), {})
            attendance_rows = [
                item
                for item in self.state.get("asistencia", [])
                if int(item.get("id_matricula", 0) or 0) == int(enrollment.get("id_matricula", 0) or 0)
                and self._parse_cliente_id(item.get("id_cliente_num") or item.get("id_cliente")) == int(enrollment.get("id_cliente", 0) or 0)
                and not item.get("anulado")
            ]
            routine_supervision.append(
                {
                    **enrollment,
                    "rutina_nombre": routine.get("nombre_rutina", ""),
                    "zonas_musculares": routine.get("zonas_musculares", ""),
                    "color": routine.get("color", "Azul"),
                    "asistencias": attendance_rows[:10],
                }
            )

        routines_summary = []
        for routine in self.state.get("catalogo_rutina", []):
            routine_id = int(routine.get("id_rutina", 0) or 0)
            assigned = [
                row
                for row in self.state.get("horarios_servicio", [])
                if int(row.get("id_rutina", 0) or 0) == routine_id
            ]
            routine_enrollments = [
                row
                for row in active_enrollments
                if int(row.get("id_rutina", 0) or 0) == routine_id
            ]
            routines_summary.append(
                {
                    **routine,
                    "clientes_asignados": len({int(row.get("id_cliente", 0) or 0) for row in routine_enrollments if int(row.get("id_cliente", 0) or 0)}),
                    "horarios_asignados": len(assigned),
                }
            )

        return {
            "stats": {
                "clientes_en_horario": len({int(row.get("id_cliente", 0) or 0) for row in active_enrollments if int(row.get("id_cliente", 0) or 0)}),
                "matriculas_activas": len(active_enrollments),
                "rutinas": len(self.state.get("catalogo_rutina", [])),
                "rutinas_asignadas": len([row for row in self.state.get("horarios_servicio", []) if int(row.get("id_rutina", 0) or 0)]),
            },
            "schedule_monitor": active_enrollments,
            "routine_supervision": routine_supervision,
            "routines": routines_summary,
        }

    def _validate_new_schedule_enrollment(
        self,
        state: dict[str, Any],
        id_cliente: int,
        id_horario: int,
    ) -> None:
        cliente = next(
            (
                row
                for row in state.get("clientes", [])
                if int(row.get("id_cliente", 0) or 0) == id_cliente
            ),
            None,
        )
        if not cliente:
            raise EntityNotFound("Cliente no encontrado")
        if not self._active_membership_for_cliente(state, id_cliente):
            raise MembershipRequired("Cliente sin membresia activa")

        schedule = next(
            (
                row
                for row in state.get("horarios_servicio", [])
                if int(row.get("id_horario_servicio", 0) or 0) == id_horario
            ),
            None,
        )
        if not schedule or not bool(schedule.get("activo", True)):
            raise ValueError("Horario no disponible")

        active_enrollments = [
            row
            for row in state.get("matriculas_horario", [])
            if str(row.get("estado") or "").upper() == "ACTIVA"
        ]
        if any(
            int(row.get("id_cliente", 0) or 0) == id_cliente
            and int(row.get("id_horario_servicio", 0) or 0) == id_horario
            for row in active_enrollments
        ):
            raise EnrollmentConflict("El cliente ya esta matriculado en este horario")

        used = sum(
            1
            for row in active_enrollments
            if int(row.get("id_horario_servicio", 0) or 0) == id_horario
        )
        if used >= int(schedule.get("cupos", 1) or 1):
            raise EnrollmentConflict("Horario sin cupos disponibles")

    def matricular_cliente_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("dni"):
            cliente = self.get_cliente_by_dni(str(payload.get("dni")).strip())
            if not cliente:
                raise EntityNotFound("Cliente no encontrado")
            id_cliente = int(cliente["id_cliente"])
        else:
            id_cliente = self._parse_cliente_id(payload.get("id_cliente"))

        id_horario = int(payload.get("id_horario_servicio", 0) or 0)

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            self._validate_new_schedule_enrollment(state, id_cliente, id_horario)
            enrollment = {
                "id_matricula": self._next_int_id_in_state(state, "matriculas_horario", "id_matricula"),
                "id_cliente": id_cliente,
                "id_horario_servicio": id_horario,
                "fecha_matricula": self.today(),
                "estado": "ACTIVA",
            }
            state.setdefault("matriculas_horario", []).insert(0, enrollment)
            self._recount_schedule_cupos(state)
            return next(
                row
                for row in self.matriculas_horario(id_cliente=id_cliente, solo_activas=True)
                if int(row.get("id_matricula", 0) or 0) == int(enrollment["id_matricula"])
            )

        return self._change(_fn)

    def cancelar_matricula_horario(self, id_matricula: int, id_cliente: int | None = None) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            idx = next((i for i, row in enumerate(state.get("matriculas_horario", [])) if int(row.get("id_matricula", 0) or 0) == int(id_matricula)), -1)
            if idx < 0:
                raise EntityNotFound("Matricula no encontrada")
            if id_cliente and int(state["matriculas_horario"][idx].get("id_cliente", 0) or 0) != int(id_cliente):
                raise PermissionError("No puedes cancelar la matricula de otro cliente")
            state["matriculas_horario"][idx]["estado"] = "CANCELADA"
            self._recount_schedule_cupos(state)

        self._change(_fn)
