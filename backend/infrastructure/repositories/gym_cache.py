"""Estado y relojes locales protegidos por un único bloqueo."""
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
import threading

from domain.services.gym_domain_service import GymDomainService


@dataclass
class GymCache:
    state: dict[str, Any] = field(default_factory=lambda: GymDomainService().state)
    raw_rows: dict = field(default_factory=dict)
    last_refresh_at: float = 0.0
    resource_refreshed_at: dict[str, float] = field(default_factory=dict)
    lock: Any = field(default_factory=threading.Lock)

    def read(self, operation, resources=None):
        with self.lock:
            selected = self.state if resources is None else {key: self.state[key] for key in resources if key in self.state}
            return operation(deepcopy(selected))

    def invalidate(self):
        self.last_refresh_at = 0.0
        self.resource_refreshed_at.clear()


