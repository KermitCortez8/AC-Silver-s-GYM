"""Reglas de memberships sobre el agregado en memoria."""
from __future__ import annotations
from domain.validation import account_email, dni_number, phone_number
from domain.validation import nonnegative, required_text, date_range

import re
from domain.money import cents, discounted_price
from datetime import datetime, timedelta
from typing import Any
from domain.services.membership_lifecycle import membership_expired, normalize_membership_status


from dataclasses import dataclass
from typing import Callable
from domain.services.rule_context import RuleContext


@dataclass(frozen=True)
class MembershipsDependencies:
    get_account_by_google_sub: Callable
    get_cliente: Callable
    get_cliente_by_dni: Callable
    get_cliente_by_email: Callable
    get_usuario_by_email: Callable
    upsert_cliente: Callable


class MembershipsRules:
    def __init__(self, context: RuleContext, dependencies: MembershipsDependencies):
        self.context = context
        self.dependencies = dependencies

    def _active_membership_for_cliente(self, state: dict[str, Any], id_cliente: int) -> dict[str, Any] | None:
        today = self.context.today()
        for memb in state["membresia"]:
            if int(memb.get("id_cliente", 0)) != int(id_cliente):
                continue
            if normalize_membership_status(memb.get("estado")) != "ACTIVO":
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

    def _plan_duration_days(self, plan_name: str) -> int:
        normalized = str(plan_name or "").strip().upper()
        match = re.search(r"(\d+)", normalized)
        amount = int(match.group(1)) if match else 1

        if "ANUAL" in normalized or "AÑO" in normalized:
            return 365 * amount
        if "MES" in normalized:
            return 30 * amount
        return 30

    def _duration_days(self, plan: dict[str, Any]) -> int:
        value = str(plan.get("duracion") or "").strip().lower()
        match = re.fullmatch(r"(\d+)\s*(dias?|días?|mes(?:es)?|años?|anos?)", value)
        if not match:
            raise ValueError("La duración del plan debe indicar días, meses o años")
        amount = int(match.group(1))
        if amount <= 0:
            raise ValueError("La duración del plan debe ser mayor que cero")
        unit = match.group(2)
        return amount * (365 if unit.startswith(("año", "ano")) else 30 if unit.startswith("mes") else 1)

    def _normalize_promocion(self, row: dict[str, Any], fallback_id: int) -> dict[str, Any]:
        raw_plans = row.get("planes_aplicables") or []
        if isinstance(raw_plans, str):
            raw_plans = [part.strip() for part in raw_plans.split(",") if part.strip()]

        limite = row.get("limite_cupos")
        limite_cupos = int(limite) if limite is not None and str(limite).strip() != "" else None

        usos = row.get("usos_actuales")
        usos_actuales = max(0, int(usos or 0))

        return {
            "id_promocion": int(row.get("id_promocion") or fallback_id),
            "nombre": str(row.get("nombre") or "Promocion").strip(),
            "descripcion": str(row.get("descripcion") or ""),
            "tipo_descuento": str(row.get("tipo_descuento") or "porcentaje").strip().lower(),
            "valor_descuento": max(0.0, float(row.get("valor_descuento") or 0)),
            "fecha_inicio": str(row.get("fecha_inicio") or ""),
            "fecha_fin": str(row.get("fecha_fin") or ""),
            "icono_etiqueta": str(row.get("icono_etiqueta") or "🏷️").strip() or "🏷️",
            "palabra_clave": str(row.get("palabra_clave") or "").strip().upper(),
            "activo": bool(row.get("activo", True)),
            "planes_aplicables": [int(value) for value in raw_plans if str(value).strip().isdigit()],
            "limite_cupos": limite_cupos,
            "usos_actuales": usos_actuales,
        }

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

        raise ValueError(f"Plan de membresia no configurado en Supabase: {normalized}")

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

        # Editar o cargar un cliente no renueva ni activa su membresía anterior.
        latest = self._latest_membership_for_cliente(state, id_cliente)
        if latest:
            return latest

        plan = self._ensure_plan_for_client(state, cliente.get("plan") or "MENSUAL")
        start = self.context.today()
        end = (datetime.fromisoformat(start) + timedelta(days=self._duration_days(plan))).date().isoformat()
        membership = {
            "id_membresia": self.context.next_int_id_in_state(state, "membresia", "id_membresia"),
            "fecha_inicio": start,
            "fecha_fin": end,
            "estado": "EN_TRAMITE",
            "estado_pago": "PENDIENTE",
            "id_cliente": id_cliente,
            "id_pm": int(plan["id_pm"]),
        }
        state.setdefault("membresia", []).insert(0, membership)
        cliente["estado"] = "EN_TRAMITE"
        return membership

    def planes_membresia(self) -> list[dict[str, Any]]:
        return self.context.state.get("planes_membresia", [])

    def get_plan_membresia(self, id_pm: int) -> dict[str, Any] | None:
        return next((p for p in self.context.state.get("planes_membresia", []) if int(p.get("id_pm", 0)) == int(id_pm)), None)

    def upsert_plan_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            state.setdefault("planes_membresia", [])
            item = {**payload}
            item_id = item.get("id_pm")
            if item_id is None:
                item_id = self.context.next_int_id("planes_membresia", "id_pm")
            item["id_pm"] = int(item_id)
            item["nombre_plan"] = required_text(item.get("nombre_plan")).upper()
            item["duracion"] = str(item.get("duracion") or "30 dias").strip()
            self._duration_days(item)
            item["precio"] = cents(nonnegative(item.get("precio", 0), "Precio")) / 100
            item["activo"] = bool(item.get("activo", True))
            idx = next((i for i, row in enumerate(state["planes_membresia"]) if int(row.get("id_pm", 0)) == int(item_id)), -1)
            if idx >= 0:
                state["planes_membresia"][idx] = item
            else:
                state["planes_membresia"].insert(0, item)
            return item

        return self.context.change(_fn)

    def delete_plan_membresia(self, id_pm: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            if any(int(r.get('id_pm', 0)) == int(id_pm) for r in state.get('preregistros', [])):
                raise ValueError('No se puede eliminar un plan asociado a solicitudes de pago; puedes desactivarlo')
            if any(int(m.get("id_pm", 0)) == int(id_pm) for m in state.get("membresia", [])):
                raise ValueError("No se puede eliminar un plan usado por membresías")
            state["planes_membresia"] = [p for p in state.get("planes_membresia", []) if int(p.get("id_pm", 0)) != int(id_pm)]

        self.context.change(_fn)

    def _get_usos_promocion(self, state: dict[str, Any], promo: dict[str, Any]) -> int:
        promo_id = int(promo.get("id_promocion", 0) or 0)
        usos_registrados = int(promo.get("usos_actuales") or 0)
        if not promo_id:
            return usos_registrados

        clientes_promo: set[int] = set()
        for membership in state.get("membresia", []):
            if int(membership.get("id_promocion", 0) or 0) == promo_id:
                cliente_id = membership.get("id_cliente")
                if cliente_id:
                    clientes_promo.add(int(cliente_id))

        for cliente in state.get("clientes", []):
            cliente_promo_id = int(cliente.get("id_promocion", 0) or 0)
            cliente_promo = str(cliente.get("promocion", "")).strip().lower()
            if cliente_promo_id == promo_id or cliente_promo == f"promo-{promo_id}":
                cliente_id = cliente.get("id_cliente")
                if cliente_id:
                    clientes_promo.add(int(cliente_id))

        usos_membresia = sum(
            1
            for membership in state.get("membresia", [])
            if int(membership.get("id_promocion", 0) or 0) == promo_id
        )
        usos_calculados = len(clientes_promo) if clientes_promo else usos_membresia
        return max(usos_registrados, usos_calculados)

    def promociones(self) -> list[dict[str, Any]]:
        result = []
        for promo in self.context.state.get("promociones", []):
            item = dict(promo)
            calculated_usos = self._get_usos_promocion(self.context.state, promo)
            if calculated_usos != promo.get("usos_actuales"):
                promo["usos_actuales"] = calculated_usos
            item["usos_actuales"] = calculated_usos
            result.append(item)
        return result

    def upsert_promocion(self, payload: dict[str, Any]) -> dict[str, Any]:
        tipo = str(payload.get("tipo_descuento") or "porcentaje").strip().lower()
        if tipo not in {"porcentaje", "monto"}:
            raise ValueError("Tipo de descuento invalido")

        required_text(payload.get("nombre"))
        date_range(payload.get("fecha_inicio"), payload.get("fecha_fin"))
        valor = float(nonnegative(payload.get("valor_descuento", 0), "Descuento"))
        if tipo == "porcentaje" and valor > 100:
            raise ValueError("El porcentaje no puede ser mayor a 100")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            state.setdefault("promociones", [])
            item_id = int(payload.get("id_promocion") or 0)

            if item_id > 0:
                existing_promo = next(
                    (
                        promo
                        for promo in state["promociones"]
                        if int(promo.get("id_promocion", 0)) == item_id
                    ),
                    None,
                )
                if existing_promo:
                    today = self.context.today()
                    limite = existing_promo.get("limite_cupos")
                    usos = self._get_usos_promocion(state, existing_promo)
                    valid_until = str(existing_promo.get("fecha_fin") or "")
                    is_finished = (
                        (limite is not None and limite > 0 and usos >= limite)
                        or (valid_until and valid_until < today)
                    )
                    if is_finished:
                        raise ValueError(
                            "Una promoción terminada no se puede editar, sólo se puede eliminar."
                        )

            item = self._normalize_promocion(
                {**payload, "tipo_descuento": tipo, "valor_descuento": valor},
                self.context.next_int_id_in_state(state, "promociones", "id_promocion"),
            )
            item_id = int(payload.get("id_promocion") or item["id_promocion"])
            item["id_promocion"] = item_id

            if item.get("activo", True):
                start_1 = str(item.get("fecha_inicio") or "")
                end_1 = str(item.get("fecha_fin") or "")
                plans_1 = item.get("planes_aplicables") or []
                today = self.context.today()

                for existing in state["promociones"]:
                    if int(existing.get("id_promocion", 0)) == item_id:
                        continue
                    if not existing.get("activo", True):
                        continue

                    limite = existing.get("limite_cupos")
                    usos = self._get_usos_promocion(state, existing)
                    end_2 = str(existing.get("fecha_fin") or "")
                    if (
                        (limite is not None and limite > 0 and usos >= limite)
                        or (end_2 and end_2 < today)
                    ):
                        continue

                    start_2 = str(existing.get("fecha_inicio") or "")
                    date_overlap = True
                    if end_2 and start_1 and start_1 > end_2:
                        date_overlap = False
                    if end_1 and start_2 and start_2 > end_1:
                        date_overlap = False
                    if not date_overlap:
                        continue

                    plans_2 = existing.get("planes_aplicables") or []
                    plan_overlap = (
                        not plans_1
                        or not plans_2
                        or bool(set(plans_1) & set(plans_2))
                    )
                    if plan_overlap:
                        raise ValueError(
                            "Ya existe una promoción vigente para uno o más de estos planes "
                            "en ese rango de fechas."
                        )

            idx = next(
                (
                    i
                    for i, row in enumerate(state["promociones"])
                    if int(row.get("id_promocion", 0)) == item_id
                ),
                -1,
            )
            if idx >= 0:
                state["promociones"][idx] = item
            else:
                state["promociones"].insert(0, item)
            return item

        return self.context.change(_fn)

    def delete_promocion(self, id_promocion: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            before = len(state.get("promociones", []))
            state["promociones"] = [
                row
                for row in state.get("promociones", [])
                if int(row.get("id_promocion", 0)) != int(id_promocion)
            ]
            if len(state["promociones"]) == before:
                raise ValueError("Promocion no encontrada")

        self.context.change(_fn)

    def get_promocion_vigente_para_plan(
        self,
        state: dict[str, Any],
        id_pm: int,
    ) -> dict[str, Any] | None:
        today = self.context.today()
        for promo in state.get("promociones", []):
            if not promo.get("activo", True):
                continue

            limite = promo.get("limite_cupos")
            usos = self._get_usos_promocion(state, promo)
            if limite is not None and limite > 0 and usos >= limite:
                continue

            fecha_inicio = str(promo.get("fecha_inicio") or "")
            if fecha_inicio and fecha_inicio > today:
                continue

            fecha_fin = str(promo.get("fecha_fin") or "")
            if fecha_fin and fecha_fin < today:
                continue

            planes = promo.get("planes_aplicables") or []
            if not planes or int(id_pm) in planes:
                return promo

        return None

    def promociones_vigentes_publicas(self) -> list[dict[str, Any]]:
        today = self.context.today()
        result = []

        for promo in self.context.state.get("promociones", []):
            if not promo.get("activo", True):
                continue

            limite = promo.get("limite_cupos")
            usos = self._get_usos_promocion(self.context.state, promo)
            if limite is not None and limite > 0 and usos >= limite:
                continue

            fecha_inicio = str(promo.get("fecha_inicio") or "")
            if fecha_inicio and fecha_inicio > today:
                continue

            fecha_fin = str(promo.get("fecha_fin") or "")
            if fecha_fin and fecha_fin < today:
                continue

            result.append(
                {
                    "id_promocion": int(promo.get("id_promocion") or 0),
                    "nombre": str(promo.get("nombre") or "Promoción"),
                    "tipo_descuento": str(promo.get("tipo_descuento") or "porcentaje"),
                    "valor_descuento": float(promo.get("valor_descuento") or 0),
                    "icono_etiqueta": str(promo.get("icono_etiqueta") or "🏷️"),
                    "palabra_clave": str(promo.get("palabra_clave") or ""),
                    "planes_aplicables": [int(x) for x in (promo.get("planes_aplicables") or [])],
                    "limite_cupos": promo.get("limite_cupos"),
                    "usos_actuales": usos,
                }
            )

        return result

    def _apply_promocion_discount(
        self,
        state: dict[str, Any],
        id_pm: int,
        id_promocion: int | None,
    ) -> float:
        plan = next(
            (
                plan
                for plan in state.get("planes_membresia", [])
                if int(plan.get("id_pm", 0)) == int(id_pm)
            ),
            None,
        )
        if not plan:
            return 0.0

        precio_base = float(plan.get("precio", 0) or 0)
        if not id_promocion:
            return precio_base

        promocion = next(
            (
                promo
                for promo in state.get("promociones", [])
                if int(promo.get("id_promocion", 0)) == int(id_promocion)
            ),
            None,
        )
        if not promocion or not promocion.get("activo", True):
            return precio_base

        limite = promocion.get("limite_cupos")
        usos = self._get_usos_promocion(state, promocion)
        if limite is not None and limite > 0 and usos >= limite:
            return precio_base

        today = self.context.today()
        fecha_inicio = str(promocion.get("fecha_inicio") or "")
        if fecha_inicio and fecha_inicio > today:
            return precio_base

        fecha_fin = str(promocion.get("fecha_fin") or "")
        if fecha_fin and fecha_fin < today:
            return precio_base

        planes_aplicables = promocion.get("planes_aplicables") or []
        if planes_aplicables and int(id_pm) not in planes_aplicables:
            return precio_base

        valor = float(promocion.get("valor_descuento") or 0)
        tipo = str(promocion.get("tipo_descuento") or "porcentaje").strip().lower()

        return discounted_price(precio_base, valor, tipo)

    def _increment_promocion_usos(
        self,
        state: dict[str, Any],
        id_promocion: int | None,
    ) -> None:
        if not id_promocion:
            return

        promocion = next(
            (
                promo
                for promo in state.get("promociones", [])
                if int(promo.get("id_promocion", 0)) == int(id_promocion)
            ),
            None,
        )
        if promocion:
            usos = int(promocion.get("usos_actuales") or 0) + 1
            promocion["usos_actuales"] = usos

    def membresias(self) -> list[dict[str, Any]]:
        return [{**m, "estado": normalize_membership_status(m.get("estado"))} for m in self.context.state["membresia"]]

    def membresias_por_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return [m for m in self.membresias() if int(m.get("id_cliente", 0)) == int(id_cliente)]

    def crear_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(payload.get("id_cliente", 0))
        id_pm = int(payload.get("id_pm", 0))
        if not self.dependencies.get_cliente(id_cliente):
            raise ValueError("Cliente no encontrado")
        if not self.get_plan_membresia(id_pm):
            raise ValueError("Plan de membresía no encontrado")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = {**payload}
            id_promocion = int(item.get("id_promocion") or 0) or None
            item_id = item.get("id_membresia")
            if item_id is None:
                item_id = self.context.next_int_id("membresia", "id_membresia")

            existing = next((row for row in state["membresia"]
                             if int(row.get("id_membresia", 0)) == int(item_id)), None)
            if existing:
                if int(existing.get("id_cliente", 0)) != id_cliente:
                    raise ValueError("La membresía pertenece a otro cliente")
                if (str(existing.get("estado_pago") or "").strip().upper() == "PAGADO"
                        or normalize_membership_status(existing.get("estado")) != "EN_TRAMITE"):
                    raise ValueError("No puedes editar una membresía confirmada; registra una nueva para renovar")

            item["id_membresia"] = int(item_id)
            item["id_cliente"] = id_cliente
            item["id_pm"] = id_pm
            item["id_promocion"] = id_promocion
            item["fecha_inicio"] = ""
            item["fecha_fin"] = ""
            item["estado"] = "EN_TRAMITE"
            item["monto_pago"] = self._apply_promocion_discount(state, id_pm, id_promocion)
            item["estado_pago"] = "PENDIENTE"
            item["metodo_pago"] = str(item.get("metodo_pago") or "stripe")
            item["referencia_pago"] = ""
            item["fecha_pago"] = ""

            idx = next(
                (
                    i
                    for i, row in enumerate(state["membresia"])
                    if int(row.get("id_membresia", 0)) == int(item_id)
                ),
                -1,
            )

            if idx >= 0:
                state["membresia"][idx] = item
            else:
                # Una nueva membresía requiere pago y activación explícitos.
                item.update(
                    estado="EN_TRAMITE", estado_pago="PENDIENTE",
                    fecha_inicio="", fecha_fin="", fecha_pago="",
                    referencia_pago="",
                )
                if id_promocion:
                    self._increment_promocion_usos(state, id_promocion)
                state["membresia"].insert(0, item)

            return item

        return self.context.change(_fn)

    def _calcular_monto_con_descuento(
        self,
        id_pm: int,
        id_promocion: int | None,
    ) -> float:
        return self._apply_promocion_discount(self.context.state, id_pm, id_promocion)

    def registrar_cliente_con_membresia(self, payload: dict[str, Any]) -> dict[str, Any]:
        cliente_payload = payload["cliente"]
        id_pm = int(payload["id_pm"])
        fecha_inicio = payload["fecha_inicio"]
        fecha_fin = payload["fecha_fin"]
        id_promocion = int(payload.get("id_promocion") or 0) or None

        cliente = self.dependencies.upsert_cliente(cliente_payload)
        monto_pago = self._calcular_monto_con_descuento(id_pm, id_promocion)
        membresia = self.crear_membresia(
            {
                "id_cliente": int(cliente["id_cliente"]),
                "id_pm": id_pm,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "estado": "EN_TRAMITE",
                "id_promocion": id_promocion,
                "monto_pago": monto_pago,
                "estado_pago": "PENDIENTE",
            }
        )
        return {"cliente": cliente, "membresia": membresia}

    def registrar_cliente_publico(
        self,
        payload: dict[str, Any],
        *,
        origen_registro: str = "PUBLICO",
    ) -> dict[str, Any]:
        nombre = str(payload.get("nombre") or "").strip()
        correo = account_email(payload.get("correo"))
        telefono = phone_number(payload.get("telefono"), required=origen_registro == "PUBLICO")
        dni = dni_number(payload.get("dni"), required=True)
        password = str(payload.get("password") or payload.get("contrasena") or "").strip()
        plan_name = str(payload.get("plan") or "MENSUAL").strip().upper()
        # Este valor lo incorpora ClientsService después de verificar la credencial.
        google_sub = str(payload.get("google_sub") or "")

        if not nombre:
            raise ValueError("Ingresa tu nombre")
        if not google_sub and len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        if any(r.get('estado') == 'PENDIENTE' and (r['correo'] == correo or r['dni'] == dni)
               for r in self.context.state.get('preregistros', [])):
            raise ValueError('Existe un preregistro pendiente con esos datos. Completa o espera la caducidad del pago.')
        if self.dependencies.get_cliente_by_dni(dni):
            raise ValueError("Ya existe un cliente registrado con ese DNI")
        if self.dependencies.get_cliente_by_email(correo):
            raise ValueError("Ya existe un cliente registrado con ese correo")
        if self.dependencies.get_usuario_by_email(correo):
            raise ValueError("Ya existe una cuenta con ese correo. Inicia sesión para continuar.")
        if google_sub and self.dependencies.get_account_by_google_sub(google_sub):
            raise ValueError("Ya existe una cuenta con esta identidad de Google. Inicia sesión.")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            plan = self._ensure_plan_for_client(state, plan_name)
            id_cliente = self.context.next_int_id_in_state(state, "clientes", "id_cliente")
            id_pm = int(plan.get("id_pm"))

            promo_active = self.get_promocion_vigente_para_plan(state, id_pm)
            if origen_registro == "ADMIN":
                selected_id = int(payload.get("id_promocion") or 0)
                if selected_id:
                    promo_active = next(
                        (
                            promo
                            for promo in state.get("promociones", [])
                            if int(promo.get("id_promocion", 0)) == selected_id
                        ),
                        None,
                    )
                    valid_promos = self.promociones_vigentes_publicas()
                    if not any(
                        int(promo["id_promocion"]) == selected_id
                        and (
                            not promo["planes_aplicables"]
                            or id_pm in promo["planes_aplicables"]
                        )
                        for promo in valid_promos
                    ):
                        raise ValueError(
                            "La promoción seleccionada no está disponible para este plan"
                        )
                else:
                    promo_active = None

            id_promocion = (
                int(promo_active.get("id_promocion"))
                if promo_active
                else None
            )
            monto_final = self._apply_promocion_discount(
                state,
                id_pm,
                id_promocion,
            )

            cliente = {
                "id_cliente": id_cliente,
                "id_usuario": f"SGCLI{id_cliente:03d}",
                "nombre": nombre,
                "correo": correo,
                "telefono": telefono,
                "dni": dni,
                "plan": plan_name,
                "promocion": str(
                    promo_active.get("nombre")
                    if promo_active
                    else (payload.get("promocion") or "SIN PROMOCION")
                ).strip()
                or "SIN PROMOCION",
                "estado": "EN_TRAMITE",
                "password_hash": self.context.passwords.hash(password),
                "google_sub": google_sub,
                "origen_registro": origen_registro,
            }

            membresia = {
                "id_membresia": self.context.next_int_id_in_state(
                    state,
                    "membresia",
                    "id_membresia",
                ),
                "fecha_inicio": "",
                "fecha_fin": "",
                "estado": "EN_TRAMITE",
                "id_cliente": id_cliente,
                "id_pm": id_pm,
                "id_promocion": id_promocion,
                "monto_pago": monto_final,
                "estado_pago": "PENDIENTE",
                "metodo_pago": "stripe",
                "referencia_pago": "",
            }

            if id_promocion:
                self._increment_promocion_usos(state, id_promocion)

            state["clientes"].insert(0, cliente)
            state["membresia"].insert(0, membresia)

            return {
                "cliente": cliente,
                "membresia": membresia,
                "plan": plan,
            }

        return self.context.change(_fn)

    def reserve_public_quote(self, plan_name):
        """Reserva una promoción temporalmente sin crear un cliente ni una membresía."""
        state = self.context.state
        plan = self._ensure_plan_for_client(state, plan_name)
        if not plan.get("activo", True):
            raise ValueError("El plan seleccionado ya no está disponible")
        promo = self.get_promocion_vigente_para_plan(state, int(plan['id_pm']))
        promo_id = int(promo['id_promocion']) if promo else None
        amount = self._apply_promocion_discount(state, int(plan['id_pm']), promo_id)
        if cents(amount) <= 0:
            raise ValueError("El importe del preregistro debe ser mayor que cero")
        self._increment_promocion_usos(state, promo_id)
        return dict(plan), promo_id, amount

    def confirmar_pago_cliente_publico(self, id_cliente: int, payload: dict[str, Any]) -> dict[str, Any]:
        id_cliente = int(id_cliente)
        id_membresia = int(payload.get("id_membresia", 0) or 0)
        amount = float(payload.get("monto_pago", 0) or 0)
        payment_reference = str(payload.get("referencia_pago") or "").strip()
        if id_membresia <= 0:
            raise ValueError("Membresía de pago inválida")
        if amount <= 0:
            raise ValueError("Importe de pago inválido")
        if not payment_reference:
            raise ValueError("Referencia de pago inválida")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            cliente = next((row for row in state.get("clientes", []) if int(row.get("id_cliente", 0) or 0) == id_cliente), None)
            if not cliente:
                raise ValueError("Cliente no encontrado")
            membresia = next(
                (
                    row
                    for row in state.get("membresia", [])
                    if int(row.get("id_cliente", 0) or 0) == id_cliente
                    and int(row.get("id_membresia", 0) or 0) == id_membresia
                ),
                None,
            )
            if not membresia:
                raise ValueError("Membresia no encontrada")

            saved_amount = membresia.get("monto_pago")
            if saved_amount is None:
                plan = next(
                    (
                        row
                        for row in state.get("planes_membresia", [])
                        if int(row.get("id_pm", 0) or 0) == int(membresia.get("id_pm", 0) or 0)
                    ),
                    None,
                )
                saved_amount = (plan or {}).get("precio", 0)
            expected_amount = float(saved_amount or 0)
            if expected_amount <= 0 or cents(expected_amount) != cents(amount):
                raise ValueError("El importe del pago no coincide con la membresía")

            current_payment_status = str(membresia.get("estado_pago") or "").strip().upper()
            current_reference = str(membresia.get("referencia_pago") or "").strip()
            latest_membership = self._latest_membership_for_cliente(state, id_cliente)
            if current_payment_status == "PAGADO":
                if current_reference == payment_reference:
                    if (
                        latest_membership is membresia
                        and str(membresia.get("estado") or "").strip().upper() == "EN_TRAMITE"
                        and str(cliente.get("estado") or "").strip().upper() not in {"ACTIVO", "ACTIVA"}
                    ):
                        cliente["estado"] = "EN_TRAMITE"
                    return {"cliente": cliente, "membresia": membresia}
                raise ValueError("La membresía ya tiene otro pago confirmado")

            if latest_membership is membresia:
                cliente["estado"] = "EN_TRAMITE"
            membresia["estado"] = "EN_TRAMITE"
            membresia["estado_pago"] = "PAGADO"
            membresia["metodo_pago"] = str(payload.get("metodo_pago") or membresia.get("metodo_pago") or "pasarela")
            membresia["referencia_pago"] = payment_reference
            membresia["monto_pago"] = expected_amount
            membresia["fecha_pago"] = self.context.today()
            return {"cliente": cliente, "membresia": membresia}

        return self.context.change(_fn)

    def confirmar_pago_manual_cliente(self, id_cliente: int) -> dict[str, Any]:
        """Registra el cobro en caja; la activación sigue siendo independiente."""
        id_cliente = int(id_cliente)

        def _fn(state: dict[str, Any]):
            cliente = next((row for row in state.get("clientes", []) if int(row.get("id_cliente", 0) or 0) == id_cliente), None)
            if not cliente:
                raise ValueError("Cliente no encontrado")
            membresia = self._latest_membership_for_cliente(state, id_cliente)
            if not membresia:
                raise ValueError("Membresía no encontrada")
            if membership_expired(membresia, self.context.today()):
                raise ValueError("La membresía está vencida. Registra una nueva membresía para renovar el acceso.")
            if str(membresia.get("estado_pago") or "").strip().upper() == "PAGADO":
                return {"cliente": cliente, "membresia": membresia}
            amount = float(membresia.get("monto_pago", 0) or 0)
            if amount <= 0:
                raise ValueError("El importe del pago debe ser mayor que cero")
            membresia.update(
                estado="EN_TRAMITE", estado_pago="PAGADO", metodo_pago="efectivo",
                referencia_pago=f"manual:{membresia['id_membresia']}",
                fecha_pago=self.context.today(),
            )
            # El cobro de una renovación no desbloquea una cuenta vencida.
            if str(cliente.get("estado") or "").strip().upper() != "VENCIDA":
                cliente["estado"] = "EN_TRAMITE"
            return {"cliente": cliente, "membresia": membresia}

        return self.context.change(_fn)

    def activar_membresia_cliente(self, id_cliente: int) -> dict[str, Any]:
        self.context.expire_memberships()
        id_cliente = int(id_cliente)

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            cliente = next((row for row in state.get("clientes", []) if int(row.get("id_cliente", 0) or 0) == id_cliente), None)
            if not cliente:
                raise ValueError("Cliente no encontrado")

            membresia = self._latest_membership_for_cliente(state, id_cliente)
            if not membresia:
                raise ValueError("Membresia no encontrada")
            if membership_expired(membresia, self.context.today()):
                raise ValueError("La membresía está vencida. Registra una nueva membresía y confirma su pago para renovar el acceso.")
            if str(membresia.get("estado_pago") or "").strip().upper() != "PAGADO":
                raise ValueError("No se puede activar una membresía sin pago confirmado")
            if str(membresia.get("estado") or "").strip().upper() in {"ACTIVA", "ACTIVO"}:
                cliente["estado"] = "ACTIVO"
                membresia["estado"] = "ACTIVO"
                return {"cliente": cliente, "membresia": membresia}

            plan = self.get_plan_membresia(int(membresia.get("id_pm", 0) or 0)) or self._ensure_plan_for_client(state, cliente.get("plan") or "MENSUAL")

            start = self.context.today()
            end = (datetime.fromisoformat(start) + timedelta(days=self._duration_days(plan))).date().isoformat()
            cliente["estado"] = "ACTIVO"
            membresia["estado"] = "ACTIVO"
            membresia["fecha_inicio"] = start
            membresia["fecha_fin"] = end
            membresia["estado_pago"] = membresia.get("estado_pago") or "PAGADO"
            return {"cliente": cliente, "membresia": membresia}

        return self.context.change(_fn)
