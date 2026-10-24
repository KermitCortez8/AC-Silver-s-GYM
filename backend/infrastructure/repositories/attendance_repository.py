"""Persistencia específica de save_attendance, independiente de la fachada global."""
from copy import deepcopy
from infrastructure.http_transport import database_code
from domain.errors import AttendanceConflict
from infrastructure.http_transport import error_payload
from infrastructure.repositories.mappers import attendance

from infrastructure.repositories.gym_cache import GymCache


class AttendanceRepository:

    def __init__(self, database, cache: GymCache):
        self.database, self.cache = database, cache

    def save_attendance(self, row, expected_version, audit):

        with self.cache.lock:
            try:
                saved = self.database.rpc("guardar_asistencia", {
                    "p_registro": attendance._attendance_to_remote(row),
                    "p_version": expected_version, "p_evento": audit,
                })
            except RuntimeError as error:
                if database_code(error) == "P0001":
                    message = error_payload(error).get("message") or "El registro cambió. Actualiza la asistencia e inténtalo de nuevo."
                    raise AttendanceConflict(message) from error
                raise
            mapped = attendance._map_attendance(saved)
            rows = self.cache.state.setdefault("asistencia", [])
            index = next((i for i, r in enumerate(rows) if r["id_asistencia"] == mapped["id_asistencia"]), None)
            if index is None:
                rows.insert(0, mapped)
            else:
                rows[index] = mapped
            return deepcopy(mapped)
