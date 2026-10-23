"""Planifica cambios; PostgreSQL los valida y confirma en una sola transacción."""
from infrastructure.http_transport import database_code


class SnapshotConflict(RuntimeError):
    """Otra petición modificó la instantánea antes de confirmarla."""


def table_changes(table, pk, previous, current):
    before = {row[pk]: row for row in previous}
    after = {row[pk]: row for row in current}
    operations = []
    for identity in before.keys() - after.keys():
        operations.append({"table": table, "pk": pk, "action": "delete", "id": identity})
    for identity, row in after.items():
        if identity not in before or row != before[identity]:
            operations.append({"table": table, "pk": pk, "action": "insert" if identity not in before else "update",
                               "id": identity, "body": row})
    return operations


def commit_snapshot(database, expected, operations):
    try:
        result = database.rpc("commit_gym_transaction", {"p_expected": expected, "p_operations": operations})
    except RuntimeError as error:
        code = database_code(error)
        if code in {"40001", "40P01"}:
            raise SnapshotConflict("Los datos cambiaron durante la operación") from error
        if code in {"PGRST202", "42883"}:
            raise RuntimeError("Falta ejecutar backend/migrations/015_atomic_gym_transactions.sql en Supabase") from error
        raise
    if not isinstance(result, dict) or not isinstance(result.get("tables"), dict):
        raise RuntimeError("La base de datos no devolvió la confirmación de la transacción")
    return result["tables"]
