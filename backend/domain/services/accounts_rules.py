"""Reglas de accounts sobre el agregado en memoria."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
from domain.services.rule_context import RuleContext
from domain.services.client_identifiers import parse_client_id
from typing import Any
from domain.validation import required_text, account_email, dni_number, phone_number
from domain.services.membership_lifecycle import normalize_membership_status, project_memberships


def user_role_prefix(role: str) -> str:
    return {"admin": "ADM", "trainer": "TRA", "staff": "STA"}.get(str(role or "").strip().lower(), "USR")


def internal_account_active(account: dict | None) -> bool:
    state = account.get("estado") if account else None
    return state is True or str(state or "").strip().upper() in {"ACTIVO", "ACTIVA"}



@dataclass(frozen=True)
class AccountsDependencies:
    ensure_membership_for_active_client: Callable


class AccountsRules:
    def __init__(self, context: RuleContext, dependencies: AccountsDependencies):
        self.context = context
        self.dependencies = dependencies

    def _user_role_prefix(self, rol: str) -> str:
        return user_role_prefix(rol)

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

    def _next_usuario_code(self, state: dict[str, Any]) -> int:
        numbers: list[int] = []
        for row in state.get("usuario", []):
            usuario_id = str(row.get("id_usuario") or "").strip().upper()
            match = re.match(r"^SG[A-Z]{2,3}(\d+)$", usuario_id)
            if match:
                numbers.append(int(match.group(1)))

        return max(max(numbers, default=0), int(state.get("_identity_floors", {}).get("usuario", 0))) + 1

    def _normalize_usuario_record(self, row: dict[str, Any]) -> dict[str, Any]:
        nombre = str(row.get("nombre") or ((str(row.get("nombres") or "") + " " + str(row.get("apellidos") or "")).strip()) or "").strip()
        correo = str(row.get("correo") or row.get("email") or "").strip()
        rol = str(row.get("rol") or "staff").strip().lower()
        prefix = self._user_role_prefix(rol)
        raw_id = str(row.get("id_usuario") or "").strip().upper()
        number_match = re.search(r"(\d+)$", raw_id)
        number = int(number_match.group(1)) if number_match else self._next_usuario_code({"usuario": [row]})
        raw_id = raw_id if re.fullmatch(r"SG[A-Z]{2,3}\d+", raw_id) else f"SG{prefix}{int(number):03d}"
        password_hash = str(row.get("password_hash") or "").strip()
        if not password_hash and row.get("password"):
            password_hash = self.context.passwords.hash(str(row.get("password") or ""))
        return {
            "id_usuario": raw_id,
            "nombre": nombre,
            "correo": correo,
            "telefono": str(row.get("telefono") or "").strip(),
            "dni": str(row.get("dni") or "").strip(),
            "rol": rol if rol in {"admin", "trainer", "staff"} else "staff",
            "estado": "ACTIVO" if internal_account_active({"estado": row.get("estado", "ACTIVO")}) else "INACTIVO",
            "password_hash": password_hash,
            "google_sub": str(row.get("google_sub") or ""),
        }

    def get_usuario(self, id_usuario: Any) -> dict[str, Any] | None:
        usuario_id = self._normalize_usuario_id(id_usuario)
        if not usuario_id:
            return None

        exact = next((u for u in self.context.state["usuario"] if self._normalize_usuario_id(u.get("id_usuario")) == usuario_id), None)
        if exact:
            return exact
        legacy = re.fullmatch(r"SGUS(\d+)", usuario_id)
        if legacy:
            matches = [u for u in self.context.state["usuario"]
                       if (number := re.search(r"(\d+)$", str(u.get("id_usuario") or "")))
                       and int(number.group(1)) == int(legacy.group(1))]
            if len(matches) == 1:
                return matches[0]
        return None

    def get_usuario_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = str(email or "").strip().lower()
        return next(
            (
                u
                for u in self.context.state["usuario"]
                if str(u.get("email") or u.get("correo") or "").strip().lower() == normalized_email
            ),
            None,
        )

    def usuarios(self) -> list[dict[str, Any]]:
        return self.context.state["usuario"]

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
            for row in self.context.state.get("usuario", [])
        ]

    def _change_users(self, fn):
        return self.context.change(fn)

    def upsert_usuario(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            rol = str(payload.get("rol") or "").strip().lower()
            if rol not in {"admin", "trainer", "staff"}:
                raise ValueError("Rol inválido")

            prefix = self._user_role_prefix(rol)
            raw_id = self._normalize_usuario_id(payload.get("id_usuario"))
            existing_by_id = self.get_usuario(raw_id) if raw_id else None
            if existing_by_id:
                item_id = existing_by_id["id_usuario"]
            elif raw_id and re.fullmatch(r"SG[A-Z]{2,3}\d+", raw_id):
                # Un código indicado al crear tampoco puede reutilizar la identidad numérica.
                number = int(re.search(r"(\d+)$", raw_id).group(1))
                if any(int(re.search(r"(\d+)$", str(row["id_usuario"])).group(1)) == number
                       for row in state.get("usuario", [])):
                    raise ValueError("El identificador de usuario ya está utilizado")
                item_id = raw_id
            else:
                item_id = f"SG{prefix}{self._next_usuario_code(state):03d}"

            nombre = required_text(payload.get("nombre"))
            correo = account_email(payload.get("correo"))
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
                "telefono": phone_number(payload.get("telefono")),
                "dni": dni_number(payload.get("dni")),
                "rol": rol,
                "estado": "ACTIVO" if internal_account_active({"estado": existing.get("estado", "ACTIVO")}) else "INACTIVO",
                "password_hash": self.context.passwords.hash(password) if password else str(existing.get("password_hash") or ""),
                "google_sub": str(existing.get("google_sub") or ""),
            }

            self._check_duplicate_accounts(state["usuario"], item, "id_usuario")

            if idx >= 0:
                state["usuario"][idx] = item
            else:
                state["usuario"].insert(0, item)
            return item

        return self._change_users(_fn)

    @staticmethod
    def _check_duplicate_accounts(accounts, item, identity):
        for account in accounts:
            if account.get(identity) == item.get(identity):
                continue
            if str(account.get("correo") or "").strip().lower() == item["correo"]:
                raise ValueError("Ya existe una cuenta con ese correo.")
            if item["dni"] and str(account.get("dni") or "").strip() == item["dni"]:
                raise ValueError("Ya existe una cuenta con ese DNI.")

    def delete_usuario(self, id_usuario: Any) -> None:
        usuario_id = self._normalize_usuario_id(id_usuario)

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            state["usuario"] = [u for u in state["usuario"] if self._normalize_usuario_id(u.get("id_usuario")) != usuario_id]

        self._change_users(_fn)

    def clientes(self) -> list[dict[str, Any]]:
        return self.context.state["clientes"]

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
            password_hash = self.context.passwords.hash(str(row.get("password") or ""))
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
            "google_sub": str(row.get("google_sub") or ""),
            "origen_registro": str(row.get("origen_registro") or ""),
            "fecha_registro": str(row.get("fecha_registro") or ""),
        }

    def clientes_normalized(self) -> list[dict[str, Any]]:
        state = project_memberships(self.context.state, self.context.today())
        latest_by_client = {}
        for membership in state.get("membresia", []):
            client_id = int(membership.get("id_cliente", 0) or 0)
            latest = latest_by_client.get(client_id)
            if latest is None or int(membership.get("id_membresia", 0) or 0) > int(latest.get("id_membresia", 0) or 0):
                latest_by_client[client_id] = membership
        result = []
        for row in state.get("clientes", []):
            membership = latest_by_client.get(int(row.get("id_cliente", 0) or 0), {})
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
                    "id_promocion": membership.get("id_promocion"),
                    "membership_status": normalize_membership_status(membership.get("estado") or row["estado"]),
                    "membership_start": membership.get("fecha_inicio", ""),
                    "membership_end": membership.get("fecha_fin", ""),
                    "payment_status": membership.get("estado_pago", ""),
                    "payment_reference": membership.get("referencia_pago", ""),
                    "monto_pago": membership.get("monto_pago"),
                    "origen_registro": row.get("origen_registro", ""),
                    "has_password": bool(row.get("password_hash")),
                }
            )
        return result

    def upsert_cliente(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
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
            elif id_usuario.upper().startswith("SGCLI"):
                item_id = parse_client_id(id_usuario)

            if item_id is None:
                item_id = self.context.next_int_id("clientes", "id_cliente")

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
                "nombre": required_text(payload.get("nombre")),
                "correo": account_email(payload.get("correo") or payload.get("email")),
                "telefono": phone_number(payload.get("telefono")),
                "dni": dni_number(payload.get("dni")),
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
            self._check_duplicate_accounts(state["clientes"], item, "id_cliente")
            if any(r.get('estado') == 'PENDIENTE' and (r['correo'] == item['correo'] or r['dni'] == item['dni'])
                   for r in state.get('preregistros', [])):
                raise ValueError('Existe un preregistro pendiente con esos datos. Espera la confirmación o caducidad del pago.')
            item["password_hash"] = self.context.passwords.hash(password) if password else str(existing.get("password_hash") or "")
            item["google_sub"] = str(existing.get("google_sub") or "")
            item["origen_registro"] = str(existing.get("origen_registro") or "") if existing else "ADMIN"
            item["fecha_registro"] = existing.get("fecha_registro") or self.context.today()
            if idx >= 0:
                state["clientes"][idx] = item
            else:
                state["clientes"].insert(0, item)
            self.dependencies.ensure_membership_for_active_client(state, item)
            return item

        return self.context.change(_fn)

    def get_cliente(self, id_cliente: int) -> dict[str, Any] | None:
        return next((c for c in self.context.state["clientes"] if int(c.get("id_cliente", 0)) == int(id_cliente)), None)

    def get_cliente_by_dni(self, dni: str) -> dict[str, Any] | None:
        return next((c for c in self.context.state["clientes"] if str(c.get("dni", "")) == str(dni)), None)

    def get_cliente_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = str(email or "").strip().lower()
        return next(
            (
                c
                for c in self.context.state["clientes"]
                if str(c.get("correo") or c.get("email") or "").strip().lower() == normalized
            ),
            None,
        )

    def get_account_by_google_sub(self, subject: str) -> tuple[str, dict[str, Any]] | None:
        if not subject:
            return None
        for kind in ("usuario", "clientes"):
            for account in self.context.state[kind]:
                if account.get("google_sub") == subject:
                    return kind, account
        return None

    def link_google_account(self, kind: str, account_id: str, subject: str) -> dict[str, Any]:
        if kind not in {"usuario", "clientes"} or not subject:
            raise ValueError("Identidad de Google inválida")

        def _fn(state: dict[str, Any]):
            for table in ("usuario", "clientes"):
                if any(row.get("google_sub") == subject for row in state[table]):
                    raise ValueError("La identidad de Google ya está vinculada. Inicia sesión nuevamente.")
            account = next((row for row in state[kind] if row.get("id_usuario") == account_id), None)
            if not account or account.get("google_sub"):
                raise ValueError("No se pudo vincular esta cuenta de Google")
            account["google_sub"] = subject
            return account

        return self.context.change(_fn)

    def authenticate_usuario_password(self, correo: str, password: str) -> dict[str, Any] | None:
        usuario = self.get_usuario_by_email(correo)
        if not usuario or not self.context.passwords.verify(password, str(usuario.get("password_hash") or "")):
            return None
        return usuario

    def authenticate_cliente_password(self, correo: str, password: str) -> dict[str, Any] | None:
        cliente = self.get_cliente_by_email(correo)
        if not cliente or not self.context.passwords.verify(password, str(cliente.get("password_hash") or "")):
            return None
        return cliente

    def delete_cliente(self, id_cliente: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            # Procesa esta operación.
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
            enrollment_ids = {int(row["id_matricula"]) for row in state.get("matriculas_horario", [])
                              if matches_id(row.get("id_cliente"))}
            state["rutina_progreso"] = [row for row in state.get("rutina_progreso", [])
                                        if int(row.get("id_matricula") or 0) not in enrollment_ids]
            state["matriculas_horario"] = [row for row in state.get("matriculas_horario", [])
                                           if not matches_id(row.get("id_cliente"))]

        self.context.change(_fn)
