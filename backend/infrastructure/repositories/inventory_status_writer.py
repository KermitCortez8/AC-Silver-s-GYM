"""Reconciliación explícita del estado de inventario para consumidores anteriores."""
from typing import Any
from domain.services.gym_domain_service import GymDomainService


class InventoryStatusWriter:
    def __init__(self, database, metadata):
        self.database, self.metadata = database, metadata



    def reconcile(self, rows: list[dict[str, Any]], state: dict[str, Any]) -> None:
        if "INVENTARIO" in self.metadata.missing_tables:
            return
        remotos = {int(row.get("id_item", 0) or 0): str(row.get("Estado") or "") for row in rows}
        for item in state.get("inventario", []):
            id_item = int(item.get("id_item", 0) or 0)
            estado = str(item.get("estado") or "")
            if not GymDomainService(state).is_store_inventory(item) or id_item not in remotos or remotos[id_item] == estado:
                continue
            try:
                self.database.update("INVENTARIO", "id_item", id_item, {"Estado": estado})
            except RuntimeError:
                item["estado"] = remotos[id_item]
