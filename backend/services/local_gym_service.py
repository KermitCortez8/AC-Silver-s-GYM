from __future__ import annotations

import threading
from typing import Any

from services.gym_domain_service import GymDomainService


class LocalGymService(GymDomainService):
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.state = self._normalize(self._seed())

    def ensure_fresh(self) -> None:
        return None

    def _save(self) -> None:
        return None
