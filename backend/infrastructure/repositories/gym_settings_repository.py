"""Persistencia específica de save_settings, independiente de la fachada global."""
import time
from typing import Any
from application.errors import SchemaNotReady
from domain.models.gym import ParametrosHorarioServicioInput
from infrastructure.http_transport import database_code
from infrastructure.repositories.atomic_changes import SnapshotConflict, commit_snapshot, table_changes
from infrastructure.repositories.mappers import configuration

from infrastructure.repositories.gym_cache import GymCache
from infrastructure.repositories.gym_table_access import GymTableAccess

TABLE = "CONFIGURACION_GIMNASIO"
SETTINGS_MIGRATION = "028_parametros_horarios.sql"


class GymSettingsRepository:

    def __init__(self, database, cache: GymCache, tables: GymTableAccess):
        self.database, self.cache, self.tables = database, cache, tables

    def save_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        updates = configuration._config_to_remote(payload)
        editing_schedules = "parametros_horarios" in payload
        if editing_schedules:
            settings = ParametrosHorarioServicioInput.model_validate(payload["parametros_horarios"])
            updates = {"parametros_horarios": settings.model_dump()}
        with self.cache.lock:
            for attempt in range(3):
                rows = self.tables.select_optional(TABLE, "id_config.asc")
                if editing_schedules and TABLE in self.tables.metadata.missing_tables:
                    raise SchemaNotReady(SETTINGS_MIGRATION)
                row = rows[0] if rows else {"id_config": 1, **configuration._config_to_remote({})}
                body = {**row, **updates}
                operations = table_changes(TABLE, "id_config", rows, [body, *rows[1:]])
                for operation in operations:
                    if operation["action"] == "update":
                        operation["body"] = {"id_config": row["id_config"], **updates}
                try:
                    committed = commit_snapshot(self.database, {TABLE: rows}, operations)
                except SnapshotConflict:
                    if attempt < 2:
                        continue
                    raise ValueError("La configuración cambió. Actualiza e inténtalo de nuevo.")
                except RuntimeError as error:
                    if editing_schedules and database_code(error) == "42703":
                        raise SchemaNotReady(SETTINGS_MIGRATION) from error
                    raise
                saved = next((entry for entry in committed.get(TABLE, []) if entry["id_config"] == row["id_config"]), None)
                if saved is None:
                    raise RuntimeError("La base de datos no confirmó la configuración del gimnasio")
                self.cache.raw_rows = {**self.cache.raw_rows, **committed}
                self.cache.state["configuracion_gimnasio"] = configuration._map_config(saved)
                self.cache.resource_refreshed_at.update(configuracion_gimnasio=time.monotonic())
                return dict(self.cache.state["configuracion_gimnasio"])
