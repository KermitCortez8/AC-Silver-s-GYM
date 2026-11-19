"""Límite local y atómico de llamadas al proveedor, sin identificar visitantes."""

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from time import monotonic


class RateLimitExceeded(Exception):
    pass


class AgentBudget:
    """Cupo global por proceso; una cuota distribuida requerirá un almacén compartido."""

    def __init__(self, per_minute=10, per_day=100):
        self.per_minute = per_minute
        self.per_day = per_day
        self._lock = Lock()
        self._minute = deque()
        self._day = None
        self._daily_count = 0

    def reserve(self):
        now = monotonic()
        today = datetime.now(timezone.utc).date()
        with self._lock:
            if today != self._day:
                self._day = today
                self._daily_count = 0
            while self._minute and self._minute[0] <= now - 60:
                self._minute.popleft()
            if len(self._minute) >= self.per_minute or self._daily_count >= self.per_day:
                raise RateLimitExceeded("El asistente alcanzó su límite temporal. Inténtalo más tarde.")
            self._minute.append(now)
            self._daily_count += 1
