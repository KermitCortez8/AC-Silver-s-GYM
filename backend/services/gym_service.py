from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_time() -> str:
    return datetime.now().strftime("%H:%M")


def _safe_date(value: str) -> str:
    if value:
        return value
    return _today_iso()


class GymService:
    def __init__(self, db_file: Path) -> None:
        self.db_file = db_file
        self.lock = threading.Lock()
        self.state = self._load()

    def _seed(self) -> dict[str, Any]:
        today = _today_iso()
        return {
            "inventario": [
                {
                    "id_item": 1,
                    "nombre_item": "Mancuernas ajustables",
                    "tipo": "Pesas",
                    "cantidad_stock": 12,
                    "estado": "Operativo",
                    "n_activo": 1,
                    "unidad_venta": "unidad",
                    "precio_venta": 0,
                    "stock_minimo": 1,
                    "ubicacion": "Almacén",
                    "observaciones": "",
                }
            ],
            "mov_inv": [],
            "productos_tienda": [
                {
                    "id_producto": 1,
                    "nombre_producto": "Proteína Whey",
                    "descripcion": "Proteína de suero de alta calidad",
                    "categoria": "Suplementos",
                    "id_item": None,
                    "unidad_venta": "unidad",
                    "precio_venta": 89.99,
                    "cantidad_stock": 50,
                    "stock_minimo": 10,
                    "estado": "Disponible",
                }
            ],
            "usuario": [
                {
                    "id_usuario": "SGUS001",
                    "nombre": "Carlos Pérez",
                    "correo": "carlos@urp.edu.pe",
                    "telefono": "999111222",
                    "dni": "",
                    "rol": "admin",
                    "estado": "Activo",
                }
            ],
            "clientes": [
                {
                    "id_cliente": 1,
                    "id_usuario": "cliente-1",
                    "nombre": "Maria Fernandez",
                    "correo": "maria@ejemplo.com",
                    "telefono": "999111222",
                    "dni": "74281635",
                    "plan": "MENSUAL",
                    "promocion": "SIN PROMOCION",
                    "estado": "ACTIVO",
                }
            ],
            "tickets_atencion": [],
            "horario": [],
            "catalogo_rutina": [
                {
                    "id_rutina": 1,
                    "nombre_rutina": "Fuerza Inicial",
                    "zonas_musculares": "Piernas, core",
                    "color": "Azul",
                }
            ],
            "asistencia": [],
            "membresia": [
                {
                    "id_membresia": 1,
                    "fecha_inicio": today,
                    "fecha_fin": "2026-12-31",
                    "estado": "Activa",
                    "id_cliente": 1,
                    "id_pm": 1,
                }
            ],
            "planes_membresia": [
                {
                    "id_pm": 1,
                    "nombre_plan": "MENSUAL",
                    "duracion": "30 dias",
                    "precio": 80,
                    "activo": True,
                }
            ],
            "configuracion_gimnasio": {
                "capacidad_total": 30,
                "capacidad_por_hora": 10,
            },
        }

    def _normalize(self, state: dict[str, Any]) -> dict[str, Any]:
        seed = self._seed()
        merged = {**seed, **(state or {})}

        # Garantiza las estructuras esperadas sin romper objetos tipo configuración.
        for key, value in seed.items():
            if isinstance(value, list) and not isinstance(merged.get(key), list):
                merged[key] = value
            elif isinstance(value, dict) and not isinstance(merged.get(key), dict):
                merged[key] = value

        merged["usuario"] = [self._normalize_usuario_record(row) for row in merged.get("usuario", []) if isinstance(row, dict)]
        merged["clientes"] = [self._normalize_cliente_record(row, index) for index, row in enumerate(merged.get("clientes", []), start=1) if isinstance(row, dict)]

        # Migración de inventario: cada item debe tener número de activo único y datos comerciales.
        used_assets: set[int] = set()
        for index, item in enumerate(merged.get("inventario", []), start=1):
            try:
                current = int(item.get("n_activo") or 0)
            except Exception:
                current = 0
            if current <= 0 or current in used_assets:
                current = max(used_assets, default=0) + 1
            item["n_activo"] = current
            used_assets.add(current)
            item.setdefault("unidad_venta", "unidad")
            item.setdefault("precio_venta", 0)
            item.setdefault("stock_minimo", 1)
            item.setdefault("ubicacion", "Almacén")
            item.setdefault("observaciones", "")

        for index, asistencia in enumerate(merged.get("asistencia", []), start=1):
            asistencia.setdefault("id_asistencia", index)
            asistencia.setdefault("servicio", "fitness")

        for producto in merged.get("productos_tienda", []):
            producto.setdefault("id_item", None)
            producto.setdefault("unidad_venta", "unidad")

        cfg = {**seed["configuracion_gimnasio"], **merged.get("configuracion_gimnasio", {})}
        cfg["capacidad_total"] = max(1, int(cfg.get("capacidad_total") or 30))
        cfg["capacidad_por_hora"] = max(1, int(cfg.get("capacidad_por_hora") or 10))
        merged["configuracion_gimnasio"] = cfg

        return merged

    def _user_role_prefix(self, rol: str) -> str:
        rol_value = str(rol or "").strip().lower()
        return {
            "admin": "ADM",
            "trainer": "TRA",
            "staff": "STA",
        }.get(rol_value, "USR")

    def _normalize_usuario_id(self, value: Any) -> str | None:
        if value is None:
            return None

        raw = str(value).strip().upper()
        if not raw:
            return None

        match = re.match(r"^(?:SGUS|USSG)?(\d+)$", raw)
        if match:
            return f"SGUS{int(match.group(1)):03d}"

        return raw

    def _next_usuario_code(self, state: dict[str, Any]) -> str:
        numbers: list[int] = []
        for row in state.get("usuario", []):
            usuario_id = str(row.get("id_usuario") or "").strip().upper()
            match = re.match(r"^SG[A-Z]{3}(\d+)$", usuario_id)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers, default=0) + 1

    def _normalize_usuario_record(self, row: dict[str, Any]) -> dict[str, Any]:
        nombre = str(row.get("nombre") or ((str(row.get("nombres") or "") + " " + str(row.get("apellidos") or "")).strip()) or "").strip()
        correo = str(row.get("correo") or row.get("email") or "").strip()
        rol = str(row.get("rol") or "staff").strip().lower()
        prefix = self._user_role_prefix(rol)
        raw_id = str(row.get("id_usuario") or "").strip().upper()
        number_match = re.search(r"(\d+)$", raw_id)
        number = int(number_match.group(1)) if number_match else self._next_usuario_code({"usuario": [row]})
        raw_id = f"SG{prefix}{int(number):03d}"
        return {
            "id_usuario": raw_id,
            "nombre": nombre,
            "correo": correo,
            "telefono": str(row.get("telefono") or "").strip(),
            "dni": str(row.get("dni") or "").strip(),
            "rol": rol if rol in {"admin", "trainer", "staff"} else "staff",
            "estado": "ACTIVO",
        }

    def _load(self) -> dict[str, Any]:
        if not self.db_file.exists():
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            seed = self._seed()
            self.db_file.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
            return seed
        data = json.loads(self.db_file.read_text(encoding="utf-8"))
        normalized = self._normalize(data)
        # Backfill simple nombre when missing: use email local-part (cleaned) if available
        for u in normalized.get("usuario", []):
            try:
                if not str(u.get("nombre") or "").strip():
                    email = str(u.get("correo") or u.get("email") or "").strip()
                    if email and "@" in email:
                        local = email.split("@", 1)[0]
                        # replace dots/underscores with space and title-case
                        derived = " ".join([part.capitalize() for part in re.sub(r"[._]+", " ", local).split()])
                        u["nombre"] = derived
            except Exception:
                # ignore any error during best-effort backfill
                pass
        # Persist normalized state back to disk to migrate older records (fill `nombre`, normalize ids, etc.)
        try:
            self.db_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # If persistence fails, continue using normalized in-memory state
            pass
        return normalized

    def _save(self) -> None:
        self.db_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _mutate(self, fn):
        with self.lock:
            result = fn(self.state)
            self._save()
            return result

    def _next_int_id(self, table: str, key: str) -> int:
        rows = self.state[table]
        if not rows:
            return 1
        return max(int(row.get(key, 0)) for row in rows) + 1

    def _active_membership_for_cliente(self, state: dict[str, Any], id_cliente: int) -> dict[str, Any] | None:
        today = _today_iso()
        for memb in state["membresia"]:
            if int(memb.get("id_cliente", 0)) != int(id_cliente):
                continue
            if str(memb.get("estado", "")).lower() != "activa":
                continue
            inicio = str(memb.get("fecha_inicio", ""))
            fin = str(memb.get("fecha_fin", ""))
            if inicio <= today <= fin:
                return memb
        return None

    def get_usuario(self, id_usuario: Any) -> dict[str, Any] | None:
        usuario_id = self._normalize_usuario_id(id_usuario)
        if not usuario_id:
            return None

        return next((u for u in self.state["usuario"] if self._normalize_usuario_id(u.get("id_usuario")) == usuario_id), None)

    def get_usuario_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = str(email or "").strip().lower()
        return next(
            (
                u
                for u in self.state["usuario"]
                if str(u.get("email") or u.get("correo") or "").strip().lower() == normalized_email
            ),
            None,
        )

    def usuarios(self) -> list[dict[str, Any]]:
        return self.state["usuario"]

    def usuarios_normalized(self) -> list[dict[str, Any]]:
        return [
            {
                "id_usuario": row["id_usuario"],
                "nombre": row["nombre"],
                "correo": row["correo"],
                "telefono": row["telefono"],
                "dni": row["dni"],
                "rol": row["rol"],
            }
            for row in self.state.get("usuario", [])
        ]

    def upsert_usuario(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            rol = str(payload.get("rol") or "").strip().lower()
            if rol not in {"admin", "trainer", "staff"}:
                raise ValueError("Rol inválido")

            prefix = self._user_role_prefix(rol)
            raw_id = self._normalize_usuario_id(payload.get("id_usuario"))
            if raw_id and re.match(r"^SG[A-Z]{3}\d{3}$", raw_id):
                item_id = raw_id
            else:
                numbers: list[int] = []
                for row in state.get("usuario", []):
                    current_id = str(row.get("id_usuario") or "").strip().upper()
                    if current_id.startswith(f"SG{prefix}"):
                        match = re.match(rf"^SG{prefix}(\d+)$", current_id)
                        if match:
                            numbers.append(int(match.group(1)))
                item_id = f"SG{prefix}{(max(numbers, default=0) + 1):03d}"

            nombre = str(payload.get("nombre") or "").strip()
            correo = str(payload.get("correo") or "").strip()
            item = {
                "id_usuario": item_id,
                "nombre": nombre,
                "correo": correo,
                "telefono": str(payload.get("telefono") or "").strip(),
                "dni": str(payload.get("dni") or "").strip(),
                "rol": rol,
                "estado": "Activo",
            }

            idx = next((i for i, row in enumerate(state["usuario"]) if self._normalize_usuario_id(row.get("id_usuario")) == item_id), -1)
            if idx >= 0:
                state["usuario"][idx] = item
            else:
                state["usuario"].insert(0, item)
            return item

        return self._mutate(_fn)

    def delete_usuario(self, id_usuario: Any) -> None:
        usuario_id = self._normalize_usuario_id(id_usuario)

        def _fn(state: dict[str, Any]):
            state["usuario"] = [u for u in state["usuario"] if self._normalize_usuario_id(u.get("id_usuario")) != usuario_id]

        self._mutate(_fn)

    def clientes(self) -> list[dict[str, Any]]:
        return self.state["clientes"]

    def _normalize_cliente_record(self, row: dict[str, Any], fallback_index: int) -> dict[str, Any]:
        id_cliente = row.get("id_cliente")
        if id_cliente is None:
            id_cliente = fallback_index

        nombre = str(row.get("nombre") or ((str(row.get("nombres") or "") + " " + str(row.get("apellidos") or "")).strip()) or "").strip()
        correo = str(row.get("correo") or row.get("email") or "").strip()
        telefono = str(row.get("telefono") or "").strip()
        dni = str(row.get("dni") or "").strip()
        plan = str(row.get("plan") or "").strip()
        promocion = str(row.get("promocion") or "").strip()
        raw_estado = row.get("estado")
        if isinstance(raw_estado, bool):
            estado = "Activo" if raw_estado else "Inactivo"
        else:
            estado_text = str(raw_estado or "").strip().lower()
            if estado_text in {"true", "activo", "activa", "1", "si", "sí"}:
                estado = "Activo"
            elif estado_text in {"false", "inactivo", "inactiva", "0", "no"}:
                estado = "Inactivo"
            else:
                estado = str(raw_estado or "").strip() or "Activo"

        return {
            "id_cliente": int(id_cliente),
            "id_usuario": str(row.get("id_usuario") or f"SGCLI{int(id_cliente):03d}").strip().upper(),
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "dni": dni,
            "plan": plan,
            "promocion": promocion,
            "estado": estado.upper() if estado else "ACTIVO",
        }

    def clientes_normalized(self) -> list[dict[str, Any]]:
        return [
            {
                "id_usuario": row["id_usuario"],
                "nombre": row["nombre"],
                "correo": row["correo"],
                "telefono": row["telefono"],
                "dni": row["dni"],
                "plan": row["plan"],
                "promocion": row["promocion"],
                "estado": row["estado"],
            }
            for row in self.state.get("clientes", [])
        ]

    def upsert_cliente(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            raw_id = payload.get("id_usuario") or payload.get("id_cliente")
            id_usuario = str(raw_id).strip() if raw_id not in [None, ""] else ""

            item_id = None
            if id_usuario.startswith("cliente-"):
                try:
                    item_id = int(id_usuario.split("-", 1)[1])
                except Exception:
                    item_id = None
            elif str(raw_id or "").isdigit():
                item_id = int(str(raw_id))

            if item_id is None:
                item_id = self._next_int_id("clientes", "id_cliente")

            if not id_usuario or id_usuario.isdigit():
                id_usuario = f"SGCLI{int(item_id):03d}"

            raw_estado = payload.get("estado")
            if isinstance(raw_estado, bool):
                estado = "ACTIVO" if raw_estado else "INACTIVO"
            else:
                estado_text = str(raw_estado or "").strip().lower()
                if estado_text in {"true", "activo", "activa", "1", "si", "sí"}:
                    estado = "ACTIVO"
                elif estado_text in {"false", "inactivo", "inactiva", "0", "no"}:
                    estado = "INACTIVO"
                else:
                    estado = str(raw_estado or "ACTIVO").strip().upper() or "ACTIVO"

            item = {
                "id_cliente": int(item_id),
                "id_usuario": id_usuario,
                "nombre": str(payload.get("nombre") or "").strip(),
                "correo": str(payload.get("correo") or payload.get("email") or "").strip(),
                "telefono": str(payload.get("telefono") or "").strip(),
                "dni": str(payload.get("dni") or "").strip(),
                "plan": str(payload.get("plan") or "MENSUAL").strip() or "MENSUAL",
                "promocion": str(payload.get("promocion") or "SIN PROMOCION").strip() or "SIN PROMOCION",
                "estado": estado,
            }

            idx = next((i for i, row in enumerate(state["clientes"]) if int(row.get("id_cliente", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["clientes"][idx] = item
            else:
                state["clientes"].insert(0, item)
            return item

        return self._mutate(_fn)

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return next((c for c in self.state["clientes"] if int(c.get("id_cliente", 0)) == int(id_cliente)), None)

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return next((c for c in self.state["clientes"] if str(c.get("dni", "")) == str(dni)), None)

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        return next((c for c in self.state["clientes"] if str(c.get("email", "")).lower() == email.lower()), None)

    def delete_cliente(self, id_cliente: int) -> None:
        def _fn(state: dict[str, Any]):
            def matches_id(value):
                try:
                    if value is None:
                        return False
                    # numeric comparison
                    if isinstance(value, (int, float)) or (isinstance(value, str) and str(value).isdigit()):
                        return int(value) == int(id_cliente)
                    # string uid comparison (SGCLI### or cliente-#)
                    s = str(value).strip().upper()
                    if s.startswith("SGCLI"):
                        try:
                            return int(s.replace("SGCLI", "")) == int(id_cliente)
                        except Exception:
                            return False
                    if s.startswith("CLIENTE-"):
                        try:
                            return int(s.split("-", 1)[1]) == int(id_cliente)
                        except Exception:
                            return False
                    return False
                except Exception:
                    return False

            state["clientes"] = [c for c in state["clientes"] if not matches_id(c.get("id_cliente"))]
            state["membresia"] = [m for m in state["membresia"] if not matches_id(m.get("id_cliente"))]
            state["asistencia"] = [a for a in state["asistencia"] if not matches_id(a.get("id_cliente") or a.get("id_cliente_uid") or a.get("id_cliente"))]
            state["horario"] = [h for h in state["horario"] if not matches_id(h.get("id_cliente"))]
            state["tickets_atencion"] = [t for t in state["tickets_atencion"] if not matches_id(t.get("id_cliente"))]

        self._mutate(_fn)

    def planes_membresia(self) -> list[dict[str, Any]]:
        return self.state.get("planes_membresia", [])

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        return next((p for p in self.state.get("planes_membresia", []) if int(p.get("id_pm", 0)) == int(id_pm)), None)

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            state.setdefault("planes_membresia", [])
            item = {**payload}
            item_id = item.get("id_pm")
            if item_id is None:
                item_id = self._next_int_id("planes_membresia", "id_pm")
            item["id_pm"] = int(item_id)
            item["nombre_plan"] = str(item.get("nombre_plan") or "MENSUAL").strip().upper()
            item["duracion"] = str(item.get("duracion") or "30 dias").strip()
            item["precio"] = int(item.get("precio") or 0)
            item["activo"] = bool(item.get("activo", True))
            idx = next((i for i, row in enumerate(state["planes_membresia"]) if int(row.get("id_pm", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["planes_membresia"][idx] = item
            else:
                state["planes_membresia"].insert(0, item)
            return item

        return self._mutate(_fn)

    def delete_plan_membresia(self, id_pm: int) -> None:
        def _fn(state: dict[str, Any]):
            if any(int(m.get("id_pm", 0)) == int(id_pm) for m in state.get("membresia", [])):
                raise ValueError("No se puede eliminar un plan usado por membresías")
            state["planes_membresia"] = [p for p in state.get("planes_membresia", []) if int(p.get("id_pm", 0)) != int(id_pm)]

        self._mutate(_fn)

    def membresias(self) -> list[dict[str, Any]]:
        return self.state["membresia"]

    def membresias_por_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return [m for m in self.state["membresia"] if int(m.get("id_cliente", 0)) == int(id_cliente)]

    def crear_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_pm = int(payload.get("id_pm", 0))
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")
        if not self.get_plan_membresia(id_pm):
            raise ValueError("Plan de membresía no encontrado")

        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_membresia")
            if item_id is None:
                item_id = self._next_int_id("membresia", "id_membresia")
            item["id_membresia"] = int(item_id)
            item["id_cliente"] = id_cliente
            item["id_pm"] = id_pm
            item["fecha_inicio"] = _safe_date(item.get("fecha_inicio", ""))
            item["fecha_fin"] = _safe_date(item.get("fecha_fin", ""))
            item["estado"] = item.get("estado", "Activa")
            idx = next((i for i, row in enumerate(state["membresia"]) if int(row.get("id_membresia", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["membresia"][idx] = item
            else:
                state["membresia"].insert(0, item)
            return item

        return self._mutate(_fn)

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        cliente_payload = payload["cliente"]
        id_pm = int(payload["id_pm"])
        fecha_inicio = payload["fecha_inicio"]
        fecha_fin = payload["fecha_fin"]

        cliente = self.upsert_cliente(cliente_payload)
        membresia = self.crear_membresia(
            {
                "id_cliente": int(cliente["id_cliente"]),
                "id_pm": id_pm,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "estado": "Activa",
            }
        )
        return {"cliente": cliente, "membresia": membresia}

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

        fecha = str(payload.get("fecha") or "").strip() or _today_iso()
        hora = str(payload.get("hora") or "").strip() or _now_time()
        id_usuario_registra = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        def _fn(state: dict[str, Any]):
            membresia = self._active_membership_for_cliente(state, id_cliente)
            if not membresia:
                raise ValueError("Cliente sin membresía activa")
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

        return self._mutate(_fn)

    def actualizar_asistencia(self, id_asistencia: int, payload: dict[str, Any]) -> dict[str, Any]:
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
            self._validate_attendance_capacity(state, current.get("fecha", _today_iso()), current.get("hora", _now_time()), exclude_id=id_asistencia)
            state["asistencia"][idx] = current
            return current

        return self._mutate(_fn)

    def eliminar_asistencia(self, id_asistencia: int) -> None:
        def _fn(state: dict[str, Any]):
            original = len(state["asistencia"])
            state["asistencia"] = [a for a in state["asistencia"] if int(a.get("id_asistencia", 0) or 0) != int(id_asistencia)]
            if len(state["asistencia"]) == original:
                raise ValueError("Asistencia no encontrada")

        self._mutate(_fn)

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
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

    def inventario(self) -> list[dict[str, Any]]:
        return self.state["inventario"]

    def get_item_inventario(self, id_item: int) -> dict[str, Any] | None:
        return next((i for i in self.state["inventario"] if int(i.get("id_item", 0)) == int(id_item)), None)

    def upsert_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_item")
            if item_id is None:
                item_id = self._next_int_id("inventario", "id_item")
            item["id_item"] = int(item_id)
            item["cantidad_stock"] = max(0, int(item.get("cantidad_stock") or 0))
            item["stock_minimo"] = max(0, int(item.get("stock_minimo") or 1))
            item["unidad_venta"] = str(item.get("unidad_venta") or "unidad")
            item["precio_venta"] = float(item.get("precio_venta") or 0)
            item["ubicacion"] = str(item.get("ubicacion") or "Almacén")
            item["observaciones"] = str(item.get("observaciones") or "")
            idx = next((i for i, row in enumerate(state["inventario"]) if int(row.get("id_item", 0)) == int(item_id)), -1)
            if idx >= 0:
                item["n_activo"] = int(item.get("n_activo") or state["inventario"][idx].get("n_activo") or self._next_n_activo(state))
                state["inventario"][idx] = item
            else:
                item["n_activo"] = int(item.get("n_activo") or self._next_n_activo(state))
                state["inventario"].insert(0, item)
            return item

        return self._mutate(_fn)

    def delete_inventario(self, id_item: int) -> None:
        def _fn(state: dict[str, Any]):
            state["inventario"] = [i for i in state["inventario"] if int(i.get("id_item", 0)) != int(id_item)]
            state["mov_inv"] = [m for m in state["mov_inv"] if int(m.get("id_item", 0)) != int(id_item)]
            for producto in state.get("productos_tienda", []):
                if int(producto.get("id_item") or 0) == int(id_item):
                    producto["id_item"] = None

        self._mutate(_fn)

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return self.state["mov_inv"]

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_item = int(payload.get("id_item", 0))
        id_usuario = self._normalize_usuario_id(payload.get("id_usuario"))
        cantidad = max(1, int(payload.get("cantidad", 1)))
        tipo = str(payload.get("tipo_movimiento", "")).lower()

        if not self.get_item_inventario(id_item):
            raise ValueError("Item de inventario no encontrado")
        if not self.get_usuario(id_usuario):
            raise ValueError("Usuario no encontrado")
        if tipo not in {"entrada", "salida", "ajuste"}:
            raise ValueError("Tipo de movimiento inválido")

        def _fn(state: dict[str, Any]):
            item = next((i for i in state["inventario"] if int(i.get("id_item", 0)) == id_item), None)
            if not item:
                raise ValueError("Item de inventario no encontrado")
            stock_actual = int(item.get("cantidad_stock", 0))
            if tipo == "entrada":
                nuevo_stock = stock_actual + cantidad
            elif tipo == "salida":
                if stock_actual < cantidad:
                    raise ValueError("Stock insuficiente para salida")
                nuevo_stock = stock_actual - cantidad
            else:
                nuevo_stock = cantidad

            item["cantidad_stock"] = nuevo_stock
            mov = {
                "id_mov": self._next_int_id("mov_inv", "id_mov"),
                "id_item": id_item,
                "id_usuario": id_usuario,
                "tipo_movimiento": tipo,
                "fecha_movimiento": _safe_date(payload.get("fecha_movimiento", "")),
                "descripcion": payload.get("descripcion", ""),
                "cantidad": cantidad,
            }
            state["mov_inv"].insert(0, mov)
            return {"movimiento": mov, "stock_actual": nuevo_stock}

        return self._mutate(_fn)

    def tickets(self) -> list[dict[str, Any]]:
        return self.state["tickets_atencion"]

    def upsert_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_usuario = self._normalize_usuario_id(payload.get("id_usuario"))
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")
        if not self.get_usuario(id_usuario):
            raise ValueError("Usuario no encontrado")

        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_ticket")
            if item_id is None:
                item_id = self._next_int_id("tickets_atencion", "id_ticket")
            item["id_ticket"] = int(item_id)
            item["id_usuario"] = id_usuario
            item["fecha_emitido"] = _safe_date(item.get("fecha_emitido", ""))
            idx = next((i for i, row in enumerate(state["tickets_atencion"]) if int(row.get("id_ticket", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["tickets_atencion"][idx] = item
            else:
                state["tickets_atencion"].insert(0, item)
            return item

        return self._mutate(_fn)

    def catalogo_rutina(self) -> list[dict[str, Any]]:
        return self.state["catalogo_rutina"]

    def upsert_rutina(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_rutina")
            if item_id is None:
                item_id = self._next_int_id("catalogo_rutina", "id_rutina")
            item["id_rutina"] = int(item_id)
            idx = next((i for i, row in enumerate(state["catalogo_rutina"]) if int(row.get("id_rutina", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["catalogo_rutina"][idx] = item
            else:
                state["catalogo_rutina"].insert(0, item)
            return item

        return self._mutate(_fn)

    def horarios(self) -> list[dict[str, Any]]:
        return self.state["horario"]

    def upsert_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_rutina = int(payload.get("id_rutina", 0))
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")
        if not next((r for r in self.state["catalogo_rutina"] if int(r.get("id_rutina", 0)) == id_rutina), None):
            raise ValueError("Rutina no encontrada")

        dia = str(payload.get("dia_semana") or "Lunes").strip()
        hora_inicio = str(payload.get("hora_inicio") or "06:00").strip()
        hora_fin = str(payload.get("hora_fin") or "07:00").strip()
        capacidad_maxima = max(1, int(payload.get("capacidad_maxima") or 1))

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

        return self._mutate(_fn)

    def configuracion_gimnasio(self) -> dict[str, Any]:
        return self.state.get("configuracion_gimnasio", {"capacidad_total": 30, "capacidad_por_hora": 10})

    def actualizar_configuracion_gimnasio(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            cfg = state.setdefault("configuracion_gimnasio", {})
            cfg["capacidad_total"] = max(1, int(payload.get("capacidad_total", cfg.get("capacidad_total", 30))))
            cfg["capacidad_por_hora"] = max(1, int(payload.get("capacidad_por_hora", cfg.get("capacidad_por_hora", 10))))
            return cfg

        return self._mutate(_fn)

    def summary(self) -> dict[str, Any]:
        total_clientes = len(self.state["clientes"])
        membresias_activas = len(
            [
                m
                for m in self.state["membresia"]
                if str(m.get("estado", "")).lower() == "activa"
                and str(m.get("fecha_inicio", "")) <= _today_iso() <= str(m.get("fecha_fin", ""))
            ]
        )
        asistencias_hoy = len([a for a in self.state["asistencia"] if a.get("fecha") == _today_iso()])
        items_stock_bajo = [
            item
            for item in self.state["inventario"]
            if int(item.get("cantidad_stock", 0)) <= int(item.get("stock_minimo", 0))
        ]

        return {
            "stats": {
                "total_clientes": total_clientes,
                "membresias_activas": membresias_activas,
                "asistencias_hoy": asistencias_hoy,
                "total_items_inventario": len(self.state["inventario"]),
                "items_stock_bajo": len(items_stock_bajo),
            },
            "flujos": {
                "registro_control_inventario": {
                    "items": len(self.state["inventario"]),
                    "movimientos": len(self.state["mov_inv"]),
                },
                "registro_usuarios_membresia": {
                    "usuarios": len(self.state["usuario"]),
                    "clientes": total_clientes,
                    "membresias": len(self.state["membresia"]),
                },
                "registro_asistencia_usuario": {
                    "asistencias": len(self.state["asistencia"]),
                    "asistencias_hoy": asistencias_hoy,
                },
            },
            "alertas": items_stock_bajo,
        }

    def productos_tienda(self) -> list[dict[str, Any]]:
        return self.state.get("productos_tienda", [])

    def get_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return next((p for p in self.state.get("productos_tienda", []) if int(p.get("id_producto", 0)) == int(id_producto)), None)

    def upsert_producto_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            state.setdefault("productos_tienda", [])
            producto = {**payload}
            producto_id = producto.get("id_producto")
            if producto_id is None:
                producto_id = self._next_int_id("productos_tienda", "id_producto")
            producto["id_producto"] = int(producto_id)
            producto["id_item"] = int(producto["id_item"]) if producto.get("id_item") else None
            producto["unidad_venta"] = str(producto.get("unidad_venta") or "unidad")
            producto["precio_venta"] = float(producto.get("precio_venta") or 0)
            producto["cantidad_stock"] = max(0, int(producto.get("cantidad_stock") or 0))
            producto["stock_minimo"] = max(0, int(producto.get("stock_minimo") or 0))

            if producto["id_item"]:
                item = next((i for i in state.get("inventario", []) if int(i.get("id_item", 0)) == producto["id_item"]), None)
                if not item:
                    raise ValueError("Item de almacén no encontrado")
                # Almacén -> precio de venta y unidad de venta para tienda.
                item["unidad_venta"] = producto["unidad_venta"]
                item["precio_venta"] = producto["precio_venta"]
                if not producto.get("nombre_producto"):
                    producto["nombre_producto"] = item.get("nombre_item", "Sin nombre")
                if producto["cantidad_stock"] == 0:
                    producto["cantidad_stock"] = int(item.get("cantidad_stock", 0) or 0)

            idx = next((i for i, row in enumerate(state["productos_tienda"]) if int(row.get("id_producto", 0)) == int(producto_id)), -1)
            if idx >= 0:
                state["productos_tienda"][idx] = producto
            else:
                state["productos_tienda"].insert(0, producto)
            return producto

        return self._mutate(_fn)

    def delete_producto_tienda(self, id_producto: int) -> None:
        def _fn(state: dict[str, Any]):
            if "productos_tienda" in state:
                state["productos_tienda"] = [p for p in state["productos_tienda"] if int(p.get("id_producto", 0)) != int(id_producto)]

        self._mutate(_fn)
