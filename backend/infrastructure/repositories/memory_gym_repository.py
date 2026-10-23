"""Repositorio en memoria para pruebas y ejecución sin proveedores externos."""
from copy import deepcopy
import threading

from domain.services.gym_domain_service import GymDomainService


class MemoryGymRepository:
    def __init__(self, state=None):
        self.lock = threading.RLock()
        self.state = state if state is not None else GymDomainService().state

    def read(self, operation):
        with self.lock:
            return operation(self.state)

    def change(self, operation, resources=None):
        with self.lock:
            previous = deepcopy(self.state)
            try:
                return operation(self.state)
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
