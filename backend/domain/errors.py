class AttendanceConflict(ValueError):
    """La asistencia fue modificada o entra en conflicto con otro registro."""


def raise_schedule_enrollment_error(error):
    normalized = str(error).lower()
    for markers, message in (
        (("ya esta matriculado", "23505"), "El cliente ya esta matriculado en este horario"),
        (("sin cupos",), "Horario sin cupos disponibles"),
        (("sin membresia activa",), "Cliente sin membresia activa"),
        (("horario no disponible", "23503"), "Horario no disponible"),
    ):
        if any(marker in normalized for marker in markers):
            raise ValueError(message) from error
    raise error
