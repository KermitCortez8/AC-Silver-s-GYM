"""Unidad de trabajo: bloqueo, reversión local y reintento de conflictos SQL."""
from copy import deepcopy
import time
from typing import Any
from application.errors import SchemaNotReady
from infrastructure.http_transport import database_code
from infrastructure.repositories.atomic_changes import SnapshotConflict
from infrastructure.repositories.gym_tables import CORE_TABLES, SYNC_STATE_KEYS, selected_resources

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_snapshot_reader import GymSnapshotReader
from infrastructure.repositories.gym_change_planner import GymChangePlanner
from infrastructure.repositories.gym_table_access import TableMetadata


class GymUnitOfWork:

    def __init__(self, database, cache: GymCache, reader: GymSnapshotReader, planner: GymChangePlanner, metadata: TableMetadata):
        self.database, self.cache, self.reader = database, cache, reader
        self.planner, self.metadata = planner, metadata

    def snapshot(self, resources=None) -> dict[str, Any]:
        selected = selected_resources(resources)
        return {key: deepcopy(self.cache.state.get(key, [])) for key in SYNC_STATE_KEYS if key in selected}

    def changed_keys(self, previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
        return [key for key in previous if previous[key] != current.get(key, [])]

    def change(self, fn, resources=None):
        with self.cache.lock:
            for attempt in range(3):
                self.reader.refresh_if_stale(resources)
                previous = self.snapshot(resources)
                try:
                    if "preregistros" in previous and "PREREGISTROS_MEMBRESIA" in self.metadata.missing_tables:
                        raise SchemaNotReady("020_public_preregistrations.sql")
                    table_names = [CORE_TABLES[key][0] for key in previous if key in CORE_TABLES
                                   and CORE_TABLES[key][0] not in self.metadata.missing_tables]
                    if "pedidos_tienda" in previous:
                        table_names.append("VENTAS")
                    floors = self.database.rpc("gym_identity_floors", {"p_tables": sorted(table_names)})
                    if not isinstance(floors, dict):
                        raise SchemaNotReady("015_atomic_gym_transactions.sql")
                    self.cache.state["_identity_floors"] = {
                        key: int(floors.get(table, 0)) for key, (table, _local, _remote) in CORE_TABLES.items()
                    }
                    self.cache.state["_identity_floors"]["pedidos_tienda"] = int(floors.get("VENTAS", 0))
                    result = fn(self.cache.state)
                    changed_keys = self.changed_keys(previous, self.cache.state)
                    if changed_keys:
                        self.planner.commit(previous, self.cache.state, changed_keys)
                except Exception as error:
                    self.cache.state.update(deepcopy(previous))
                    self.cache.last_refresh_at = 0.0
                    self.cache.resource_refreshed_at.clear()
                    if database_code(error) in {"PGRST202", "42883"}:
                        raise SchemaNotReady("015_atomic_gym_transactions.sql") from error
                    if isinstance(error, SnapshotConflict) and attempt < 2:
                        # La RPC no escribió nada. Recalcula las reglas sobre datos actuales.
                        self.reader.load(resources)
                        continue
                    if isinstance(error, SnapshotConflict):
                        raise ValueError("Los datos cambiaron. Actualiza e inténtalo de nuevo.") from error
                    raise
                changed_at = time.monotonic()
                self.cache.resource_refreshed_at.update(dict.fromkeys(changed_keys, changed_at))
                return result
