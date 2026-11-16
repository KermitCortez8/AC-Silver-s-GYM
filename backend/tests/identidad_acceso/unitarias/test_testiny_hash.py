"""TC-148: contrato criptográfico local; no se autentica contra proveedores."""
from infrastructure.security import hash_password, verify_password


def test_tc148_hash_no_revela_clave_y_solo_verifica_la_correcta():
    password = "clave-sintetica-qa"
    first = hash_password(password)
    second = hash_password(password)
    assert first != password and password not in first
    assert first != second  # Salt independiente, sin escribir cuentas ni sesiones.
    assert verify_password(password, first) is True
    assert verify_password("otra-clave-sintetica", first) is False
