"""Reglas de store sobre el agregado en memoria."""
from __future__ import annotations
from domain.validation import integer_quantity, nonnegative, required_text
from domain.errors import EntityNotFound

from datetime import datetime, timezone
from typing import Any
from domain.money import cents, order_totals
from domain.services.gym_values import TIPO_TIENDA, ESTADO_PAGO_PAGADO, ESTADO_PAGO_PENDIENTE, ESTADO_PEDIDO_CANCELADO, _pedido_pagado, _parse_utc, PedidoCanceladoConPagoError


from dataclasses import dataclass
from typing import Callable
from domain.services.rule_context import RuleContext


@dataclass(frozen=True)
class StoreDependencies:
    actualizar_estados_tienda: Callable
    es_item_tienda: Callable
    find_item_in_state: Callable
    next_n_activo: Callable


class StoreRules:
    def __init__(self, context: RuleContext, dependencies: StoreDependencies):
        self.context = context
        self.dependencies = dependencies

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
            "fecha_pedido": str(row.get("fecha_pedido") or self.context.now()),
            "metodo_pago": str(row.get("metodo_pago") or "tarjeta"),
            "referencia_pago": str(row.get("referencia_pago") or ""),
            "estado_pago": str(row.get("estado_pago") or "PAGADO"),
            "estado_pedido": str(row.get("estado_pedido") or "PENDIENTE"),
            "observacion_admin": str(row.get("observacion_admin") or ""),
            "fecha_actualizacion": str(row.get("fecha_actualizacion") or row.get("fecha_pedido") or self.context.now()),
            "subtotal": round(subtotal, 2),
            "igv": round(igv, 2),
            "total": round(total, 2),
            "items": items,
        }

    def productos_tienda(self) -> list[dict[str, Any]]:
        return self.context.state.get("productos_tienda", [])

    def get_producto_tienda(self, id_producto: int) -> dict[str, Any] | None:
        return next((p for p in self.context.state.get("productos_tienda", []) if int(p.get("id_producto", 0)) == int(id_producto)), None)

    def upsert_producto_tienda(self, payload: dict[str, Any], actor: Any = None) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            productos = state.setdefault("productos_tienda", [])
            producto = {**payload}
            producto_id = producto.get("id_producto")
            idx = -1
            if producto_id is not None:
                idx = next((i for i, row in enumerate(productos) if int(row.get("id_producto", 0)) == int(producto_id)), -1)
            if producto_id is None:
                producto_id = self.context.next_int_id_in_state(state, "productos_tienda", "id_producto")
            previo = productos[idx] if idx >= 0 else None
            producto["id_producto"] = int(producto_id)
            producto["unidad_venta"] = str(producto.get("unidad_venta") or "unidad")
            required_text(producto.get("nombre_producto"))
            producto["precio_venta"] = float(nonnegative(producto.get("precio_venta") or 0, "Precio"))
            producto["stock_minimo"] = integer_quantity(producto["stock_minimo"] if producto.get("stock_minimo") is not None else 0, "Stock mínimo")
            stock_solicitado = integer_quantity(producto.get("cantidad_stock", 0), "Stock")

            id_item = int(producto["id_item"]) if producto.get("id_item") else None
            if previo and previo.get("id_item"):
                # El vínculo producto-ítem es 1:1 y no cambia al editar.
                id_item = int(previo["id_item"])

            item = None
            if id_item:
                item = self.dependencies.find_item_in_state(state, id_item)
                if not item:
                    raise EntityNotFound("Item de almacén no encontrado")
                if not self.dependencies.es_item_tienda(item):
                    raise ValueError("Solo los ítems con Tipo 'Tienda' pueden venderse en la tienda")
                otro = next(
                    (
                        p for p in productos
                        if int(p.get("id_item") or 0) == id_item and int(p.get("id_producto", 0)) != producto["id_producto"]
                    ),
                    None,
                )
                if otro:
                    raise ValueError(f"El ítem ya está vinculado al producto {otro.get('nombre_producto') or otro.get('id_producto')}")
            elif previo is None:
                # Producto nuevo sin ítem: se crea su reserva en INVENTARIO, vacía.
                item = {
                    "id_item": self.context.next_int_id_in_state(state, "inventario", "id_item"),
                    "nombre_item": str(producto.get("nombre_producto") or "Sin nombre"),
                    "tipo": TIPO_TIENDA,
                    "cantidad_stock": 0,
                    "estado": "Disponible",
                    "n_activo": self.dependencies.next_n_activo(state),
                    "unidad_venta": producto["unidad_venta"],
                    "precio_venta": producto["precio_venta"],
                    "stock_minimo": producto["stock_minimo"],
                    "ubicacion": "Almacén",
                    "observaciones": "",
                }
                state["inventario"].insert(0, item)
                id_item = int(item["id_item"])
            producto["id_item"] = id_item

            if item:
                # Almacén -> precio de venta y unidad de venta para tienda.
                item["unidad_venta"] = producto["unidad_venta"]
                item["precio_venta"] = producto["precio_venta"]
                if not producto.get("nombre_producto"):
                    producto["nombre_producto"] = item.get("nombre_item", "Sin nombre")
            # El stock de la tienda solo se fija al crear el producto; después sube con reposiciones
            # desde INVENTARIO y baja con las ventas.
            producto["cantidad_stock"] = int(previo.get("cantidad_stock") or 0) if previo else stock_solicitado

            if idx >= 0:
                productos[idx] = producto
            else:
                productos.insert(0, producto)
            self.dependencies.actualizar_estados_tienda(state)
            return producto

        return self.context.change(_fn)

    def delete_producto_tienda(self, id_producto: int) -> None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            if "productos_tienda" in state:
                state["productos_tienda"] = [p for p in state["productos_tienda"] if int(p.get("id_producto", 0)) != int(id_producto)]

        self.context.change(_fn)

    def pedidos_tienda(self) -> list[dict[str, Any]]:
        return self.context.state.get("pedidos_tienda", [])

    def crear_pedido_tienda(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._crear_pedido_tienda(payload, pago_pendiente=False)

    def crear_pedido_tienda_pago_pendiente(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._crear_pedido_tienda(payload, pago_pendiente=True)

    def _crear_pedido_tienda(self, payload: dict[str, Any], pago_pendiente: bool) -> dict[str, Any]:
        raw_items = payload.get("items") or []
        if not raw_items:
            raise ValueError("El pedido no tiene productos")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            state.setdefault("pedidos_tienda", [])
            state.setdefault("productos_tienda", [])
            self.dependencies.actualizar_estados_tienda(state)

            # Valida el pedido completo antes de tocar el stock.
            lineas: list[tuple[dict[str, Any], int]] = []
            solicitado: dict[int, int] = {}
            for raw_item in raw_items:
                id_producto = int(raw_item.get("id_producto") or 0)
                cantidad = integer_quantity(raw_item.get("cantidad", 1), minimum=1)
                producto = next(
                    (
                        row
                        for row in state.get("productos_tienda", [])
                        if int(row.get("id_producto", 0) or 0) == id_producto
                    ),
                    None,
                )

                if not producto:
                    raise EntityNotFound(f"Producto no encontrado: {id_producto}")
                if str(producto.get("estado") or "Disponible") != "Disponible":
                    raise ValueError(f"Producto no disponible: {producto.get('nombre_producto', id_producto)}")

                solicitado[id_producto] = solicitado.get(id_producto, 0) + cantidad
                if int(producto.get("cantidad_stock") or 0) < solicitado[id_producto]:
                    raise ValueError(f"Stock insuficiente para {producto.get('nombre_producto', 'producto')}")
                lineas.append((producto, cantidad))

            id_pedido = self.context.next_int_id_in_state(state, "pedidos_tienda", "id_pedido")
            cliente_nombre = str(payload.get("cliente_nombre") or "Cliente")
            items: list[dict[str, Any]] = []
            subtotal_cents = 0

            for producto, cantidad in lineas:
                precio = float(producto.get("precio_venta") or 0)
                item_subtotal_cents = cents(precio) * cantidad
                item_subtotal = item_subtotal_cents / 100
                subtotal_cents += item_subtotal_cents

                # La venta solo descuenta el stock de la tienda; la reserva de INVENTARIO no cambia.
                producto["cantidad_stock"] = int(producto.get("cantidad_stock") or 0) - cantidad

                items.append(
                    {
                        "id_producto": int(producto.get("id_producto") or 0),
                        "nombre_producto": str(producto.get("nombre_producto") or "Producto"),
                        "cantidad": cantidad,
                        "precio_unitario": precio,
                        "subtotal": item_subtotal,
                    }
                )

            self.dependencies.actualizar_estados_tienda(state)
            totals = order_totals(subtotal_cents)
            ahora = self.context.now()
            pedido = {
                "id_pedido": id_pedido,
                "id_cliente": int(payload.get("id_cliente") or 0) or None,
                "cliente_nombre": cliente_nombre,
                "cliente_correo": str(payload.get("cliente_correo") or ""),
                "cliente_dni": str(payload.get("cliente_dni") or ""),
                "fecha_pedido": ahora,
                "creado_en": ahora,
                "metodo_pago": "tarjeta" if pago_pendiente else str(payload.get("metodo_pago") or "tarjeta"),
                # Con tarjeta la referencia es el session_id de Stripe: se registra después de crear la sesión.
                "referencia_pago": "" if pago_pendiente else str(payload.get("referencia_pago") or f"PED-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"),
                "estado_pago": ESTADO_PAGO_PENDIENTE if pago_pendiente else ESTADO_PAGO_PAGADO,
                "estado_pedido": "PENDIENTE",
                "observacion_admin": "",
                "fecha_actualizacion": ahora,
                **totals,
                "items": items,
            }
            state["pedidos_tienda"].insert(0, pedido)
            return pedido

        return self.context.change(_fn)

    def _devolver_stock_pedido(self, state: dict[str, Any], pedido: dict[str, Any]) -> None:
        for linea in pedido.get("items", []):
            producto = next(
                (
                    row
                    for row in state.get("productos_tienda", [])
                    if int(row.get("id_producto", 0) or 0) == int(linea.get("id_producto") or 0)
                ),
                None,
            )
            if producto:
                producto["cantidad_stock"] = int(producto.get("cantidad_stock") or 0) + max(1, int(linea.get("cantidad") or 1))
        self.dependencies.actualizar_estados_tienda(state)

    @staticmethod
    def _find_pedido_in_state(state: dict[str, Any], id_pedido: Any) -> dict[str, Any] | None:
        return next(
            (row for row in state.get("pedidos_tienda", []) if int(row.get("id_pedido", 0) or 0) == int(id_pedido)),
            None,
        )

    def get_pedido_tienda(self, id_pedido: int) -> dict[str, Any] | None:
        return self._find_pedido_in_state(self.context.state, id_pedido)

    def pedidos_pago_pendiente(self) -> list[dict[str, Any]]:
        return [
            dict(pedido)
            for pedido in self.context.state.get("pedidos_tienda", [])
            if not _pedido_pagado(pedido)
            and str(pedido.get("estado_pedido") or "").strip().upper() != ESTADO_PEDIDO_CANCELADO
        ]

    @staticmethod
    def minutos_desde_creacion(pedido: dict[str, Any]) -> float | None:
        creado = _parse_utc(pedido.get("creado_en"))
        if creado is None:
            return None
        return (datetime.now(timezone.utc) - creado).total_seconds() / 60

    def registrar_sesion_pago_pedido(self, id_pedido: int, session_id: str) -> dict[str, Any]:
        session_id = str(session_id or "").strip()
        if not session_id:
            raise ValueError("Sesión de pago inválida")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            pedido = self._find_pedido_in_state(state, id_pedido)
            if not pedido:
                raise EntityNotFound("Pedido no encontrado")
            if _pedido_pagado(pedido) or str(pedido.get("estado_pedido") or "").strip().upper() == ESTADO_PEDIDO_CANCELADO:
                raise ValueError("El pedido ya no está pendiente de pago")
            pedido["referencia_pago"] = session_id
            pedido["fecha_actualizacion"] = self.context.now()
            return pedido

        return self.context.change(_fn)

    def confirmar_pago_pedido_tienda(self, id_pedido: int, payload: dict[str, Any]) -> dict[str, Any]:
        id_pedido = int(id_pedido)
        amount = round(float(payload.get("monto_pago", 0) or 0), 2)
        payment_reference = str(payload.get("referencia_pago") or "").strip()
        if id_pedido <= 0:
            raise ValueError("Pedido de pago inválido")
        if amount <= 0:
            raise ValueError("Importe de pago inválido")
        if not payment_reference:
            raise ValueError("Referencia de pago inválida")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            pedido = self._find_pedido_in_state(state, id_pedido)
            if not pedido:
                raise EntityNotFound("Pedido no encontrado")

            expected_amount = round(float(pedido.get("total") or 0), 2)
            if expected_amount <= 0 or cents(expected_amount) != cents(amount):
                raise ValueError("El importe del pago no coincide con el pedido")

            current_reference = str(pedido.get("referencia_pago") or "").strip()
            if _pedido_pagado(pedido):
                if current_reference == payment_reference:
                    return pedido
                raise ValueError("El pedido ya tiene otro pago confirmado")
            if current_reference and current_reference != payment_reference:
                raise ValueError("La sesión de pago no corresponde a este pedido")
            if str(pedido.get("estado_pedido") or "").strip().upper() == ESTADO_PEDIDO_CANCELADO:
                raise PedidoCanceladoConPagoError(
                    f"El pedido #{id_pedido} estaba cancelado cuando llegó el pago; requiere reembolso"
                )

            pedido["estado_pago"] = ESTADO_PAGO_PAGADO
            pedido["metodo_pago"] = str(payload.get("metodo_pago") or "tarjeta")
            pedido["referencia_pago"] = payment_reference
            pedido["fecha_actualizacion"] = self.context.now()
            return pedido

        return self.context.change(_fn)

    def cancelar_pedido_pago_pendiente(self, id_pedido: int, observacion: str = "") -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            pedido = self._find_pedido_in_state(state, id_pedido)
            if not pedido:
                raise EntityNotFound("Pedido no encontrado")
            if _pedido_pagado(pedido):
                raise ValueError("El pedido ya fue pagado")
            if str(pedido.get("estado_pedido") or "").strip().upper() == ESTADO_PEDIDO_CANCELADO:
                return pedido
            self._devolver_stock_pedido(state, pedido)
            pedido["estado_pedido"] = ESTADO_PEDIDO_CANCELADO
            pedido["observacion_admin"] = str(observacion or "Pago no completado: pedido cancelado y stock devuelto")
            pedido["fecha_actualizacion"] = self.context.now()
            return pedido

        return self.context.change(_fn)

    def actualizar_pedido_tienda(self, id_pedido: int, payload: dict[str, Any], actor: Any = None) -> dict[str, Any]:
        estado = str(payload.get("estado_pedido") or "").strip().upper()
        if estado not in {"PENDIENTE", "CONFIRMADO", "ENTREGADO", "CANCELADO"}:
            raise ValueError("Estado de pedido invalido")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            pedido = next((row for row in state.get("pedidos_tienda", []) if int(row.get("id_pedido", 0) or 0) == int(id_pedido)), None)
            if not pedido:
                raise EntityNotFound("Pedido no encontrado")
            if estado in {"CONFIRMADO", "ENTREGADO"} and not _pedido_pagado(pedido):
                raise ValueError("No se puede confirmar ni entregar un pedido sin pago confirmado")
            actual = str(pedido.get("estado_pedido") or "").strip().upper()
            if actual == "CANCELADO" and estado != "CANCELADO":
                raise ValueError("Un pedido cancelado no puede cambiar de estado")
            if estado == "CANCELADO" and actual != "CANCELADO":
                if actual != "PENDIENTE":
                    raise ValueError("Solo se pueden cancelar pedidos en estado PENDIENTE")
                self._devolver_stock_pedido(state, pedido)
            pedido["estado_pedido"] = estado
            pedido["observacion_admin"] = str(payload.get("observacion_admin") or "")
            pedido["fecha_actualizacion"] = self.context.now()
            return pedido

        return self.context.change(_fn)
