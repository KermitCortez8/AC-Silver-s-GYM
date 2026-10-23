"""Cliente REST de Supabase compartido por los repositorios."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

class SupabaseRestClient:
    # Inicializa la clase.
    def __init__(self, url: str, key: str) -> None:
        self.rest_url = f"{url.rstrip('/')}/rest/v1"
        self.key = key

    # Procesa esta operación.
    def _request(
        self,
        method: str,
        table: str,
        query: dict[str, Any] | None = None,
        body: Any | None = None,
        return_representation: bool = False,
    ) -> Any:
        encoded_table = quote(table, safe="")
        query_string = urlencode(query or {}, doseq=True, safe="*,().:")
        url = f"{self.rest_url}/{encoded_table}"
        if query_string:
            url = f"{url}?{query_string}"

        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation" if return_representation else "return=minimal",
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {method} {table} fallo ({error.code}): {details}") from error

        if not raw:
            return []
        return json.loads(raw)

    # Procesa esta operación.
    def select(self, table: str, order: str | None = None) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"select": "*"}
        if order:
            query["order"] = order
        rows = self._request("GET", table, query=query, return_representation=True)
        return rows if isinstance(rows, list) else []

    def validate_columns(self, table: str, columns: set[str]) -> None:
        """Pide explícitamente las columnas para que PostgREST detecte una migración faltante."""
        self._request(
            "GET",
            table,
            query={"select": ",".join(sorted(columns)), "limit": 1},
            return_representation=True,
        )

    def select_all(self, table: str, order: str) -> list[dict[str, Any]]:
        rows = []
        # Respeta también instalaciones con un límite de PostgREST menor a 1000.
        while True:
            page = self._request("GET", table, query={"select": "*", "order": order,
                                                     "offset": len(rows), "limit": 1000})
            if not page:
                return rows
            rows.extend(page)

    # Procesa esta operación.
    def insert(
        self,
        table: str,
        body: dict[str, Any] | list[dict[str, Any]],
        return_representation: bool = False,
    ) -> Any:
        return self._request("POST", table, body=body, return_representation=return_representation)

    def rpc(self, function_name: str, body: dict[str, Any]) -> Any:
        url = f"{self.rest_url}/rpc/{quote(function_name, safe='')}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        request = Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Supabase RPC {function_name} fallo ({error.code}): {details}"
            ) from error
        return json.loads(raw) if raw else None

    # Actualiza el registro correspondiente.
    def update(self, table: str, pk_column: str, pk_value: Any, body: dict[str, Any]) -> None:
        self._request("PATCH", table, query={pk_column: f"eq.{pk_value}"}, body=body)

    # Elimina el registro indicado.
    def delete(self, table: str, pk_column: str, pk_value: Any) -> None:
        self._request("DELETE", table, query={pk_column: f"eq.{pk_value}"})

    # Elimina el registro indicado.
    def delete_where(self, table: str, column: str, value: Any) -> None:
        self._request("DELETE", table, query={column: f"eq.{value}"})

