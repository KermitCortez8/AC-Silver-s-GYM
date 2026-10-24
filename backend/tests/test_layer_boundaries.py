"""Contratos de capas y sustitución de proveedores sin acceder a servicios reales."""
import ast
from copy import deepcopy
from pathlib import Path

import pytest

from application.services.clients_service import ClientsService
from application.services.gym_service import GymService
from domain.services.gym_domain_service import GymDomainService

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("layer,forbidden", [
    ("domain", {"application", "infrastructure", "presentation", "app", "fastapi"}),
    ("application", {"infrastructure", "presentation", "app", "fastapi"}),
    ("presentation/routes", {"infrastructure"}),
])
def test_imports_respect_layer_boundaries(layer, forbidden):
    for path in (BACKEND / layer).rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = ([node.module or ""] if isinstance(node, ast.ImportFrom)
                     else [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
            assert not any(name.split(".")[0] in forbidden for name in names), path


def test_persistence_does_not_inherit_domain_rules():
    from infrastructure.repositories.gym_repository import SupabaseGymRepository
    from infrastructure.repositories.memory_gym_repository import MemoryGymRepository
    assert not issubclass(SupabaseGymRepository, GymDomainService)
    assert not issubclass(MemoryGymRepository, GymDomainService)
    for path in (BACKEND / "infrastructure").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Attribute) or not node.attr.startswith("_"):
                continue
            # Repositorios y adaptadores deben usar las capacidades públicas del dominio.
            value = node.value
            uses_rules = isinstance(value, ast.Attribute) and value.attr == "rules"
            calls_rules = (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                           and value.func.attr == "_rules")
            assert not (uses_rules or calls_rules), f"{path}:{node.lineno}: {node.attr}"


class FakePasswords:
    def hash(self, value):
        return f"test:{value}"

    def verify(self, value, encoded):
        return encoded == self.hash(value)


class RecordingRepository:
    """Un proveedor alternativo que implementa el contrato público."""
    def __init__(self):
        self.data = GymDomainService().state
        self.writes = 0
        self.fail_commit = False

    def query(self, query, passwords=None):
        from domain.services.membership_lifecycle import apply_membership_expiration
        from domain.services.gym_domain_service import _today_iso
        snapshot = deepcopy({key: self.data.get(key, []) for key in query.resources})
        apply_membership_expiration(snapshot, _today_iso())
        return deepcopy(query.run(GymDomainService(snapshot, passwords).components))

    def execute(self, command, passwords=None):
        return deepcopy(self.change(lambda state: command.run(GymDomainService(state, passwords).components), command.resources))

    def read(self, operation, resources=None):
        return operation(self.data)

    def change(self, operation, resources=None):
        candidate = deepcopy(self.data)
        result = operation(candidate)
        if self.fail_commit:
            raise RuntimeError("storage unavailable")
        self.data = candidate
        self.writes += 1
        return result

    def refresh(self, resources=None):
        pass

    def validate_admin_registration_schema(self):
        pass


def test_client_registration_uses_injected_repository_and_hasher():
    repository = RecordingRepository()
    service = GymService(repository, FakePasswords())
    result = ClientsService(service).register_admin_client({
        "nombre": "Ana", "correo": "ana@example.com", "dni": "12345678",
        "password": "secreto123", "plan": "MENSUAL",
    })
    assert repository.writes == 1
    assert repository.data["clientes"][0]["password_hash"] == "test:secreto123"
    assert "password_hash" not in result["cliente"]
    assert result["membresia"]["estado_pago"] == "PENDIENTE"
    result["membresia"]["monto_pago"] = 0
    assert service.latest_membership(result["cliente"]["id_cliente"])["monto_pago"] == 79


def test_read_results_cannot_mutate_persisted_state_and_failed_commit_propagates():
    repository = RecordingRepository()
    service = GymService(repository, FakePasswords())
    plans = service.planes_membresia()
    plans[0]["precio"] = 0
    assert service.planes_membresia()[0]["precio"] == 79

    repository.fail_commit = True
    with pytest.raises(RuntimeError, match="storage unavailable"):
        service.upsert_plan_membresia({"id_pm": 1, "nombre_plan": "MENSUAL", "precio": 10})
    assert repository.writes == 0
    assert service.planes_membresia()[0]["precio"] == 79


def test_unpaid_order_expiration_releases_reserved_stock_through_application():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from application.services.store_checkout_service import procesar_pedidos_pendientes

    repository = RecordingRepository()
    repository.data["productos_tienda"] = [{
        "id_producto": 1, "nombre_producto": "Agua", "cantidad_stock": 5,
        "precio_venta": 2, "estado": "Disponible",
    }]
    service = GymService(repository, FakePasswords())
    order = service.crear_pedido_tienda_pago_pendiente({"items": [{"id_producto": 1, "cantidad": 2}]})
    assert service.get_producto_tienda(1)["cantidad_stock"] == 3
    repository.data["pedidos_tienda"][0]["creado_en"] = (datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat()
    procesar_pedidos_pendientes(service, SimpleNamespace(), SimpleNamespace())
    assert service.get_pedido_tienda(order["id_pedido"])["estado_pedido"] == "CANCELADO"
    assert service.get_producto_tienda(1)["cantidad_stock"] == 5
