"""TC-178: traza descriptiva de lecturas concurrentes del adaptador QA."""
import json
import threading
from time import perf_counter

from tests.paneles_configuracion.integracion.test_supabase_refresh import service_with_remote


def test_tc178_registra_inicio_fin_errores_y_maximo_de_conexiones(record_property):
    barrier = threading.Barrier(6)
    lock = threading.Lock()
    trace = []
    counters = {"active": 0, "peak": 0}

    class Remote:
        def select(self, table, order=None):
            with lock:
                row = {"table": table, "start": perf_counter(), "error": None}
                trace.append(row)
                position = len(trace)
                counters["active"] += 1
                counters["peak"] = max(counters["peak"], counters["active"])
            try:
                if position <= 6:
                    barrier.wait(timeout=5)
                return []
            except Exception as error:
                row["error"] = type(error).__name__
                raise
            finally:
                with lock:
                    row["end"] = perf_counter()
                    counters["active"] -= 1
        select_all = select

    started = perf_counter()
    service_with_remote(Remote()).ensure_fresh()
    elapsed = perf_counter() - started
    assert len(trace) == 19 and counters == {"active": 0, "peak": 6}
    assert all(row["end"] >= row["start"] and row["error"] is None for row in trace)
    assert max(row["start"] for row in trace[:6]) <= min(row["end"] for row in trace[:6])
    record_property("qa_lecturas", json.dumps(trace))
    record_property("qa_conexiones_maximas", counters["peak"])
    record_property("qa_segundos", elapsed)
