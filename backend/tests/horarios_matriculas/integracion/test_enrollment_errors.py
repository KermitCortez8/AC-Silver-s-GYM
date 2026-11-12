"""Los errores del repositorio conservan sus mensajes de negocio y su causa."""
import pytest

from infrastructure.repositories.gym_repository import SupabaseGymRepository


@pytest.mark.parametrize("database_error,message", [
    ("23505: duplicate key", "El cliente ya esta matriculado en este horario"),
    ("SIN CUPOS", "Horario sin cupos disponibles"),
    ("sin membresia activa", "Cliente sin membresia activa"),
    ("23503: foreign key violation", "Horario no disponible"),
])
def test_enrollment_errors_keep_their_business_meaning(database_error, message):
    error = RuntimeError(database_error)

    with pytest.raises(ValueError) as raised:
        SupabaseGymRepository._raise_schedule_enrollment_error(error)

    assert str(raised.value) == message
    assert raised.value.__cause__ is error


def test_unknown_storage_error_is_not_hidden_as_a_validation_error():
    error = RuntimeError("database connection lost")

    with pytest.raises(RuntimeError) as raised:
        SupabaseGymRepository._raise_schedule_enrollment_error(error)

    assert raised.value is error
