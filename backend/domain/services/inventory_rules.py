"""Reglas de inventory sobre el agregado en memoria."""
from __future__ import annotations
from domain.errors import EntityNotFound
from domain.validation import nonnegative, required_text, integer_quantity

from typing import Any
from domain.services.gym_values import TIPO_TIENDA, ESTADO_DESCONTINUADO, ESTADO_DISPONIBLE, ESTADO_STOCK_BAJO, ESTADO_AGOTADO, DESTINO_TIENDA, DESTINO_VENTA, _MOVIMIENTO_PEDIDO


from dataclasses import dataclass
from typing import Callable
from domain.services.rule_context import RuleContext


@dataclass(frozen=True)
class InventoryDependencies:
    normalize_usuario_id: Callable
    get_usuario: Callable


class InventoryRules:
    def __init__(self, context: RuleContext, dependencies: InventoryDependencies):
        self.context = context
        self.dependencies = dependencies

    def inventario(self) -> list[dict[str, Any]]:
        return self.context.state["inventario"]

    def get_item_inventario(self, id_item: int) -> dict[str, Any] | None:
        return next((i for i in self.context.state["inventario"] if int(i.get("id_item", 0)) == int(id_item)), None)

    @staticmethod
    def _es_item_tienda(item: dict[str, Any] | None) -> bool:
        return bool(item) and str(item.get("tipo") or "").strip().lower() == TIPO_TIENDA.lower()

    @staticmethod
    def _find_item_in_state(state: dict[str, Any], id_item: Any) -> dict[str, Any] | None:
        if not id_item:
            return None
        return next((i for i in state.get("inventario", []) if int(i.get("id_item", 0) or 0) == int(id_item)), None)

    @staticmethod
    def _next_n_activo(state: dict[str, Any]) -> int:
        return max((int(i.get("n_activo") or 0) for i in state.get("inventario", [])), default=0) + 1

    def _actor_usuario_id(self, actor: Any) -> str | None:
        usuario = self.dependencies.get_usuario(actor) if actor else None
        return self.dependencies.normalize_usuario_id(usuario.get("id_usuario")) if usuario else None

    def _aplicar_movimiento(
        self,
        state: dict[str, Any],
        item: dict[str, Any],
        tipo: str,
        cantidad: int,
        descripcion: str,
        id_usuario: str | None = None,
        fecha: str = "",
        destino: str | None = None,
    ) -> dict[str, Any]:
        tipo = str(tipo or "").lower()
        if tipo not in {"entrada", "salida", "ajuste"}:
            raise ValueError("Tipo de movimiento inválido")
        cantidad = integer_quantity(cantidad, minimum=1)
        stock_actual = int(item.get("cantidad_stock", 0) or 0)
        if tipo == "entrada":
            nuevo_stock = stock_actual + cantidad
        elif tipo == "salida":
            if stock_actual < cantidad:
                raise ValueError(f"Stock insuficiente para {item.get('nombre_item') or 'el ítem'}")
            nuevo_stock = stock_actual - cantidad
        else:
            nuevo_stock = cantidad

        item["cantidad_stock"] = nuevo_stock
        mov = {
            "id_mov": self.context.next_int_id_in_state(state, "mov_inv", "id_mov"),
            "id_item": int(item["id_item"]),
            "id_usuario": id_usuario,
            "tipo_movimiento": tipo,
            "fecha_movimiento": self.context.safe_date(fecha),
            "descripcion": descripcion,
            "cantidad": cantidad,
            "destino": destino if tipo == "salida" else None,
        }
        state["mov_inv"].insert(0, mov)
        return mov

    @staticmethod
    def _producto_de_item(state: dict[str, Any], id_item: Any) -> dict[str, Any] | None:
        if not id_item:
            return None
        return next((p for p in state.get("productos_tienda", []) if int(p.get("id_item") or 0) == int(id_item)), None)

    @staticmethod
    def _normalizar_destino(tipo: str, destino: Any) -> str | None:
        valor = str(destino or "").strip().upper()
        if tipo != "salida" or not valor:
            return None
        if valor != DESTINO_TIENDA:
            raise ValueError("Destino inválido: una salida solo puede tener destino TIENDA")
        return valor

    def _actualizar_estados_tienda(self, state: dict[str, Any]) -> None:
        self._actualizar_estados_items_tienda(state)
        for producto in state.get("productos_tienda", []):
            stock = int(producto.get("cantidad_stock") or 0)
            if producto.get("id_item"):
                item = self._find_item_in_state(state, producto["id_item"])
                vendible = (
                    item is not None
                    and self._es_item_tienda(item)
                    and str(item.get("estado") or "") != ESTADO_DESCONTINUADO
                    and float(producto.get("precio_venta") or 0) > 0
                )
                if not vendible:
                    producto["estado"] = "Descatalogado"
                    continue
            producto["estado"] = "Disponible" if stock > 0 else "Agotado"

    def _actualizar_estados_items_tienda(self, state: dict[str, Any]) -> None:
        # Cada ítem usa su propio stock mínimo; el del producto solo aplica al stock de la tienda.
        for item in state.get("inventario", []):
            if not self._es_item_tienda(item) or str(item.get("estado") or "") == ESTADO_DESCONTINUADO:
                continue
            stock = int(item.get("cantidad_stock", 0) or 0)
            if stock <= 0:
                item["estado"] = ESTADO_AGOTADO
            elif stock <= int(item.get("stock_minimo") or 0):
                item["estado"] = ESTADO_STOCK_BAJO
            else:
                item["estado"] = ESTADO_DISPONIBLE

    def _crear_producto_para_item(self, state: dict[str, Any], item: dict[str, Any]) -> None:
        productos = state.setdefault("productos_tienda", [])
        if any(int(p.get("id_item") or 0) == int(item["id_item"]) for p in productos):
            return
        productos.insert(
            0,
            {
                "id_producto": self.context.next_int_id_in_state(state, "productos_tienda", "id_producto"),
                "id_item": int(item["id_item"]),
                "nombre_producto": str(item.get("nombre_item") or "Sin nombre"),
                "descripcion": "",
                "categoria": "General",
                "unidad_venta": str(item.get("unidad_venta") or "unidad"),
                "precio_venta": 0.0,
                "cantidad_stock": 0,
                "stock_minimo": 5,
                "estado": "Descatalogado",
                "imagen_url": "",
            },
        )

    def upsert_inventario(self, payload: dict[str, Any], actor: Any = None) -> dict[str, Any]:
        id_usuario = self._actor_usuario_id(actor)

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = {**payload}
            item_id = item.get("id_item")
            idx = -1
            if item_id is not None:
                idx = next((i for i, row in enumerate(state["inventario"]) if int(row.get("id_item", 0)) == int(item_id)), -1)
            if item_id is None:
                item_id = self.context.next_int_id_in_state(state, "inventario", "id_item")
            item["id_item"] = int(item_id)
            if str(item.get("tipo") or "").strip().lower() == TIPO_TIENDA.lower():
                item["tipo"] = TIPO_TIENDA
            required_text(item.get("nombre_item"))
            stock_inicial = integer_quantity(item.get("cantidad_stock", 0), "Stock")
            item["stock_minimo"] = integer_quantity(item["stock_minimo"] if item.get("stock_minimo") is not None else 1, "Stock mínimo")
            item["unidad_venta"] = str(item.get("unidad_venta") or "unidad")
            item["precio_venta"] = float(nonnegative(item.get("precio_venta") or 0, "Precio"))
            item["ubicacion"] = str(item.get("ubicacion") or "Almacén")
            item["observaciones"] = str(item.get("observaciones") or "")
            if idx >= 0:
                previo = state["inventario"][idx]
                # El stock solo cambia mediante movimientos; editar el ítem no lo modifica.
                item["cantidad_stock"] = int(previo.get("cantidad_stock", 0) or 0)
                item["n_activo"] = int(item.get("n_activo") or previo.get("n_activo") or self._next_n_activo(state))
                state["inventario"][idx] = item
            else:
                item["cantidad_stock"] = 0
                item["n_activo"] = int(item.get("n_activo") or self._next_n_activo(state))
                state["inventario"].insert(0, item)
                if stock_inicial > 0:
                    self._aplicar_movimiento(
                        state, item, "entrada", stock_inicial, "Alta de ítem: saldo inicial", id_usuario=id_usuario
                    )
            if self._es_item_tienda(item):
                self._crear_producto_para_item(state, item)
            self._actualizar_estados_tienda(state)
            return item

        return self.context.change(_fn)

    def delete_inventario(self, id_item: int) -> dict[str, Any] | None:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = self._find_item_in_state(state, id_item)
            if not item:
                raise EntityNotFound("Item de inventario no encontrado")
            tiene_movimientos = any(int(m.get("id_item", 0) or 0) == int(id_item) for m in state["mov_inv"])
            tiene_producto = any(int(p.get("id_item") or 0) == int(id_item) for p in state.get("productos_tienda", []))
            if tiene_movimientos or tiene_producto:
                item["estado"] = ESTADO_DESCONTINUADO
                self._actualizar_estados_tienda(state)
                return item
            state["inventario"] = [i for i in state["inventario"] if int(i.get("id_item", 0)) != int(id_item)]
            return None

        return self.context.change(_fn)

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return self.context.state["mov_inv"]

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_item = int(payload.get("id_item", 0))
        id_usuario = self.dependencies.normalize_usuario_id(payload.get("id_usuario"))
        tipo = str(payload.get("tipo_movimiento", "")).lower()

        if not self.get_item_inventario(id_item):
            raise EntityNotFound("Item de inventario no encontrado")
        if not self.dependencies.get_usuario(id_usuario):
            raise EntityNotFound("Usuario no encontrado")
        if tipo not in {"entrada", "salida", "ajuste"}:
            raise ValueError("Tipo de movimiento inválido")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = self._find_item_in_state(state, id_item)
            if not item:
                raise EntityNotFound("Item de inventario no encontrado")
            destino = self._normalizar_destino(tipo, payload.get("destino"))
            producto = self._producto_de_item(state, id_item) if destino == DESTINO_TIENDA else None
            if destino == DESTINO_TIENDA and not producto:
                raise ValueError("El ítem no tiene un producto de Tienda enlazado para reponer")
            mov = self._aplicar_movimiento(
                state,
                item,
                tipo,
                integer_quantity(payload.get("cantidad", 1), minimum=1),
                str(payload.get("descripcion") or ""),
                id_usuario=id_usuario,
                fecha=str(payload.get("fecha_movimiento") or ""),
                destino=destino,
            )
            if producto:
                # Reposición: las unidades salen de la reserva y entran al stock de la tienda.
                producto["cantidad_stock"] = int(producto.get("cantidad_stock") or 0) + int(mov["cantidad"])
            self._actualizar_estados_tienda(state)
            return {
                "movimiento": mov,
                "stock_actual": item["cantidad_stock"],
                "stock_tienda": int(producto["cantidad_stock"]) if producto else None,
            }

        return self.context.change(_fn)

    def actualizar_movimiento_inventario(self, id_mov: int, payload: dict[str, Any]) -> dict[str, Any]:
        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            mov = next((m for m in state["mov_inv"] if int(m.get("id_mov", 0) or 0) == int(id_mov)), None)
            if not mov:
                raise EntityNotFound("Movimiento no encontrado")

            tipo_actual = str(mov.get("tipo_movimiento") or "").lower()
            cantidad_actual = max(1, int(mov.get("cantidad") or 1))
            item_actual = int(mov.get("id_item") or 0)
            destino_actual = str(mov.get("destino") or "").strip().upper() or None
            nuevo_tipo = str(payload.get("tipo_movimiento") or tipo_actual).lower()
            nueva_cantidad = integer_quantity(payload.get("cantidad", cantidad_actual), minimum=1)
            nuevo_item = int(payload.get("id_item") or item_actual)
            if nuevo_tipo not in {"entrada", "salida", "ajuste"}:
                raise ValueError("Tipo de movimiento inválido")

            descripcion_actual = str(mov.get("descripcion") or "")
            descripcion = descripcion_actual if payload.get("descripcion") is None else str(payload["descripcion"]).strip()
            fecha = str(payload.get("fecha_movimiento") or mov.get("fecha_movimiento") or "")

            prefijo_pedido = _MOVIMIENTO_PEDIDO.match(descripcion_actual)
            es_de_pedido = destino_actual == DESTINO_VENTA or prefijo_pedido is not None
            if es_de_pedido:
                # Su destino no se toca: si llega otro, se detecta como cambio y se rechaza abajo.
                nuevo_destino = str(payload.get("destino", destino_actual) or "").strip().upper() or None
            else:
                nuevo_destino = self._normalizar_destino(nuevo_tipo, payload.get("destino", destino_actual))
            cambia_stock = (nuevo_tipo, nueva_cantidad, nuevo_item, nuevo_destino) != (
                tipo_actual,
                cantidad_actual,
                item_actual,
                destino_actual,
            )

            if es_de_pedido:
                if cambia_stock:
                    raise ValueError("Los movimientos de un pedido solo permiten cambiar la fecha y la descripción")
                if prefijo_pedido:
                    # Conserva la referencia al pedido aunque se reescriba la descripción.
                    prefijo = prefijo_pedido.group(0)
                    if not descripcion.startswith(prefijo):
                        descripcion = f"{prefijo} - {descripcion}" if descripcion else prefijo

            nuevos_stocks: list[tuple[dict[str, Any], int]] = []
            nuevos_stocks_tienda: list[tuple[dict[str, Any], int]] = []
            if cambia_stock:
                item_viejo = self._find_item_in_state(state, item_actual)
                item_nuevo = self._find_item_in_state(state, nuevo_item)
                if not item_nuevo:
                    raise EntityNotFound("Item de inventario no encontrado")
                if "ajuste" in (tipo_actual, nuevo_tipo):
                    # Un ajuste fija el stock exacto: solo se corrige si sigue siendo el último movimiento del ítem.
                    if tipo_actual == "ajuste" and nuevo_tipo != "ajuste":
                        raise ValueError("Un ajuste solo puede corregirse con otro ajuste")
                    if nuevo_item != item_actual:
                        raise ValueError("Un ajuste no puede cambiar de item")
                    ultimo = max(int(m.get("id_mov", 0) or 0) for m in state["mov_inv"] if int(m.get("id_item") or 0) == item_actual)
                    if int(mov["id_mov"]) != ultimo:
                        raise ValueError("Solo se puede corregir un ajuste si es el último movimiento del item; registra un nuevo ajuste")
                    nuevos_stocks.append((item_nuevo, nueva_cantidad))
                else:
                    def efecto(tipo: str, cantidad: int) -> int:
                        return cantidad if tipo == "entrada" else -cantidad

                    stocks = {int(i["id_item"]): int(i.get("cantidad_stock", 0) or 0) for i in (item_viejo, item_nuevo) if i}
                    if item_viejo:
                        stocks[item_actual] -= efecto(tipo_actual, cantidad_actual)
                    stocks[nuevo_item] += efecto(nuevo_tipo, nueva_cantidad)
                    for item in (item_viejo, item_nuevo):
                        if item and stocks[int(item["id_item"])] < 0:
                            raise ValueError(f"El cambio dejaría stock negativo en {item.get('nombre_item') or 'el item'}")
                    nuevos_stocks = [(item, stocks[int(item["id_item"])]) for item in (item_viejo, item_nuevo) if item]

                # Reposiciones: se quita lo que entró a la tienda y se suma lo nuevo.
                tienda: dict[int, tuple[dict[str, Any], int]] = {}
                cambios = (
                    (item_actual, -cantidad_actual if tipo_actual == "salida" and destino_actual == DESTINO_TIENDA else 0),
                    (nuevo_item, nueva_cantidad if nuevo_tipo == "salida" and nuevo_destino == DESTINO_TIENDA else 0),
                )
                for id_item, delta in cambios:
                    if not delta:
                        continue
                    producto = self._producto_de_item(state, id_item)
                    if not producto:
                        if delta > 0:
                            raise ValueError("El ítem no tiene un producto de Tienda enlazado para reponer")
                        continue
                    clave = int(producto["id_producto"])
                    previo = tienda[clave][1] if clave in tienda else int(producto.get("cantidad_stock") or 0)
                    tienda[clave] = (producto, previo + delta)
                for producto, stock in tienda.values():
                    if stock < 0:
                        raise ValueError(
                            f"La tienda ya vendió esas unidades de {producto.get('nombre_producto') or 'el producto'}; "
                            "no se puede reducir la reposición"
                        )
                nuevos_stocks_tienda = list(tienda.values())

            # Todo validado: se aplican los cambios.
            for item, stock in nuevos_stocks:
                item["cantidad_stock"] = stock
            for producto, stock in nuevos_stocks_tienda:
                producto["cantidad_stock"] = stock
            mov.update(
                {
                    "tipo_movimiento": nuevo_tipo,
                    "cantidad": nueva_cantidad,
                    "id_item": nuevo_item,
                    "fecha_movimiento": self.context.safe_date(fecha),
                    "descripcion": descripcion,
                    "destino": nuevo_destino,
                }
            )
            self._actualizar_estados_tienda(state)
            item_final = self._find_item_in_state(state, nuevo_item)
            return {"movimiento": mov, "stock_actual": int(item_final.get("cantidad_stock", 0) or 0) if item_final else None}

        return self.context.change(_fn)
