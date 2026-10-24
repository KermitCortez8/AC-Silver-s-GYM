"""Planifica y confirma el conjunto de cambios de una unidad de negocio."""
from infrastructure.repositories.atomic_changes import commit_snapshot, table_changes
from infrastructure.repositories.gym_tables import CORE_TABLES
from infrastructure.repositories.mappers import store
from infrastructure.repositories.mappers.registry import to_remote_body

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_table_access import GymTableAccess


class GymChangePlanner:

    def __init__(self, database, cache: GymCache, tables: GymTableAccess):
        self.database, self.cache, self.tables = database, cache, tables

    def commit(self, previous, current, changed_keys):
        if not changed_keys:
            return
        operations = []
        for key in changed_keys:
            if key not in CORE_TABLES:
                continue
            table, _local_pk, remote_pk = CORE_TABLES[key]
            if table in self.tables.metadata.missing_tables:
                raise RuntimeError(f"La tabla {table} no está disponible; no se guardó ningún cambio")
            before = [self.tables.prepare_write(table, to_remote_body(key, row))
                      for row in previous.get(key, [])]
            after = [self.tables.prepare_write(table, to_remote_body(key, row))
                     for row in current.get(key, [])]
            operations.extend(table_changes(table, remote_pk, before, after))
        if "pedidos_tienda" in changed_keys:
            before = {int(row["id_pedido"]): row for row in previous.get("pedidos_tienda", [])}
            after = {int(row["id_pedido"]): row for row in current.get("pedidos_tienda", [])}
            operations.extend(table_changes("VENTAS", "id_venta",
                [self.tables.prepare_write("VENTAS", store._sale_to_remote(row)) for row in before.values()],
                [self.tables.prepare_write("VENTAS", store._sale_to_remote(row)) for row in after.values()]))
            for identity in before.keys() | after.keys():
                old, new = before.get(identity), after.get(identity)
                if old is None or new is None or old.get("items") != new.get("items"):
                    operations.append({"table": "DETALLE_VENTA", "pk": "id_detalle", "action": "delete_details",
                                       "id": identity})
                    for item in (new or {}).get("items", []):
                        operations.append({"table": "DETALLE_VENTA", "pk": "id_detalle", "action": "insert",
                                           "body": store._sale_detail_to_remote(identity, item)})
        if not operations:
            return
        raw = self.cache.raw_rows
        tables = {CORE_TABLES[key][0] for key in previous if key in CORE_TABLES}
        if "pedidos_tienda" in previous:
            tables.update(("VENTAS", "DETALLE_VENTA"))
        if "clientes" in previous and "CONFIGURACION_GIMNASIO" in raw:
            tables.add("CONFIGURACION_GIMNASIO")
        tables.difference_update(self.tables.metadata.missing_tables)
        if tables - raw.keys():
            raise RuntimeError("No hay una instantánea remota completa para confirmar los cambios")
        expected = {table: raw[table] for table in sorted(tables)}
        committed = commit_snapshot(self.database, expected, operations)
        self.cache.raw_rows.update(committed)
