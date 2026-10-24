"""Selección de mapeos puros por recurso del gimnasio."""
from typing import Any
from infrastructure.repositories.mappers import accounts, attendance, configuration, inventory, memberships, schedules, store

def to_remote_body(state_key: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "planes_membresia": memberships._plan_to_remote,
        "promociones": memberships._promotion_to_remote,
        "clientes": accounts._client_to_remote,
        "membresia": memberships._membership_to_remote,
        "usuario": accounts._user_to_remote,
        "inventario": inventory._inventory_to_remote,
        "mov_inv": inventory._inventory_move_to_remote,
        "productos_tienda": inventory._product_to_remote,
        "catalogo_rutina": schedules._routine_to_remote,
        "horario": schedules._schedule_to_remote,
        "horarios_servicio": schedules._service_schedule_to_remote,
        "matriculas_horario": schedules._schedule_enrollment_to_remote,
        "rutina_progreso": schedules._routine_progress_to_remote,
        "tickets_atencion": schedules._ticket_to_remote,
        "asistencia": attendance._attendance_to_remote,
    }[state_key](row)
