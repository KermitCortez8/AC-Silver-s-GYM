"""Persistencia específica de save_settings, independiente de la fachada global."""
import time
from typing import Any
from infrastructure.repositories.atomic_changes import SnapshotConflict, commit_snapshot, table_changes
from infrastructure.repositories.mappers import configuration

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_table_access import GymTableAccess


class GymSettingsRepository:

    def __init__(self, database, cache: GymCache, tables: GymTableAccess):
        self.database, self.cache, self.tables = database, cache, tables

    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"id_config": 1, **configuration._config_to_remote(payload)}
        with self.cache.lock:
            for attempt in range(3):
                rows = self.tables.select_optional("CONFIGURACION_GIMNASIO", "id_config.asc")
                try:
                    committed = commit_snapshot(self.database, {"CONFIGURACION_GIMNASIO": rows},
                        table_changes("CONFIGURACION_GIMNASIO", "id_config", rows, [body]))
                except SnapshotConflict:
                    if attempt < 2:
                        continue
                    raise ValueError("La configuración cambió. Actualiza e inténtalo de nuevo.")
                self.cache.raw_rows = {**self.cache.raw_rows, **committed}
                self.cache.state["configuracion_gimnasio"] = configuration._map_config(body)
                self.cache.resource_refreshed_at.update(configuracion_gimnasio=time.monotonic())
                return dict(self.cache.state.get("configuracion_gimnasio") or {})
