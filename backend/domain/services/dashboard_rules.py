"""Reglas de dashboard sobre el agregado en memoria."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from domain.services.gym_values import ESTADO_PEDIDO_CANCELADO, _days_until, _pedido_pagado


class DashboardRules:
    def summary(self) -> dict[str, Any]:
        total_clientes = len(self.state["clientes"])
        today = self.today()
        membresias_activas = len(
            [
                m
                for m in self.state["membresia"]
                if str(m.get("estado", "")).lower() == "activa"
                and str(m.get("fecha_inicio", "")) <= today <= str(m.get("fecha_fin", ""))
            ]
        )
        attendance_today = datetime.now(ZoneInfo("America/Lima")).date().isoformat()
        valid_attendance = [a for a in self.state["asistencia"] if not a.get("anulado")]
        asistencias_hoy = len([a for a in valid_attendance if a.get("fecha") == attendance_today])
        items_stock_bajo = [
            item
            for item in self.state["inventario"]
            if int(item.get("cantidad_stock", 0)) <= int(item.get("stock_minimo", 0))
        ]
               # Solo cuentan los pedidos con el cobro confirmado; las ventas excluyen los cancelados.
        pedidos = [p for p in self.state.get("pedidos_tienda", []) if _pedido_pagado(p)]
        pedidos_pendientes = len([p for p in pedidos if str(p.get("estado_pedido") or "").upper() == "PENDIENTE"])
        ventas_mes = round(
            sum(
                float(p.get("total") or 0)
                for p in pedidos
                if str(p.get("estado_pedido") or "").upper() != ESTADO_PEDIDO_CANCELADO
                and str(p.get("fecha_pedido") or "")[:7] == today[:7]
            ),
            2,
        )
        vencimientos = [m for m in self.state["membresia"] if (days := _days_until(m.get("fecha_fin"), today)) is not None and 0 <= days <= 7]
        capacidad = self.configuracion_gimnasio()

        return {
            "stats": {
                "total_clientes": total_clientes,
                "membresias_activas": membresias_activas,
                "asistencias_hoy": asistencias_hoy,
                "total_items_inventario": len(self.state["inventario"]),
                "items_stock_bajo": len(items_stock_bajo),
                "pedidos_pendientes": pedidos_pendientes,
                "ventas_mes": ventas_mes,
                "vencimientos_7_dias": len(vencimientos),
                "aforo_dia": f"{asistencias_hoy}/{capacidad.get('capacidad_total', 30)}",
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
                    "asistencias": len(valid_attendance),
                    "asistencias_hoy": asistencias_hoy,
                },
            },
            "alertas": items_stock_bajo,
        }
