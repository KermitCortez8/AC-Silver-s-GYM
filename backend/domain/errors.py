class AttendanceConflict(ValueError):
    """La asistencia fue modificada o entra en conflicto con otro registro."""


class EntityNotFound(ValueError):
    """No existe la entidad solicitada."""


class MembershipRequired(ValueError):
    """La operación requiere una membresía activa."""


class EnrollmentConflict(ValueError):
    """Una matrícula incumple cupos o unicidad."""
