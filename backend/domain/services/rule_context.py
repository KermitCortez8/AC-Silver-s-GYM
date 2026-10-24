"""Estado de una transacción y utilidades compartidas por las reglas."""
from dataclasses import dataclass, field
from typing import Any, Callable
from domain.ports import PasswordHasher
from domain.services.membership_lifecycle import apply_membership_expiration
from domain.services import gym_values


@dataclass
class RuleContext:
    state: dict[str, Any]
    passwords: PasswordHasher | None = None
    today_provider: Callable[[], str] = field(default_factory=lambda: gym_values._today_iso)
    now_provider: Callable[[], str] = field(default_factory=lambda: gym_values._now_iso)

    def change(self, operation):
        return operation(self.state)

    def today(self):
        return self.today_provider()

    def now(self):
        return self.now_provider()

    def safe_date(self, value):
        return value if value else self.today()

    def next_int_id(self, table, key):
        return self.next_int_id_in_state(self.state, table, key)

    def next_int_id_in_state(self, state, table, key):
        rows = state.setdefault(table, [])
        return max(int(state.get("_identity_floors", {}).get(table, 0)),
                   max((int(row.get(key, 0) or 0) for row in rows), default=0)) + 1

    def expire_memberships(self):
        return apply_membership_expiration(self.state, self.today())
