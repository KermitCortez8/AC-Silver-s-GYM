"""Reglas de inventory sobre el agregado en memoria."""
from __future__ import annotations
from domain.errors import EntityNotFound
from domain.validation import nonnegative, required_text, integer_quantity
from domain.form_limits import INVENTORY_TEXT_LIMIT

import re
import unicodedata
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from domain.services.gym_values import TIPO_TIENDA, ESTADO_DESCONTINUADO, ESTADO_DISPONIBLE, ESTADO_STOCK_BAJO, ESTADO_AGOTADO, DESTINO_TIENDA, DESTINO_VENTA, _MOVIMIENTO_PEDIDO


from dataclasses import dataclass
from typing import Callable
from domain.services.rule_context import RuleContext


# Equipos y accesorios llevan N° de activo por unidad (1008-MC-001); el resto cuenta solo cantidad.
ESTADOS_UNIDAD = ("Operativo", "En mantenimiento", "Fuera de servicio")
ESTADO_UNIDAD_BAJA = "Dado de baja"
# Cambio de ubicación de una unidad: queda en MOV_INV pero no altera el stock.
TIPO_TRASLADO = "traslado"
_LIMA = ZoneInfo("America/Lima")
_PALABRAS_VACIAS = {"de", "del", "la", "las", "el", "los", "para", "por", "con", "y", "a", "al", "en", "un", "una"}


def es_categoria_por_unidad(tipo: Any) -> bool:
    valor = str(tipo or "").strip().lower()
    return valor.startswith("equipo") or valor.startswith("accesorio")


def prefijo_activo(nombre: Any) -> str:
    """Iniciales de las dos primeras palabras significativas; misma regla que la migración 026."""
    texto = unicodedata.normalize("NFKD", str(nombre or "")).encode("ascii", "ignore").decode().lower()
    palabras = [p for p in re.split(r"[^a-z]+", texto) if p and p not in _PALABRAS_VACIAS]
    if not palabras:
        return "AC"
    if len(palabras) == 1:
        return palabras[0][:2].ljust(2, "x").upper()
    return (palabras[0][0] + palabras[1][0]).upper()


def codigo_unidad(n_activo: Any, prefijo: str, correlativo: int) -> str:
    return f"{int(n_activo or 0)}-{prefijo}-{correlativo:03d}"


@dataclass(frozen=True)
class InventoryDependencies:
    normalize_usuario_id: Callable
    get_usuario: Callable


class InventoryRules:
    def __init__(self, context: RuleContext, dependencies: InventoryDependencies):
        self.context = context
        self.dependencies = dependencies

    def inventario(self) -> list[dict[str, Any]]:
        # Los eliminados desde la papelera de Tienda solo se conservan por sus movimientos.
        return [i for i in self.context.state["inventario"] if not i.get("eliminado")]

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
        id_unidad: int | None = None,
    ) -> dict[str, Any]:
        tipo = str(tipo or "").lower()
        if tipo not in {"entrada", "salida", "ajuste", TIPO_TRASLADO}:
            raise ValueError("Tipo de movimiento inválido")
        cantidad = integer_quantity(cantidad, minimum=1)
        stock_actual = int(item.get("cantidad_stock", 0) or 0)
        if tipo == TIPO_TRASLADO:
            nuevo_stock = stock_actual
        elif tipo == "entrada":
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
            "id_unidad": int(id_unidad) if id_unidad else None,
            "hora_movimiento": self._hora_actual(),
        }
        state["mov_inv"].insert(0, mov)
        return mov

    def _hora_actual(self) -> str | None:
        # Hora local de Lima en que se registra el movimiento (HH:MM:SS).
        try:
            momento = datetime.fromisoformat(str(self.context.now()).replace("Z", "+00:00"))
        except ValueError:
            return None
        if momento.tzinfo is None:
            return momento.strftime("%H:%M:%S")
        return momento.astimezone(_LIMA).strftime("%H:%M:%S")

    @staticmethod
    def _producto_de_item(state: dict[str, Any], id_item: Any) -> dict[str, Any] | None:
        if not id_item:
            return None
        return next((p for p in state.get("productos_tienda", []) if int(p.get("id_item") or 0) == int(id_item)), None)

    @staticmethod
    def _usa_unidades(item: dict[str, Any] | None) -> bool:
        # Los artículos anteriores a la migración 026 no tienen prefijo y siguen contando solo cantidad.
        return bool(item) and es_categoria_por_unidad(item.get("tipo")) and bool(item.get("prefijo_activo"))

    @staticmethod
    def _unidades_de(state: dict[str, Any], id_item: Any, activas: bool = True) -> list[dict[str, Any]]:
        return [
            u for u in state.get("inventario_unidades", [])
            if int(u.get("id_item") or 0) == int(id_item or 0)
            and (not activas or u.get("estado") != ESTADO_UNIDAD_BAJA)
        ]

    def _crear_unidades(self, state: dict[str, Any], item: dict[str, Any], cantidad: int, fecha: str = "") -> list[dict[str, Any]]:
        unidades = state.setdefault("inventario_unidades", [])
        siguiente = max((int(u.get("correlativo") or 0) for u in self._unidades_de(state, item["id_item"], activas=False)), default=0)
        creadas = []
        for correlativo in range(siguiente + 1, siguiente + cantidad + 1):
            unidad = {
                "id_unidad": self.context.next_int_id_in_state(state, "inventario_unidades", "id_unidad"),
                "id_item": int(item["id_item"]),
                "correlativo": correlativo,
                "codigo": codigo_unidad(item.get("n_activo"), item["prefijo_activo"], correlativo),
                "estado": "Operativo",
                "ubicacion": str(item.get("ubicacion") or "Almacén"),
                "observaciones": "",
                "fecha_alta": self.context.safe_date(fecha),
                "fecha_baja": None,
            }
            unidades.append(unidad)
            creadas.append(unidad)
        return creadas

    @staticmethod
    def _anotar_unidades(mov: dict[str, Any], unidades: list[dict[str, Any]]) -> None:
        # MOV_INV guarda qué códigos de activo entraron; las altas siempre son correlativas.
        if not unidades:
            return
        codigos = unidades[0]["codigo"] if len(unidades) == 1 else f"{unidades[0]['codigo']} a {unidades[-1]['codigo']}"
        texto = f"{'Unidad' if len(unidades) == 1 else 'Unidades'}: {codigos}"
        mov["descripcion"] = f"{mov['descripcion']} · {texto}" if mov.get("descripcion") else texto

    def _sincronizar_items_por_unidad(self, state: dict[str, Any]) -> None:
        # El stock es la cantidad de unidades activas y el estado resume el de sus unidades.
        # Cada operación solo carga sus recursos: sin INVENTARIO_UNIDADES no hay nada que sincronizar
        # (si se tomara como lista vacía, los equipos quedarían en 0 al operar desde Tienda o Pedidos).
        if "inventario_unidades" not in state:
            return
        for item in state.get("inventario", []):
            if not self._usa_unidades(item):
                continue
            activas = self._unidades_de(state, item["id_item"])
            item["cantidad_stock"] = len(activas)
            if str(item.get("estado") or "") == ESTADO_DESCONTINUADO:
                continue
            estados = {u.get("estado") for u in activas}
            item["estado"] = next((e for e in ESTADOS_UNIDAD if e in estados), ESTADO_AGOTADO)

    @staticmethod
    def _normalizar_destino(tipo: str, destino: Any) -> str | None:
        valor = str(destino or "").strip().upper()
        if tipo != "salida" or not valor:
            return None
        if valor != DESTINO_TIENDA:
            raise ValueError("Destino inválido: una salida solo puede tener destino TIENDA")
        return valor

    def _actualizar_estados_tienda(self, state: dict[str, Any]) -> None:
        self._sincronizar_items_por_unidad(state)
        self._actualizar_estados_items_tienda(state)
        for producto in state.get("productos_tienda", []):
            stock = int(producto.get("cantidad_stock") or 0)
            if producto.get("archivado"):
                producto["estado"] = "Descatalogado"
                continue
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
                # El prefijo es fijo: renombrar el artículo no cambia los códigos de sus unidades.
                item["prefijo_activo"] = str(previo.get("prefijo_activo") or "")
                state["inventario"][idx] = item
                if es_categoria_por_unidad(item.get("tipo")) and not item["prefijo_activo"]:
                    # Pasa a controlarse por unidad: el stock que ya tenía recibe sus códigos.
                    item["prefijo_activo"] = prefijo_activo(item.get("nombre_item"))
                    if not self._unidades_de(state, item["id_item"], activas=False):
                        self._crear_unidades(state, item, item["cantidad_stock"])
            else:
                item["cantidad_stock"] = 0
                item["n_activo"] = int(item.get("n_activo") or self._next_n_activo(state))
                item["prefijo_activo"] = prefijo_activo(item.get("nombre_item")) if es_categoria_por_unidad(item.get("tipo")) else ""
                state["inventario"].insert(0, item)
                if stock_inicial > 0:
                    mov = self._aplicar_movimiento(
                        state, item, "entrada", stock_inicial, "Alta de ítem: saldo inicial", id_usuario=id_usuario
                    )
                    if self._usa_unidades(item):
                        self._anotar_unidades(mov, self._crear_unidades(state, item, stock_inicial, mov["fecha_movimiento"]))
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
                # Se archiva: MOV_INV y TIENDA_PRODUCTOS lo referencian y su historial se conserva.
                item["estado"] = ESTADO_DESCONTINUADO
                item["archivado"] = True
                item["fecha_baja"] = self.context.today()
                for producto in state.get("productos_tienda", []):
                    if int(producto.get("id_item") or 0) == int(id_item):
                        producto["archivado"] = True
                self._actualizar_estados_tienda(state)
                return item
            state["inventario"] = [i for i in state["inventario"] if int(i.get("id_item", 0)) != int(id_item)]
            return None

        return self.context.change(_fn)

    def _unidades_elegidas(self, state: dict[str, Any], item: dict[str, Any], ids: Any, accion: str = "salen") -> list[dict[str, Any]]:
        ids = [integer_quantity(i, minimum=1) for i in (ids or [])]
        if not ids:
            raise ValueError(f"Elige las unidades que {accion}")
        if len(set(ids)) != len(ids):
            raise ValueError("Una unidad está repetida en el movimiento")
        activas = {int(u["id_unidad"]): u for u in self._unidades_de(state, item["id_item"])}
        if any(i not in activas for i in ids):
            raise ValueError("Alguna unidad elegida ya no está activa o no pertenece al artículo")
        return [activas[i] for i in ids]

    def _trasladar_unidad(self, state, item, unidad, destino, id_usuario=None, fecha="", nota=""):
        # Cambia la ubicación de la unidad y deja el traslado en MOV_INV; el stock no cambia.
        origen = str(unidad.get("ubicacion") or "")
        unidad["ubicacion"] = destino
        descripcion = f"Traslado {unidad['codigo']}: {origen or 'Sin ubicación'} → {destino}"
        return self._aplicar_movimiento(
            state, item, TIPO_TRASLADO, 1, f"{descripcion} · {nota}" if nota else descripcion,
            id_usuario=id_usuario, fecha=fecha, id_unidad=unidad["id_unidad"],
        )

    def unidades_inventario(self) -> list[dict[str, Any]]:
        return self.context.state.get("inventario_unidades", [])

    def actualizar_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        def _fn(state: dict[str, Any]):
            unidad = next((u for u in state.get("inventario_unidades", []) if int(u.get("id_unidad") or 0) == int(id_unidad)), None)
            if not unidad:
                raise EntityNotFound("Unidad no encontrada")
            if unidad.get("estado") == ESTADO_UNIDAD_BAJA:
                raise ValueError("La unidad está dada de baja y no se puede editar")
            item = self._find_item_in_state(state, unidad.get("id_item"))
            if item and item.get("archivado"):
                raise ValueError("El artículo está archivado y no admite cambios")
            estado = str(payload.get("estado") or unidad.get("estado") or "Operativo")
            if estado not in ESTADOS_UNIDAD:
                raise ValueError("Estado de unidad inválido; para retirarla usa Dar de baja")
            unidad["estado"] = estado
            if payload.get("ubicacion") is not None:
                destino = required_text(payload["ubicacion"], "La ubicación", INVENTORY_TEXT_LIMIT)
                if item and destino != str(unidad.get("ubicacion") or ""):
                    self._trasladar_unidad(
                        state, item, unidad, destino,
                        id_usuario=self.dependencies.normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None,
                    )
                else:
                    unidad["ubicacion"] = destino
            if payload.get("observaciones") is not None:
                unidad["observaciones"] = str(payload["observaciones"]).strip()
            self._actualizar_estados_tienda(state)
            return unidad

        return self.context.change(_fn)

    def restablecer_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        # Devuelve a servicio la misma unidad (mismo código) con una entrada de 1 ligada a ella.
        id_usuario = self.dependencies.normalize_usuario_id(payload.get("id_usuario")) if payload.get("id_usuario") else None

        def _fn(state: dict[str, Any]):
            unidad = next((u for u in state.get("inventario_unidades", []) if int(u.get("id_unidad") or 0) == int(id_unidad)), None)
            if not unidad:
                raise EntityNotFound("Unidad no encontrada")
            if unidad.get("estado") != ESTADO_UNIDAD_BAJA:
                raise ValueError("La unidad no está dada de baja")
            item = self._find_item_in_state(state, unidad.get("id_item"))
            if not item:
                raise EntityNotFound("Item de inventario no encontrado")
            if item.get("archivado"):
                raise ValueError("El artículo está archivado y no admite movimientos")
            motivo = str(payload.get("motivo") or "").strip()
            descripcion = f"Restablecimiento {unidad['codigo']}" + (f" · {motivo}" if motivo else "")
            mov = self._aplicar_movimiento(
                state, item, "entrada", 1, descripcion, id_usuario=id_usuario,
                fecha=str(payload.get("fecha_movimiento") or ""), id_unidad=unidad["id_unidad"],
            )
            unidad["estado"] = "Operativo"
            unidad["fecha_baja"] = None
            self._actualizar_estados_tienda(state)
            return {"unidad": unidad, "movimiento": mov, "stock_actual": item["cantidad_stock"]}

        return self.context.change(_fn)

    def dar_de_baja_unidad_inventario(self, id_unidad: int, payload: dict[str, Any]) -> dict[str, Any]:
        # La baja es una salida de una unidad: queda en Movimientos y la unidad conserva su historial.
        unidad = next((u for u in self.context.state.get("inventario_unidades", []) if int(u.get("id_unidad") or 0) == int(id_unidad)), None)
        if not unidad:
            raise EntityNotFound("Unidad no encontrada")
        return self.registrar_movimiento_inventario({
            "id_item": unidad["id_item"],
            "id_usuario": payload.get("id_usuario"),
            "tipo_movimiento": "salida",
            "cantidad": 1,
            "unidades": [int(id_unidad)],
            "descripcion": str(payload.get("motivo") or "Baja de unidad").strip(),
            "fecha_movimiento": str(payload.get("fecha_movimiento") or ""),
        })

    def movimientos_inventario(self) -> list[dict[str, Any]]:
        return self.context.state["mov_inv"]

    def registrar_movimiento_inventario(self, payload: dict[str, Any]) -> dict[str, Any]:
        id_item = int(payload.get("id_item", 0))
        id_usuario = self.dependencies.normalize_usuario_id(payload.get("id_usuario"))
        tipo = str(payload.get("tipo_movimiento", "")).lower()

        item_actual = self.get_item_inventario(id_item)
        if not item_actual:
            raise EntityNotFound("Item de inventario no encontrado")
        if item_actual.get("archivado"):
            raise ValueError("El artículo está archivado y no admite movimientos")
        if not self.dependencies.get_usuario(id_usuario):
            raise EntityNotFound("Usuario no encontrado")
        if tipo not in {"entrada", "salida", "ajuste", TIPO_TRASLADO}:
            raise ValueError("Tipo de movimiento inválido")

        # Procesa esta operación.
        def _fn(state: dict[str, Any]):
            item = self._find_item_in_state(state, id_item)
            if not item:
                raise EntityNotFound("Item de inventario no encontrado")
            if tipo == TIPO_TRASLADO:
                return self._registrar_traslado(state, item, payload, id_usuario)
            destino = self._normalizar_destino(tipo, payload.get("destino"))
            producto = self._producto_de_item(state, id_item) if destino == DESTINO_TIENDA else None
            if destino == DESTINO_TIENDA and not producto:
                raise ValueError("El ítem no tiene un producto de Tienda enlazado para reponer")
            cantidad = integer_quantity(payload.get("cantidad", 1), minimum=1)
            descripcion = str(payload.get("descripcion") or "")
            salientes: list[dict[str, Any]] = []
            if self._usa_unidades(item):
                if tipo == "ajuste":
                    raise ValueError("Los equipos con N° de activo por unidad no admiten ajustes: registra una entrada o una salida")
                if tipo == "salida":
                    salientes = self._unidades_elegidas(state, item, payload.get("unidades"))
                    cantidad = len(salientes)
                    codigos = "Unidades: " + ", ".join(u["codigo"] for u in salientes)
                    descripcion = f"{descripcion} · {codigos}" if descripcion else codigos
            mov = self._aplicar_movimiento(
                state,
                item,
                tipo,
                cantidad,
                descripcion,
                id_usuario=id_usuario,
                fecha=str(payload.get("fecha_movimiento") or ""),
                destino=destino,
                id_unidad=salientes[0]["id_unidad"] if len(salientes) == 1 else None,
            )
            if self._usa_unidades(item):
                if tipo == "entrada":
                    self._anotar_unidades(mov, self._crear_unidades(state, item, cantidad, mov["fecha_movimiento"]))
                for unidad in salientes:
                    unidad["estado"] = ESTADO_UNIDAD_BAJA
                    unidad["fecha_baja"] = mov["fecha_movimiento"]
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

    def _registrar_traslado(self, state, item, payload, id_usuario) -> dict[str, Any]:
        # Solo los equipos con N° de activo cambian de ubicación por unidad; Tienda sigue con destino Tienda.
        if not self._usa_unidades(item):
            raise ValueError("Solo los equipos y accesorios con N° de activo se trasladan entre ubicaciones")
        unidades = self._unidades_elegidas(state, item, payload.get("unidades"), "se trasladan")
        destino = required_text(payload.get("ubicacion_destino"), "La ubicación de destino", INVENTORY_TEXT_LIMIT)
        repetidas = [u["codigo"] for u in unidades if str(u.get("ubicacion") or "") == destino]
        if repetidas:
            raise ValueError(f"{', '.join(repetidas)} ya está en {destino}")
        nota = str(payload.get("descripcion") or "").strip()
        fecha = str(payload.get("fecha_movimiento") or "")
        movimientos = [
            self._trasladar_unidad(state, item, unidad, destino, id_usuario=id_usuario, fecha=fecha, nota=nota)
            for unidad in unidades
        ]
        self._actualizar_estados_tienda(state)
        return {"movimiento": movimientos[0], "movimientos": movimientos,
                "stock_actual": item["cantidad_stock"], "stock_tienda": None}

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
            if tipo_actual == TIPO_TRASLADO or nuevo_tipo == TIPO_TRASLADO:
                # Un traslado describe dónde estuvo una unidad: no se convierte ni se convierte en él.
                if (nuevo_tipo, nueva_cantidad, nuevo_item) != (tipo_actual, cantidad_actual, item_actual):
                    raise ValueError("Los traslados solo permiten cambiar la fecha y la descripción")
                if payload.get("descripcion") is not None:
                    mov["descripcion"] = str(payload["descripcion"]).strip()
                mov["fecha_movimiento"] = self.context.safe_date(str(payload.get("fecha_movimiento") or mov.get("fecha_movimiento") or ""))
                item_final = self._find_item_in_state(state, item_actual)
                return {"movimiento": mov, "stock_actual": int(item_final.get("cantidad_stock", 0) or 0) if item_final else None}
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

            if cambia_stock and any(
                self._usa_unidades(self._find_item_in_state(state, i)) for i in (item_actual, nuevo_item)
            ):
                # Cada entrada o salida creó o dio de baja unidades concretas.
                raise ValueError("Los movimientos de equipos con unidades solo permiten cambiar la fecha y la descripción")

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
