from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from utils.security import hash_password, verify_password


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


class GymDomainService:
    def __init__(self, db_file: Any | None = None) -> None:
        raise RuntimeError("GymDomainService solo contiene reglas de negocio. Usa SupabaseGymService para persistencia.")

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
            "pedidos_tienda": [],
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
            "horarios_servicio": [
                {"id_horario_servicio": 1, "servicio": "fitness", "codigo_dia": "LUN", "dia": "lunes", "hora_inicio": "06:00", "hora_fin": "08:00", "cupos": 12, "cupos_usados": 0, "activo": True},
                {"id_horario_servicio": 2, "servicio": "musculacion", "codigo_dia": "MAR", "dia": "martes", "hora_inicio": "18:00", "hora_fin": "20:00", "cupos": 10, "cupos_usados": 0, "activo": True},
                {"id_horario_servicio": 3, "servicio": "cardio", "codigo_dia": "MIE", "dia": "miercoles", "hora_inicio": "07:00", "hora_fin": "09:00", "cupos": 10, "cupos_usados": 0, "activo": True},
                {"id_horario_servicio": 4, "servicio": "baile", "codigo_dia": "VIE", "dia": "viernes", "hora_inicio": "18:00", "hora_fin": "20:00", "cupos": 14, "cupos_usados": 0, "activo": True},
            ],
            "matriculas_horario": [],
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
                },
                {
                    "id_pm": 2,
                    "nombre_plan": "3 MESES",
                    "duracion": "90 dias",
                    "precio": 220,
                    "activo": True,
                },
                {
                    "id_pm": 3,
                    "nombre_plan": "ANUAL",
                    "duracion": "365 dias",
                    "precio": 780,
                    "activo": True,
                },
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

        merged["pedidos_tienda"] = [
            self._normalize_pedido_tienda(row, index)
            for index, row in enumerate(merged.get("pedidos_tienda", []), start=1)
            if isinstance(row, dict)
        ]

        merged["horarios_servicio"] = self._normalize_horarios_servicio(merged.get("horarios_servicio", seed["horarios_servicio"]))
        merged["matriculas_horario"] = [
            self._normalize_matricula_horario(row, index)
            for index, row in enumerate(merged.get("matriculas_horario", []), start=1)
            if isinstance(row, dict)
        ]
        self._recount_schedule_cupos(merged)
        self._ensure_default_membership_plans(merged)

        cfg = {**seed["configuracion_gimnasio"], **merged.get("configuracion_gimnasio", {})}
        cfg["capacidad_total"] = max(1, int(cfg.get("capacidad_total") or 30))
        cfg["capacidad_por_hora"] = max(1, int(cfg.get("capacidad_por_hora") or 10))
        merged["configuracion_gimnasio"] = cfg

        for cliente in merged.get("clientes", []):
            self._ensure_membership_for_active_client(merged, cliente)

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
        password_hash = str(row.get("password_hash") or "").strip()
        if not password_hash and row.get("password"):
            password_hash = hash_password(str(row.get("password") or ""))
        return {
            "id_usuario": raw_id,
            "nombre": nombre,
            "correo": correo,
            "telefono": str(row.get("telefono") or "").strip(),
            "dni": str(row.get("dni") or "").strip(),
            "rol": rol if rol in {"admin", "trainer", "staff"} else "staff",
            "estado": "ACTIVO",
            "password_hash": password_hash,
        }

    def _load(self) -> dict[str, Any]:
        raise RuntimeError("GymDomainService no lee archivos locales. Usa SupabaseGymService.")

    def _save(self) -> None:
        raise RuntimeError("GymDomainService no guarda archivos locales. Usa SupabaseGymService.")

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

    def _latest_membership_for_cliente(self, state: dict[str, Any], id_cliente: int) -> dict[str, Any] | None:
        memberships = [
            membership
            for membership in state.get("membresia", [])
            if int(membership.get("id_cliente", 0) or 0) == int(id_cliente)
        ]
        return sorted(memberships, key=lambda row: int(row.get("id_membresia", 0) or 0), reverse=True)[0] if memberships else None

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
                "has_password": bool(row.get("password_hash")),
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
            password = str(payload.get("password") or payload.get("contrasena") or "").strip()
            idx = next((i for i, row in enumerate(state["usuario"]) if self._normalize_usuario_id(row.get("id_usuario")) == item_id), -1)
            existing = state["usuario"][idx] if idx >= 0 else {}
            if idx < 0 and not password:
                raise ValueError("Ingresa una contraseña para el usuario")
            if password and len(password) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres")
            item = {
                "id_usuario": item_id,
                "nombre": nombre,
                "correo": correo,
                "telefono": str(payload.get("telefono") or "").strip(),
                "dni": str(payload.get("dni") or "").strip(),
                "rol": rol,
                "estado": "Activo",
                "password_hash": hash_password(password) if password else str(existing.get("password_hash") or ""),
            }

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
        password_hash = str(row.get("password_hash") or "").strip()
        if not password_hash and row.get("password"):
            password_hash = hash_password(str(row.get("password") or ""))
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
            "password_hash": password_hash,
        }

    def _plan_duration_days(self, plan_name: str) -> int:
        normalized = str(plan_name or "").strip().upper()
        match = re.search(r"(\d+)", normalized)
        amount = int(match.group(1)) if match else 1

        if "ANUAL" in normalized or "AÑO" in normalized:
            return 365 * amount
        if "MES" in normalized:
            return 30 * amount
        return 30

    def _next_int_id_in_state(self, state: dict[str, Any], table: str, key: str) -> int:
        rows = state.setdefault(table, [])
        if not rows:
            return 1
        return max(int(row.get(key, 0) or 0) for row in rows) + 1

    def _normalize_pedido_tienda(self, row: dict[str, Any], fallback_id: int) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for item in row.get("items", []):
            if not isinstance(item, dict):
                continue
            cantidad = max(1, int(item.get("cantidad") or 1))
            precio = float(item.get("precio_unitario") or item.get("precio") or 0)
            subtotal = float(item.get("subtotal") or precio * cantidad)
            items.append(
                {
                    "id_producto": int(item.get("id_producto") or 0),
                    "nombre_producto": str(item.get("nombre_producto") or item.get("nombre") or "Producto"),
                    "cantidad": cantidad,
                    "precio_unitario": precio,
                    "subtotal": subtotal,
                }
            )

        subtotal = float(row.get("subtotal") or sum(float(item.get("subtotal") or 0) for item in items))
        igv = float(row.get("igv") or round(subtotal * 0.18, 2))
        total = float(row.get("total") or round(subtotal + igv, 2))

        return {
            "id_pedido": int(row.get("id_pedido") or fallback_id),
            "id_cliente": int(row.get("id_cliente") or 0) or None,
            "cliente_nombre": str(row.get("cliente_nombre") or row.get("nombre_cliente") or "Cliente"),
            "cliente_correo": str(row.get("cliente_correo") or row.get("correo") or ""),
            "cliente_dni": str(row.get("cliente_dni") or row.get("dni") or ""),
            "fecha_pedido": str(row.get("fecha_pedido") or _now_iso()),
            "metodo_pago": str(row.get("metodo_pago") or "tarjeta"),
            "referencia_pago": str(row.get("referencia_pago") or ""),
            "estado_pago": str(row.get("estado_pago") or "PAGADO"),
            "estado_pedido": str(row.get("estado_pedido") or "PENDIENTE"),
            "subtotal": round(subtotal, 2),
            "igv": round(igv, 2),
            "total": round(total, 2),
            "items": items,
        }

    def _ensure_default_membership_plans(self, state: dict[str, Any]) -> None:
        defaults = [
            {"nombre_plan": "MENSUAL", "duracion": "30 dias", "precio": 80},
            {"nombre_plan": "3 MESES", "duracion": "90 dias", "precio": 220},
            {"nombre_plan": "ANUAL", "duracion": "365 dias", "precio": 780},
        ]
        state.setdefault("planes_membresia", [])

        for default in defaults:
            normalized_name = default["nombre_plan"].upper()
            existing = next(
                (
                    plan
                    for plan in state["planes_membresia"]
                    if str(plan.get("nombre_plan") or "").strip().upper() == normalized_name
                ),
                None,
            )
            if existing:
                existing.setdefault("duracion", default["duracion"])
                existing.setdefault("precio", default["precio"])
                existing.setdefault("activo", True)
                continue

            state["planes_membresia"].append(
                {
                    "id_pm": self._next_int_id_in_state(state, "planes_membresia", "id_pm"),
                    "nombre_plan": default["nombre_plan"],
                    "duracion": default["duracion"],
                    "precio": default["precio"],
                    "activo": True,
                }
            )

    def _ensure_plan_for_client(self, state: dict[str, Any], plan_name: str) -> dict[str, Any]:
        state.setdefault("planes_membresia", [])
        normalized = str(plan_name or "MENSUAL").strip().upper() or "MENSUAL"
        existing = next(
            (
                plan
                for plan in state["planes_membresia"]
                if str(plan.get("nombre_plan") or "").strip().upper() == normalized
            ),
            None,
        )
        if existing:
            return existing

        days = self._plan_duration_days(normalized)
        plan = {
            "id_pm": self._next_int_id_in_state(state, "planes_membresia", "id_pm"),
            "nombre_plan": normalized,
            "duracion": f"{days} dias",
            "precio": 0,
            "activo": True,
        }
        state["planes_membresia"].insert(0, plan)
        return plan

    def _ensure_membership_for_active_client(self, state: dict[str, Any], cliente: dict[str, Any]) -> dict[str, Any] | None:
        id_cliente = int(cliente.get("id_cliente", 0) or 0)
        if not id_cliente:
            return None

        estado = str(cliente.get("estado") or "").strip().upper()
        if estado not in {"ACTIVO", "ACTIVA"}:
            return None

        current = self._active_membership_for_cliente(state, id_cliente)
        if current:
            return current

        plan = self._ensure_plan_for_client(state, cliente.get("plan") or "MENSUAL")
        start = _today_iso()
        end = (datetime.fromisoformat(start) + timedelta(days=self._plan_duration_days(plan.get("nombre_plan", "MENSUAL")))).date().isoformat()
        membership = {
            "id_membresia": self._next_int_id_in_state(state, "membresia", "id_membresia"),
            "fecha_inicio": start,
            "fecha_fin": end,
            "estado": "Activa",
            "id_cliente": id_cliente,
            "id_pm": int(plan.get("id_pm")),
        }
        state.setdefault("membresia", []).insert(0, membership)
        return membership

    def clientes_normalized(self) -> list[dict[str, Any]]:
        result = []
        for row in self.state.get("clientes", []):
            membership = self._latest_membership_for_cliente(self.state, int(row.get("id_cliente", 0) or 0)) or {}
            result.append(
                {
                    "id_cliente": row["id_cliente"],
                    "id_usuario": row["id_usuario"],
                    "nombre": row["nombre"],
                    "correo": row["correo"],
                    "telefono": row["telefono"],
                    "dni": row["dni"],
                    "plan": row["plan"],
                    "promocion": row["promocion"],
                    "estado": row["estado"],
                    "id_membresia": membership.get("id_membresia"),
                    "membership_status": membership.get("estado") or row["estado"],
                    "membership_start": membership.get("fecha_inicio", ""),
                    "membership_end": membership.get("fecha_fin", ""),
                    "payment_status": membership.get("estado_pago", ""),
                    "payment_reference": membership.get("referencia_pago", ""),
                    "has_password": bool(row.get("password_hash")),
                }
            )
        return result

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
            existing = state["clientes"][idx] if idx >= 0 else {}
            password = str(payload.get("password") or payload.get("contrasena") or "").strip()
            if idx < 0 and not password:
                raise ValueError("Ingresa una contraseña para el cliente")
            if password and len(password) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres")
            item["password_hash"] = hash_password(password) if password else str(existing.get("password_hash") or "")
            if idx >= 0:
                state["clientes"][idx] = item
            else:
                state["clientes"].insert(0, item)
            self._ensure_membership_for_active_client(state, item)
            return item

        return self._mutate(_fn)

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return next((c for c in self.state["clientes"] if int(c.get("id_cliente", 0)) == int(id_cliente)), None)

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return next((c for c in self.state["clientes"] if str(c.get("dni", "")) == str(dni)), None)

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = str(email or "").strip().lower()
        return next(
            (
                c
                for c in self.state["clientes"]
                if str(c.get("correo") or c.get("email") or "").strip().lower() == normalized
            ),
            None,
        )

    def authenticate_usuario_password(self, correo: str, password: str) -> dict[str, Any] | None:
        usuario = self.get_usuario_by_email(correo)
        if not usuario or not verify_password(password, str(usuario.get("password_hash") or "")):
            return None
        return usuario

    def authenticate_cliente_password(self, correo: str, password: str) -> dict[str, Any] | None:
        cliente = self.get_cliente_by_email(correo)
        if not cliente or not verify_password(password, str(cliente.get("password_hash") or "")):
            return None
        return cliente

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
            state["asistencia"] = [a for a in state["asistencia"] if not matches_id(a.get("id_cliente_num") or a.get("id_cliente") or a.get("id_cliente_uid"))]
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

    def registrar_cliente_publico(self, payload: dict[str, Any]) -> dict[str, Any]:
        nombre = str(payload.get("nombre") or payload.get("google_name") or "").strip()
        correo = str(payload.get("correo") or payload.get("google_email") or "").strip().lower()
        telefono = str(payload.get("telefono") or "").strip()
        dni = str(payload.get("dni") or "").strip()
        password = str(payload.get("password") or payload.get("contrasena") or "").strip()
        plan_name = str(payload.get("plan") or "MENSUAL").strip().upper()

        if not nombre:
            raise ValueError("Ingresa tu nombre")
        if not correo or "@" not in correo:
            raise ValueError("Ingresa un correo valido")
        if not dni:
            raise ValueError("Ingresa tu DNI")
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        if self.get_cliente_by_dni(dni):
            raise ValueError("Ya existe un cliente registrado con ese DNI")
        if self.get_cliente_by_email(correo):
            raise ValueError("Ya existe un cliente registrado con ese correo")

        def _fn(state: dict[str, Any]):
            plan = self._ensure_plan_for_client(state, plan_name)
            id_cliente = self._next_int_id_in_state(state, "clientes", "id_cliente")
            cliente = {
                "id_cliente": id_cliente,
                "id_usuario": f"SGCLI{id_cliente:03d}",
                "nombre": nombre,
                "correo": correo,
                "telefono": telefono,
                "dni": dni,
                "plan": plan_name,
                "promocion": str(payload.get("promocion") or "SIN PROMOCION").strip() or "SIN PROMOCION",
                "estado": "PENDIENTE_PAGO",
                "password_hash": hash_password(password),
            }
            membresia = {
                "id_membresia": self._next_int_id_in_state(state, "membresia", "id_membresia"),
                "fecha_inicio": "",
                "fecha_fin": "",
                "estado": "PENDIENTE_PAGO",
                "id_cliente": id_cliente,
                "id_pm": int(plan.get("id_pm")),
                "estado_pago": "PENDIENTE",
                "metodo_pago": str(payload.get("metodo_pago") or "pasarela"),
                "referencia_pago": str(payload.get("referencia_pago") or f"PAY-{id_cliente:03d}"),
            }
            state["clientes"].insert(0, cliente)
            state["membresia"].insert(0, membresia)
            return {"cliente": cliente, "membresia": membresia, "plan": plan}

        return self._mutate(_fn)

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(id_cliente)

        def _fn(state: dict[str, Any]):
            cliente = next((row for row in state.get("clientes", []) if int(row.get("id_cliente", 0) or 0) == id_cliente), None)
            if not cliente:
                raise ValueError("Cliente no encontrado")
            membresia = self._latest_membership_for_cliente(state, id_cliente)
            if not membresia:
                raise ValueError("Membresia no encontrada")
            cliente["estado"] = "EN_TRAMITE"
            membresia["estado"] = "EN_TRAMITE"
            membresia["estado_pago"] = "PAGADO"
            membresia["metodo_pago"] = str(payload.get("metodo_pago") or membresia.get("metodo_pago") or "pasarela")
            membresia["referencia_pago"] = str(payload.get("referencia_pago") or membresia.get("referencia_pago") or f"PAY-{id_cliente:03d}")
            membresia["fecha_pago"] = _today_iso()
            return {"cliente": cliente, "membresia": membresia}

        return self._mutate(_fn)

    def activar_membresia_cliente(self, id_cliente: int) -> dict[str, Any]:
        id_cliente = int(id_cliente)

        def _fn(state: dict[str, Any]):
            cliente = next((row for row in state.get("clientes", []) if int(row.get("id_cliente", 0) or 0) == id_cliente), None)
            if not cliente:
                raise ValueError("Cliente no encontrado")

            membresia = self._latest_membership_for_cliente(state, id_cliente)
            if not membresia:
                plan = self._ensure_plan_for_client(state, cliente.get("plan") or "MENSUAL")
                membresia = {
                    "id_membresia": self._next_int_id_in_state(state, "membresia", "id_membresia"),
                    "id_cliente": id_cliente,
                    "id_pm": int(plan.get("id_pm")),
                }
                state["membresia"].insert(0, membresia)
            else:
                plan = self.get_plan_membresia(int(membresia.get("id_pm", 0) or 0)) or self._ensure_plan_for_client(state, cliente.get("plan") or "MENSUAL")

            start = _today_iso()
            end = (datetime.fromisoformat(start) + timedelta(days=self._plan_duration_days(plan.get("nombre_plan", cliente.get("plan", "MENSUAL"))))).date().isoformat()
            cliente["estado"] = "ACTIVO"
            membresia["estado"] = "Activa"
            membresia["fecha_inicio"] = start
            membresia["fecha_fin"] = end
            membresia["estado_pago"] = membresia.get("estado_pago") or "PAGADO"
            return {"cliente": cliente, "membresia": membresia}

        return self._mutate(_fn)

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
                        "codigo_dia": str(row.get("codigo_dia") or self._day_code(day)).strip().upper(),
                        "dia": day,
                        "hora_inicio": hora_inicio,
                        "hora_fin": hora_fin,
                        "cupos": cupos,
                        "cupos_usados": max(0, int(row.get("cupos_usados") or 0)),
                        "activo": bool(row.get("activo", True)),
                    }
                )

        if not normalized:
            normalized = [dict(row) for row in self._seed()["horarios_servicio"]]

        return sorted(normalized, key=lambda row: (str(row.get("dia")), str(row.get("hora_inicio")), str(row.get("servicio"))))

    def _normalize_matricula_horario(self, row: dict[str, Any], fallback_index: int) -> dict[str, Any]:
        return {
            "id_matricula": int(row.get("id_matricula", 0) or fallback_index),
            "id_cliente": int(row.get("id_cliente", 0) or 0),
            "id_horario_servicio": int(row.get("id_horario_servicio", 0) or 0),
            "fecha_matricula": str(row.get("fecha_matricula") or _today_iso()),
            "estado": str(row.get("estado") or "ACTIVA").strip().upper(),
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

        return self._mutate(_fn)

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
        fecha = str(payload.get("fecha") or "").strip() or _today_iso()
        hora_entrada = str(payload.get("hora_entrada") or "").strip() or _now_time()
        id_usuario_registra = self._normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

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

        return self._mutate(_fn)

    def registrar_salida_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_asistencia = int(payload.get("id_asistencia", 0) or 0)
        hora_salida = str(payload.get("hora_salida") or "").strip() or _now_time()

        def _fn(state: dict[str, Any]):
            asistencia = next((row for row in state.get("asistencia", []) if int(row.get("id_asistencia", 0) or 0) == id_asistencia), None)
            if not asistencia:
                raise ValueError("Asistencia no encontrada")
            if not asistencia.get("hora_entrada"):
                asistencia["hora_entrada"] = asistencia.get("hora") or _now_time()
            asistencia["hora_salida"] = hora_salida
            return asistencia

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
            self._validate_service_schedule(state, current.get("servicio", "fitness"), current.get("fecha", _today_iso()), current.get("hora", _now_time()))
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

    def horarios_servicio(self) -> list[dict[str, Any]]:
        return self.state.get("horarios_servicio", [])

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

        item = {
            "id_horario_servicio": int(payload.get("id_horario_servicio", 0) or 0),
            "servicio": servicio,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "codigo_dia": str(payload.get("codigo_dia") or self._day_code(dia)).strip().upper(),
            "dia": dia,
            "cupos": max(1, int(payload.get("cupos") or 10)),
            "cupos_usados": 0,
            "activo": bool(payload.get("activo", True)),
        }

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

        return self._mutate(_fn)

    def delete_horario_servicio(self, id_horario_servicio: int) -> None:
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
                raise ValueError("Horario no encontrado")

        self._mutate(_fn)

    def matriculas_horario(self, id_cliente: int | None = None, dni: str | None = None) -> list[dict[str, Any]]:
        resolved_id = int(id_cliente or 0)
        if dni:
            cliente = self.get_cliente_by_dni(str(dni).strip())
            if not cliente:
                raise ValueError("Cliente no encontrado")
            resolved_id = int(cliente.get("id_cliente"))

        result = []
        for enrollment in self.state.get("matriculas_horario", []):
            if resolved_id and int(enrollment.get("id_cliente", 0) or 0) != resolved_id:
                continue
            schedule = self.get_horario_servicio(int(enrollment.get("id_horario_servicio", 0) or 0)) or {}
            cliente = self.get_cliente(int(enrollment.get("id_cliente", 0) or 0)) or {}
            result.append(
                {
                    **enrollment,
                    "cliente_nombre": cliente.get("nombre", ""),
                    "cliente_dni": cliente.get("dni", ""),
                    "cliente_codigo": cliente.get("id_usuario", ""),
                    "servicio": schedule.get("servicio", ""),
                    "codigo_dia": schedule.get("codigo_dia", ""),
                    "dia": schedule.get("dia", ""),
                    "hora_inicio": schedule.get("hora_inicio", ""),
                    "hora_fin": schedule.get("hora_fin", ""),
                    "asistencias": [
                        asistencia
                        for asistencia in self.state.get("asistencia", [])
                        if int(asistencia.get("id_matricula", 0) or 0) == int(enrollment.get("id_matricula", 0) or 0)
                    ],
                }
            )
        return sorted(result, key=lambda row: (str(row.get("dia")), str(row.get("hora_inicio"))))

    def matricular_cliente_horario(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("dni"):
            cliente = self.get_cliente_by_dni(str(payload.get("dni")).strip())
            if not cliente:
                raise ValueError("Cliente no encontrado")
            id_cliente = int(cliente["id_cliente"])
        else:
            id_cliente = self._parse_cliente_id(payload.get("id_cliente"))

        id_horario = int(payload.get("id_horario_servicio", 0) or 0)

        def _fn(state: dict[str, Any]):
            cliente = self.get_cliente(id_cliente)
            if not cliente:
                raise ValueError("Cliente no encontrado")
            if not self._active_membership_for_cliente(state, id_cliente):
                raise ValueError("Cliente sin membresia activa")
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
            duplicate = next(
                (
                    row
                    for row in state.get("matriculas_horario", [])
                    if int(row.get("id_cliente", 0) or 0) == id_cliente
                    and int(row.get("id_horario_servicio", 0) or 0) == id_horario
                    and str(row.get("estado") or "").upper() == "ACTIVA"
                ),
                None,
            )
            if duplicate:
                raise ValueError("El cliente ya esta matriculado en este horario")
            used = len(
                [
                    row
                    for row in state.get("matriculas_horario", [])
                    if int(row.get("id_horario_servicio", 0) or 0) == id_horario and str(row.get("estado") or "").upper() == "ACTIVA"
                ]
            )
            if used >= int(schedule.get("cupos", 1) or 1):
                raise ValueError("Horario sin cupos disponibles")
            enrollment = {
                "id_matricula": self._next_int_id_in_state(state, "matriculas_horario", "id_matricula"),
                "id_cliente": id_cliente,
                "id_horario_servicio": id_horario,
                "fecha_matricula": _today_iso(),
                "estado": "ACTIVA",
            }
            state.setdefault("matriculas_horario", []).insert(0, enrollment)
            self._recount_schedule_cupos(state)
            return self.matriculas_horario(id_cliente=id_cliente)[0]

        return self._mutate(_fn)

    def cancelar_matricula_horario(self, id_matricula: int) -> None:
        def _fn(state: dict[str, Any]):
            idx = next((i for i, row in enumerate(state.get("matriculas_horario", [])) if int(row.get("id_matricula", 0) or 0) == int(id_matricula)), -1)
            if idx < 0:
                raise ValueError("Matricula no encontrada")
            state["matriculas_horario"][idx]["estado"] = "CANCELADA"
            self._recount_schedule_cupos(state)

        self._mutate(_fn)

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

    def pedidos_tienda(self) -> list[dict[str, Any]]:
        return self.state.get("pedidos_tienda", [])

    def crear_pedido_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_items = payload.get("items") or []
        if not raw_items:
            raise ValueError("El pedido no tiene productos")

        def _fn(state: dict[str, Any]):
            state.setdefault("pedidos_tienda", [])
            state.setdefault("productos_tienda", [])

            items: list[dict[str, Any]] = []
            subtotal = 0.0

            for raw_item in raw_items:
                id_producto = int(raw_item.get("id_producto") or 0)
                cantidad = max(1, int(raw_item.get("cantidad") or 1))
                producto = next(
                    (
                        row
                        for row in state.get("productos_tienda", [])
                        if int(row.get("id_producto", 0) or 0) == id_producto
                    ),
                    None,
                )

                if not producto:
                    raise ValueError(f"Producto no encontrado: {id_producto}")
                if str(producto.get("estado") or "Disponible") != "Disponible":
                    raise ValueError(f"Producto no disponible: {producto.get('nombre_producto', id_producto)}")

                stock = int(producto.get("cantidad_stock") or 0)
                if stock < cantidad:
                    raise ValueError(f"Stock insuficiente para {producto.get('nombre_producto', 'producto')}")

                precio = float(producto.get("precio_venta") or 0)
                item_subtotal = round(precio * cantidad, 2)
                subtotal += item_subtotal

                producto["cantidad_stock"] = stock - cantidad
                if producto.get("id_item"):
                    linked_item = next(
                        (
                            row
                            for row in state.get("inventario", [])
                            if int(row.get("id_item", 0) or 0) == int(producto.get("id_item") or 0)
                        ),
                        None,
                    )
                    if linked_item:
                        linked_item["cantidad_stock"] = max(0, int(linked_item.get("cantidad_stock") or 0) - cantidad)

                items.append(
                    {
                        "id_producto": id_producto,
                        "nombre_producto": str(producto.get("nombre_producto") or "Producto"),
                        "cantidad": cantidad,
                        "precio_unitario": precio,
                        "subtotal": item_subtotal,
                    }
                )

            subtotal = round(subtotal, 2)
            igv = round(subtotal * 0.18, 2)
            total = round(subtotal + igv, 2)
            pedido = {
                "id_pedido": self._next_int_id_in_state(state, "pedidos_tienda", "id_pedido"),
                "id_cliente": int(payload.get("id_cliente") or 0) or None,
                "cliente_nombre": str(payload.get("cliente_nombre") or "Cliente"),
                "cliente_correo": str(payload.get("cliente_correo") or ""),
                "cliente_dni": str(payload.get("cliente_dni") or ""),
                "fecha_pedido": _now_iso(),
                "metodo_pago": str(payload.get("metodo_pago") or "tarjeta"),
                "referencia_pago": str(payload.get("referencia_pago") or f"PED-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "estado_pago": "PAGADO",
                "estado_pedido": "PENDIENTE",
                "subtotal": subtotal,
                "igv": igv,
                "total": total,
                "items": items,
            }
            state["pedidos_tienda"].insert(0, pedido)
            return pedido

        return self._mutate(_fn)
