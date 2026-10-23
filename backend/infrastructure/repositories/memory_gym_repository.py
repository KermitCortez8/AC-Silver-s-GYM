"""Repositorio en memoria para pruebas y ejecución sin proveedores externos."""
from copy import deepcopy
import threading
import re

from domain.services.gym_domain_service import GymDomainService


class MemoryGymRepository:
    def __init__(self, state=None):
        self.lock = threading.RLock()
        self.state = state if state is not None else GymDomainService().state

    def _remember_identities(self):
        keys = {"usuario": "id_usuario", "clientes": "id_cliente", "membresia": "id_membresia",
                "planes_membresia": "id_pm", "promociones": "id_promocion", "inventario": "id_item",
                "productos_tienda": "id_producto", "pedidos_tienda": "id_pedido", "mov_inv": "id_mov",
                "catalogo_rutina": "id_rutina", "horario": "id_horario", "horarios_servicio": "id_horario_servicio",
                "matriculas_horario": "id_matricula", "rutina_progreso": "id_progreso",
                "tickets_atencion": "id_ticket", "asistencia": "id_asistencia"}
        floors = self.state.setdefault("_identity_floors", {})
        for table, key in keys.items():
            values = [int(match.group(1)) for row in self.state.get(table, [])
                      if (match := re.search(r"(\d+)$", str(row.get(key) or "")))]
            floors[table] = max(floors.get(table, 0), max(values, default=0))

    def read(self, operation, resources=None):
        with self.lock:
            return operation(deepcopy(self.state if resources is None else {key: self.state[key] for key in resources if key in self.state}))

    def change(self, operation, resources=None):
        with self.lock:
            self._remember_identities()
            previous = deepcopy(self.state)
            try:
                result = operation(self.state)
                self._remember_identities()
                return result
            except Exception:
                self.state.clear()
                self.state.update(previous)
                raise

    def refresh(self, resources=None):
        pass

    def validate_admin_registration_schema(self):
        pass

    def enroll(self, payload):
        return None

    def save_settings(self, payload):
        return None

    def save_attendance(self, row, expected_version, audit):
        return None

    # Compatibilidad con consumidores antiguos; los casos de uso usan change().
    def _mutate(self, operation, resources=None):
        return self.change(operation, resources)
