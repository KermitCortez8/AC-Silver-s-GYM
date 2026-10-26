"""Ensambla capacidades de persistencia con dependencias explícitas."""
from dataclasses import dataclass
from infrastructure.repositories.gym_table_access import GymTableAccess
from infrastructure.repositories.gym_snapshot_reader import GymSnapshotReader
from infrastructure.repositories.gym_change_planner import GymChangePlanner
from infrastructure.repositories.gym_unit_of_work import GymUnitOfWork
from infrastructure.repositories.schedule_enrollment_repository import ScheduleEnrollmentRepository
from infrastructure.repositories.attendance_repository import AttendanceRepository
from infrastructure.repositories.gym_settings_repository import GymSettingsRepository
from infrastructure.repositories.inventory_status_writer import InventoryStatusWriter


@dataclass
class RepositoryComponents:
    tables: GymTableAccess
    reader: GymSnapshotReader
    planner: GymChangePlanner
    writer: GymUnitOfWork
    enrollments: ScheduleEnrollmentRepository
    attendance: AttendanceRepository
    settings: GymSettingsRepository
    inventory_status: InventoryStatusWriter


def compose_repository(database, cache, metadata, ttl):
    tables = GymTableAccess(database, metadata)
    reader = GymSnapshotReader(database, cache, tables, ttl)
    planner = GymChangePlanner(database, cache, tables)
    return RepositoryComponents(
        tables, reader, planner, GymUnitOfWork(database, cache, reader, planner, metadata),
        ScheduleEnrollmentRepository(database, cache, reader), AttendanceRepository(database, cache),
        GymSettingsRepository(database, cache, tables), InventoryStatusWriter(database, metadata),
    )


