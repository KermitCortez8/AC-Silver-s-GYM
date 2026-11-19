"""TC-153: límites temporales de la función pura, sin persistencia."""
from copy import deepcopy
from datetime import datetime

from domain.services.attendance_status import attendance_status, LIMA


def test_tc153_limites_inclusivos_precedencia_y_ninguna_mutacion():
    row = {"tipo": "general", "fecha": "2026-10-07", "hora_entrada": "10:00:00",
           "hora_salida": None, "limite_salida": "2026-10-07T13:00:00-05:00"}
    original = deepcopy(row)
    assert attendance_status(row, datetime(2026, 10, 7, 13, 0, tzinfo=LIMA)) == "dentro"
    assert attendance_status(row, datetime(2026, 10, 7, 13, 0, 1, tzinfo=LIMA)) == "incompleta"
    assert row == original
    assert attendance_status({**row, "hora_salida": "13:00:00"}) == "completada"
    assert attendance_status({**row, "hora_salida": "13:01:00"}) == "incompleta"
    assert attendance_status({**row, "anulado": True, "cierre_automatico": True}) == "anulada"
    assert attendance_status({**row, "cierre_automatico": True}) == "incompleta"
    assert row == original
