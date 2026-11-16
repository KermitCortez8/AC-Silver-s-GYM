"""Complemento TC-136: repetir clase cerrada no crea ni reabre visitas."""
from tests.asistencias.integracion.test_general_attendance import attendance, admin, enroll  # noqa: F401


def test_tc136_repetir_clase_despues_de_salida_no_reabre(attendance, admin):
    enroll(attendance)
    first = attendance.enter({"id_matricula": 1}, admin)
    attendance.advance()
    closed = attendance.exit(first["id_asistencia"], admin)
    again = attendance.enter({"id_matricula": 1}, admin)
    assert again["id_asistencia"] == first["id_asistencia"]
    assert again["hora_salida"] == closed["hora_salida"]
    assert len(attendance.gym.state["asistencia"]) == 1
