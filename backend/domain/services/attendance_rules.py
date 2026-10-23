"""Reglas de attendance sobre el agregado en memoria."""
from __future__ import annotations

import re
from typing import Any
from domain.services.gym_values import _now_time


class AttendanceRules:
    def asistencia(self) -> list[dict[str, Any]]:
        return self.state["asistencia"]

    def registrar_asistencia(self, id_cliente: int) -> dict[str, Any]:
        return self.registrar_asistencia_detallada({"id_cliente": id_cliente})

    def _parse_cliente_id(self, raw_id_cliente: Any) -> int:
        try:
            if isinstance(raw_id_cliente, str):
                s = raw_id_cliente.strip()
                m = re.match(r"^(?:SGCLI|cliente-)?(\d+)$", s, re.IGNORECASE)
                if m:
                    return int(m.group(1))
                if s.isdigit():
                    return int(s)
            return int(raw_id_cliente)
        except Exception:
            return 0

    def _attendance_hour_key(self, hora: str) -> str:
        value = str(hora or "").strip().lower()
        if not value:
            return "00"

        value = value.replace("a. m.", "am").replace("p. m.", "pm")
        value = value.replace("a.m.", "am").replace("p.m.", "pm")
        value = value.replace("a. m", "am").replace("p. m", "pm")
        match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", value)
        if not match:
            return value[:2]

        hour = int(match.group(1))
        suffix = match.group(3)
        if suffix == "pm" and hour < 12:
            hour += 12
        elif suffix == "am" and hour == 12:
            hour = 0

        return f"{hour % 24:02d}"

    def _validate_attendance_capacity(self, state: dict[str, Any], fecha: str, hora: str, exclude_id: int | None = None) -> None:
        cfg = state.get("configuracion_gimnasio", {}) or {}
        capacidad_total = max(1, int(cfg.get("capacidad_total") or 30))
        capacidad_por_hora = max(1, int(cfg.get("capacidad_por_hora") or 10))
        same_day = [a for a in state.get("asistencia", []) if str(a.get("fecha", "")) == fecha and int(a.get("id_asistencia", 0) or 0) != int(exclude_id or 0)]
        if len(same_day) >= capacidad_total:
            raise ValueError("El gimnasio alcanzó su capacidad total del día")
        hour_key = self._attendance_hour_key(hora)
        same_hour = [a for a in same_day if self._attendance_hour_key(str(a.get("hora", ""))) == hour_key]
        if len(same_hour) >= capacidad_por_hora:
            raise ValueError("El cupo de asistencias para esta hora está lleno")

    def registrar_asistencia_detallada(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_id_cliente = payload.get("id_cliente", 0)
        id_cliente = self._parse_cliente_id(raw_id_cliente)
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")

        servicio = str(payload.get("servicio") or "fitness").strip().lower()
        allowed = {"fitness", "musculacion", "cardio", "baile"}
        if servicio not in allowed:
            raise ValueError(f"Servicio inválido: {servicio}")

        fecha = str(payload.get("fecha") or "").strip() or self.today()
        hora = str(payload.get("hora") or "").strip() or _now_time()
        id_usuario_registra = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            membresia = self._active_membership_for_cliente(state, id_cliente)
            if not membresia:
                raise ValueError("Cliente sin membresía activa")
            self._validate_service_schedule(state, servicio, fecha, hora)
            self._validate_attendance_capacity(state, fecha, hora)
            client_record = self.get_cliente(id_cliente) or {}
            uid_value = str(client_record.get("id_usuario") or f"cliente-{id_cliente}")
            item = {
                "id_asistencia": self._next_int_id("asistencia", "id_asistencia"),
                "id_cliente": uid_value,
                "id_cliente_num": id_cliente,
                "fecha": fecha,
                "hora": hora,
                "servicio": servicio,
                "id_usuario_registra": id_usuario_registra,
                "id_membresia": membresia.get("id_membresia"),
            }
            state["asistencia"].insert(0, item)
            return item

        return self._change(_fn)

    def _resolve_cliente_for_attendance(self, payload: dict[str, Any]) -> int:
        if payload.get("dni"):
            cliente = self.get_cliente_by_dni(str(payload.get("dni")).strip())
            if not cliente:
                raise ValueError("Cliente no encontrado")
            return int(cliente["id_cliente"])
        return self._parse_cliente_id(payload.get("id_cliente"))

    def registrar_entrada_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_matricula = int(payload.get("id_matricula", 0) or 0)
        id_horario = int(payload.get("id_horario_servicio", 0) or 0)
        id_cliente = self._resolve_cliente_for_attendance(payload) if not id_matricula else 0
        fecha = str(payload.get("fecha") or "").strip() or self.today()
        hora_entrada = str(payload.get("hora_entrada") or "").strip() or _now_time()
        id_usuario_registra = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            enrollment = None
            if id_matricula:
                enrollment = next(
                    (
                        row
                        for row in state.get("matriculas_horario", [])
                        if int(row.get("id_matricula", 0) or 0) == id_matricula and str(row.get("estado") or "").upper() == "ACTIVA"
                    ),
                    None,
                )
            else:
                enrollment = next(
                    (
                        row
                        for row in state.get("matriculas_horario", [])
                        if int(row.get("id_cliente", 0) or 0) == id_cliente
                        and int(row.get("id_horario_servicio", 0) or 0) == id_horario
                        and str(row.get("estado") or "").upper() == "ACTIVA"
                    ),
                    None,
                )
            if not enrollment:
                raise ValueError("El cliente no tiene matricula activa en ese horario")

            resolved_cliente = int(enrollment.get("id_cliente", 0) or 0)
            membresia = self._active_membership_for_cliente(state, resolved_cliente)
            if not membresia:
                raise ValueError("Cliente sin membresia activa")

            schedule = next(
                (
                    row
                    for row in state.get("horarios_servicio", [])
                    if int(row.get("id_horario_servicio", 0) or 0) == int(enrollment.get("id_horario_servicio", 0) or 0)
                ),
                None,
            )
            if not schedule:
                raise ValueError("Horario no encontrado")
            existing = next(
                (
                    row
                    for row in state.get("asistencia", [])
                    if int(row.get("id_matricula", 0) or 0) == int(enrollment.get("id_matricula", 0) or 0)
                    and str(row.get("fecha") or "") == fecha
                ),
                None,
            )
            if existing:
                existing["hora_entrada"] = existing.get("hora_entrada") or hora_entrada
                existing["hora"] = existing.get("hora") or existing["hora_entrada"]
                return existing

            cliente = self.get_cliente(resolved_cliente) or {}
            item = {
                "id_asistencia": self._next_int_id("asistencia", "id_asistencia"),
                "id_cliente": str(cliente.get("id_usuario") or f"cliente-{resolved_cliente}"),
                "id_cliente_num": resolved_cliente,
                "fecha": fecha,
                "hora": hora_entrada,
                "hora_entrada": hora_entrada,
                "hora_salida": "",
                "servicio": str(schedule.get("servicio") or "fitness"),
                "id_usuario_registra": id_usuario_registra,
                "id_membresia": membresia.get("id_membresia"),
                "id_matricula": int(enrollment.get("id_matricula")),
                "id_horario_servicio": int(schedule.get("id_horario_servicio")),
            }
            state["asistencia"].insert(0, item)
            return item

        return self._change(_fn)

    def registrar_salida_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_asistencia = int(payload.get("id_asistencia", 0) or 0)
        hora_salida = str(payload.get("hora_salida") or "").strip() or _now_time()

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            asistencia = next((row for row in state.get("asistencia", []) if int(row.get("id_asistencia", 0) or 0) == id_asistencia), None)
            if not asistencia:
                raise ValueError("Asistencia no encontrada")
            if not asistencia.get("hora_entrada"):
                asistencia["hora_entrada"] = asistencia.get("hora") or _now_time()
            asistencia["hora_salida"] = hora_salida
            return asistencia

        return self._change(_fn)

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            idx = next((i for i, row in enumerate(state["asistencia"]) if int(row.get("id_asistencia", 0) or 0) == int(id_asistencia)), -1)
            if idx < 0:
                raise ValueError("Asistencia no encontrada")
            current = {**state["asistencia"][idx]}
            if payload.get("id_cliente") is not None:
                id_cliente = self._parse_cliente_id(payload.get("id_cliente"))
                if not self.get_cliente(id_cliente):
                    raise ValueError("Cliente no encontrado")
                cliente = self.get_cliente(id_cliente) or {}
                current["id_cliente"] = str(cliente.get("id_usuario") or f"cliente-{id_cliente}")
                current["id_cliente_num"] = id_cliente
            if payload.get("fecha"):
                current["fecha"] = str(payload.get("fecha")).strip()
            if payload.get("hora"):
                current["hora"] = str(payload.get("hora")).strip()
            if payload.get("servicio"):
                servicio = str(payload.get("servicio")).strip().lower()
                if servicio not in {"fitness", "musculacion", "cardio", "baile"}:
                    raise ValueError(f"Servicio inválido: {servicio}")
                current["servicio"] = servicio
            if payload.get("id_usuario"):
                current["id_usuario_registra"] = self._normalize_usuario_id(payload.get("id_usuario"))
            self._validate_service_schedule(state, current.get("servicio", "fitness"), current.get("fecha", self.today()), current.get("hora", _now_time()))
            self._validate_attendance_capacity(state, current.get("fecha", self.today()), current.get("hora", _now_time()), exclude_id=id_asistencia)
            state["asistencia"][idx] = current
            return current

        return self._change(_fn)

    def eliminar_asistencia(self, id_asistencia: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            original = len(state["asistencia"])
            state["asistencia"] = [a for a in state["asistencia"] if int(a.get("id_asistencia", 0) or 0) != int(id_asistencia)]
            if len(state["asistencia"]) == original:
                raise ValueError("Asistencia no encontrada")

        self._change(_fn)

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
        payload: dict[str, Any]
        if isinstance(dni, dict):
            payload = dni
            dni_val = str(payload.get("dni") or "").strip()
        else:
            payload = {"dni": str(dni)}
            dni_val = str(dni)

        cliente = self.get_cliente_by_dni(dni_val)
        if not cliente:
            raise ValueError("DNI no registrado")
        payload["id_cliente"] = int(cliente["id_cliente"])
        return self.registrar_asistencia_detallada(payload)
