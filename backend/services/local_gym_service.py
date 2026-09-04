# Módulo: local_gym_service.
# Ejecuta el dominio con almacenamiento local en memoria.
# Se utiliza cuando Supabase no está disponible o configurado.
# Conserva la misma interfaz que el servicio remoto.
from __future__ import annotations

import threading
from typing import Any

from services.gym_domain_service import GymDomainService


class LocalGymService(GymDomainService):
    # Inicializa la clase.
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.state = self._normalize(self._seed())

    # Procesa esta operación.
    def ensure_fresh(self) -> None:
        return None

    # Procesa esta operación.
    def _save(self) -> None:
        return None
