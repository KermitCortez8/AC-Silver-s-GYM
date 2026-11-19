"""TC-179: medición reproducible de 50 filas con límite parcial del proveedor."""
from io import BytesIO
import json
from time import perf_counter
from urllib.parse import parse_qs, urlsplit

from infrastructure.supabase_client import SupabaseRestClient


def test_tc179_completa_cincuenta_filas_filtradas_sin_duplicados(monkeypatch, record_property):
    calls = []
    transferred = []
    def opener(request, timeout):
        query = parse_qs(urlsplit(request.full_url).query)
        assert query["id_cliente"] == ["eq.7"]
        assert query["tipo"] == ["eq.general"]
        assert request.get_header("Prefer") == "count=exact"
        offset, limit = int(query["offset"][0]), int(query["limit"][0])
        calls.append((offset, limit))
        rows = [{"id_asistencia": n, "id_cliente": 7, "tipo": "general"} for n in range(offset, min(offset + 7, offset + limit, 85))]
        transferred.extend(rows)
        response = BytesIO(json.dumps(rows).encode())
        response.headers = {"Content-Range": f"{offset}-{offset + len(rows) - 1}/85"}
        return response
    monkeypatch.setattr("infrastructure.supabase_client.urlopen", opener)
    start = perf_counter()
    page = SupabaseRestClient("https://example.invalid", "synthetic").select_page(
        "ASISTENCIA", {"id_cliente": "eq.7", "tipo": "eq.general"}, order="id_asistencia.asc", offset=0, limit=50)
    elapsed = perf_counter() - start
    assert len(page.rows) == len(transferred) == 50 and page.total == 85
    assert [row["id_asistencia"] for row in page.rows] == list(range(50))
    assert all(row["id_cliente"] == 7 for row in page.rows)
    assert [offset for offset, _limit in calls] == [0, 7, 14, 21, 28, 35, 42, 49]
    record_property("qa_filas_transferidas", len(transferred))
    record_property("qa_consultas", len(calls))
    record_property("qa_segundos", elapsed)
