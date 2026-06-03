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
                }
            ],
            "mov_inv": [],
            "productos_tienda": [
                {
                    "id_producto": 1,
                    "nombre_producto": "Proteína Whey",
                    "descripcion": "Proteína de suero de alta calidad",
                    "categoria": "Suplementos",
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
                }
            ],
        }

    def _normalize(self, state: dict[str, Any]) -> dict[str, Any]:
        seed = self._seed()
        merged = {**seed, **(state or {})}
        for key, value in seed.items():
            if not isinstance(merged.get(key), list):
                merged[key] = value
        merged["usuario"] = [self._normalize_usuario_record(row) for row in merged.get("usuario", []) if isinstance(row, dict)]
        merged["clientes"] = [self._normalize_cliente_record(row, index) for index, row in enumerate(merged.get("clientes", []), start=1) if isinstance(row, dict)]
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
            state["clientes"] = [c for c in state["clientes"] if int(c.get("id_cliente", 0)) != int(id_cliente)]
            state["membresia"] = [m for m in state["membresia"] if int(m.get("id_cliente", 0)) != int(id_cliente)]
            state["asistencia"] = [a for a in state["asistencia"] if int(a.get("id_cliente", 0)) != int(id_cliente)]
            state["horario"] = [h for h in state["horario"] if int(h.get("id_cliente", 0)) != int(id_cliente)]
            state["tickets_atencion"] = [t for t in state["tickets_atencion"] if int(t.get("id_cliente", 0)) != int(id_cliente)]

        self._mutate(_fn)

    def planes_membresia(self) -> list[dict[str, Any]]:
        return [self.state["planes_membresia"][0]] if self.state.get("planes_membresia") else []

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        if int(id_pm) != 1:
            return None
        return self.state["planes_membresia"][0] if self.state.get("planes_membresia") else None

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            item = {
                "id_pm": 1,
                "nombre_plan": "MENSUAL",
                "duracion": "30 dias",
                "precio": 80,
            }
            state["planes_membresia"] = [item]
            return item

        return self._mutate(_fn)

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
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")

        def _fn(state: dict[str, Any]):
            membresia = self._active_membership_for_cliente(state, id_cliente)
            validacion = bool(membresia)
            if not validacion:
                raise ValueError("Cliente sin membresía activa")
            item = {
                "id_asistencia": self._next_int_id("asistencia", "id_asistencia"),
                "id_cliente": int(id_cliente),
                "id_membresia": int(membresia["id_membresia"]),
                "fecha": _today_iso(),
                "hora": _now_time(),
                "validacion": True,
            }
            state["asistencia"].insert(0, item)
            return item

        return self._mutate(_fn)

    def registrar_asistencia_detallada(self, payload: dict[str, Any]) -> dict[str, Any]:
        # payload expected keys: id_cliente, id_usuario (admin who registers, optional), fecha (optional), hora (optional), servicio
        id_cliente = int(payload.get("id_cliente", 0))
        if not self.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")

        servicio = str(payload.get("servicio") or "").strip().lower()
        allowed = {"fitness", "musculacion", "cardio", "baile"}
        if servicio not in allowed:
            raise ValueError(f"Servicio inválido: {servicio}")

        fecha = str(payload.get("fecha") or "").strip() or _today_iso()
        hora = str(payload.get("hora") or "").strip() or _now_time()
        id_usuario_registra = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        def _fn(state: dict[str, Any]):
            membresia = self._active_membership_for_cliente(state, id_cliente)
            validacion = bool(membresia)
            if not validacion:
                raise ValueError("Cliente sin membresía activa")
            item = {
                "id_asistencia": self._next_int_id("asistencia", "id_asistencia"),
                "id_cliente": int(id_cliente),
                "id_membresia": int(membresia["id_membresia"]),
                "fecha": fecha,
                "hora": hora,
                "servicio": servicio,
                "registrado_por": id_usuario_registra,
                "validacion": True,
            }
            state["asistencia"].insert(0, item)
            return item

        return self._mutate(_fn)

    def registrar_asistencia_por_dni(self, dni: str) -> dict[str, Any]:
        # Support payload dict (dni plus optional fields) or simple dni string
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
            idx = next((i for i, row in enumerate(state["inventario"]) if int(row.get("id_item", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["inventario"][idx] = item
            else:
                state["inventario"].insert(0, item)
            return item

        return self._mutate(_fn)

    def delete_inventario(self, id_item: int) -> None:
        def _fn(state: dict[str, Any]):
            state["inventario"] = [i for i in state["inventario"] if int(i.get("id_item", 0)) != int(id_item)]
            state["mov_inv"] = [m for m in state["mov_inv"] if int(m.get("id_item", 0)) != int(id_item)]

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

        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_horario")
            if item_id is None:
                item_id = self._next_int_id("horario", "id_horario")
            item["id_horario"] = int(item_id)
            item["id_cliente"] = id_cliente
            item["id_rutina"] = id_rutina
            idx = next((i for i, row in enumerate(state["horario"]) if int(row.get("id_horario", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["horario"][idx] = item
            else:
                state["horario"].insert(0, item)
            return item

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
            if "productos_tienda" not in state:
                state["productos_tienda"] = []
            
            producto = {**payload}
            producto_id = producto.get("id_producto")
            if producto_id is None:
                producto_id = self._next_int_id("productos_tienda", "id_producto")
            producto["id_producto"] = int(producto_id)
            
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
