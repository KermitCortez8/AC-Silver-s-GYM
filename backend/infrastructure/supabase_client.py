"""Cliente REST de Supabase compartido por los repositorios."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import urlopen
from infrastructure.http_transport import json_request, supabase_headers, send_response, RemoteServiceError
from urllib.request import Request

@dataclass(frozen=True)
class RowsPage:
    rows: list[dict]
    total: int


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

        headers = {**supabase_headers(self.key),
                   "Prefer": "return=representation" if return_representation else "return=minimal"}
        result = json_request(url, method=method, headers=headers, body=body,
                              context=f"Supabase {method} {table}", opener=urlopen)
        return result if result is not None else []

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

    def select_filtered(self, table, filters, *, order):
        rows = []
        while True:
            page = self._request("GET", table, query={"select": "*", "order": order,
                "offset": len(rows), "limit": 1000, **filters})
            if not page:
                return rows
            rows.extend(page)

    def select_page(self, table, filters, *, order, offset, limit):
        if offset < 0 or limit < 1 or limit > 100:
            raise ValueError("Rango de consulta inválido")
        rows, total = [], None
        while len(rows) < limit and (total is None or offset + len(rows) < total):
            query = {"select": "*", "order": order, **filters,
                     "offset": offset + len(rows), "limit": limit - len(rows)}
            try:
                page, count = self._counted_page(table, query)
            except RemoteServiceError as error:
                if error.status != 416 or error.code != "PGRST103":
                    raise
                _, count = self._counted_page(table, {"select": "*", **filters, "limit": 0})
                return RowsPage(rows, count)
            total = count
            if not page:
                break
            rows.extend(page)
        return RowsPage(rows, total or 0)

    def count(self, table, filters):
        _, total = self._counted_page(table, {"select": "*", **filters, "limit": 0})
        return total

    def _counted_page(self, table, query):
        address = f"{self.rest_url}/{quote(table, safe='')}?{urlencode(query, safe='*,().:')}"
        headers = {**supabase_headers(self.key), "Prefer": "count=exact"}
        raw, response_headers = send_response(Request(address, headers=headers),
            context=f"Supabase GET {table}", opener=urlopen)
        content_range = next((v for k, v in response_headers.items() if k.lower() == "content-range"), "")
        total = content_range.rsplit("/", 1)[-1]
        if not total.isdigit():
            raise RuntimeError("El servidor no devolvió el total de la consulta paginada")
        rows = json.loads(raw) if raw else []
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise RuntimeError("El servidor devolvió una página inválida")
        return rows, int(total)

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
        return json_request(url, method="POST", headers={**supabase_headers(self.key), "Prefer": "return=representation"},
                            body=body, context=f"Supabase RPC {function_name}", opener=urlopen)

    def update_matching(self, table: str, filters: dict[str, Any], body: dict[str, Any]):
        """Actualización condicional que devuelve las filas realmente modificadas."""
        return self._request("PATCH", table, query=filters, body=body, return_representation=True)

    # Actualiza el registro correspondiente.
    def update(self, table: str, pk_column: str, pk_value: Any, body: dict[str, Any]) -> None:
        self._request("PATCH", table, query={pk_column: f"eq.{pk_value}"}, body=body)

    # Elimina el registro indicado.
    def delete(self, table: str, pk_column: str, pk_value: Any) -> None:
        self._request("DELETE", table, query={pk_column: f"eq.{pk_value}"})

    # Elimina el registro indicado.
    def delete_where(self, table: str, column: str, value: Any) -> None:
        self._request("DELETE", table, query={column: f"eq.{value}"})

