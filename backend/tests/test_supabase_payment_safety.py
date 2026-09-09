from __future__ import annotations

import pytest

from services.supabase_gym_service import SupabaseGymService


def _service_with_validator(error: RuntimeError | None) -> SupabaseGymService:
    class FakeSupabase:
        def validate_columns(self, _table: str, _columns: set[str]) -> None:
            if error:
                raise error

    service = object.__new__(SupabaseGymService)
    service.supabase = FakeSupabase()
    return service


def test_payment_schema_reports_missing_migration() -> None:
    service = _service_with_validator(RuntimeError(
        "PGRST204: Could not find the 'monto_pago' column",
    ))

    with pytest.raises(RuntimeError, match="001_add_membership_payment_fields.sql"):
        service._validate_payment_schema()


def test_payment_schema_does_not_hide_connection_errors() -> None:
    service = _service_with_validator(RuntimeError("Supabase GET MEMBRESIA fallo (401)"))

    with pytest.raises(RuntimeError, match="401"):
        service._validate_payment_schema()
