"""Doble transaccional para los spies REST históricos; la SQL se prueba en PostgreSQL."""
from copy import deepcopy
import json

PARENTS = ['USUARIO', 'PLANES_MEMBRESIA', 'PROMOCIONES', 'CLIENTES', 'MEMBRESIA', 'INVENTARIO',
           'TIENDA_PRODUCTOS', 'CATALOGO_RUTINA', 'HORARIO', 'HORARIOS_SERVICIO', 'MATRICULAS_HORARIO',
           'RUTINA_PROGRESO', 'MOV_INV', 'TICKETS_ATENCION', 'ASISTENCIA', 'VENTAS', 'DETALLE_VENTA']
DEFAULTS = {
    'USUARIO': {'Nombre': '', 'Correo': 'admin@example.com', 'Telefono': '', 'DNI': '', 'Contraseña': '', 'Estado': True, 'google_sub': None},
    'PROMOCIONES': {'limite_cupos': None, 'usos_actuales': 0, 'icono_etiqueta': '🏷️', 'palabra_clave': ''},
    'MEMBRESIA': {'id_promocion': None},
    'INVENTARIO': {'unidad_venta': 'unidad', 'precio_venta': 0, 'stock_minimo': 1, 'ubicacion': 'Almacén', 'observaciones': ''},
    'TIENDA_PRODUCTOS': {'descripcion': '', 'unidad_venta': 'unidad'},
}


def migrated_rows(table, rows):
    for row in rows:
        for key, value in DEFAULTS.get(table, {}).items():
            row.setdefault(key, value)
        if table == 'USUARIO':
            prefix = {'admin': 'ADM', 'trainer': 'TRA', 'staff': 'STA'}.get(row.get('Rol'), 'USR')
            row.setdefault('codigo_usuario', f"SG{prefix}{int(row['id_usuario']):03d}")
    return rows


class AtomicFakeMixin:
    def rpc(self, name, body):
        if name == 'gym_identity_floors':
            from infrastructure.repositories.gym_repository import SupabaseGymRepository
            keys = {table: pk for table, _local, pk in SupabaseGymRepository.CORE_TABLES.values()}
            keys['VENTAS'] = 'id_venta'
            return {table: max((int(row.get(keys.get(table, 'id_detalle'), 0) or 0)
                               for row in self.rows.get(table, [])), default=0) for table in body['p_tables']}
        assert name == 'commit_gym_transaction'
        for table, expected in body['p_expected'].items():
            if sorted(map(json.dumps, expected)) != sorted(map(json.dumps, self.rows.get(table, []))):
                raise RuntimeError('Supabase RPC: {"code":"40001"}')
        previous = deepcopy(self.rows)
        logs = {attr: list(getattr(self, attr)) for attr in ('calls', 'writes') if hasattr(self, attr)}
        def order(op):
            phase = {'delete_details': 0, 'delete': 1, 'insert': 2, 'update': 3}[op['action']]
            rank = PARENTS.index(op['table']) if op['table'] in PARENTS else 50
            return phase, -rank if phase == 1 else -1 if phase == 3 and op['table'] == 'MEMBRESIA' else rank
        try:
            for op in sorted(body['p_operations'], key=order):
                table, pk, action = op['table'], op['pk'], op['action']
                if action == 'delete_details':
                    if hasattr(self, 'delete_where'):
                        self.delete_where(table, 'id_venta', op['id'])
                    self.rows[table] = [row for row in self.rows.get(table, []) if row.get('id_venta') != op['id']]
                elif action == 'delete':
                    self.delete(table, pk, op['id'])
                    self.rows[table] = [row for row in self.rows.get(table, []) if row.get(pk) != op['id']]
                elif action == 'insert':
                    row = deepcopy(op['body'])
                    row.setdefault(pk, max((r.get(pk, 0) for r in self.rows.get(table, [])), default=0) + 1)
                    self.insert(table, row)
                    if not any(r.get(pk) == row[pk] for r in self.rows.get(table, [])):
                        self.rows.setdefault(table, []).append(row)
                else:
                    self.update(table, pk, op['id'], deepcopy(op['body']))
                    for row in self.rows.get(table, []):
                        if row.get(pk) == op['id']:
                            row.update(op['body'])
        except Exception:
            self.rows = previous
            for attr, old in logs.items():
                setattr(self, attr, old)
            raise
        return {'tables': {table: deepcopy(self.rows.get(table, [])) for table in body['p_expected']}}


def seed_snapshot(service):
    rows = {table: [service._to_remote_body(key, row) for row in service.state.get(key, [])]
            for key, (table, _local, _pk) in service.CORE_TABLES.items()}
    rows.update(VENTAS=[service._sale_to_remote(row) for row in service.state.get('pedidos_tienda', [])], DETALLE_VENTA=[])
    service.supabase.rows = deepcopy(rows)
    service._raw_rows = deepcopy(rows)
