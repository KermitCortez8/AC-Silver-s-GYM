"""Identificadores históricos de clientes aceptados por los contratos públicos."""
import re
from typing import Any


def parse_client_id(raw_id_cliente: Any) -> int:
    try:
        if isinstance(raw_id_cliente, str):
            s = raw_id_cliente.strip()
            m = re.match(r"^(?:SGCLI|cliente-)?(\d+)$", s, re.IGNORECASE)
            if m:
                return int(m.group(1))
            if s.isdigit():
                return int(s)
        return int(raw_id_cliente)
    except Exception:
        return 0
