"""SG-RF23-IT01: pago con tarjeta, reserva de stock y restauración del carrito."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[4]
SUPPORT = ROOT / "backend/tests/soporte/tienda_checkout_stripe"
QA_URL = "http://127.0.0.1:8013"


@pytest.mark.skipif(not os.getenv("GYM_TEST_STRIPE_CLI"), reason="Requiere Stripe CLI y sandbox optativo")
def test_tc195_checkout_stripe_reserva_stock_confirma_pago_y_restaura_carrito():
    node = shutil.which("node")
    assert node, "Instala Node y las dependencias de frontend y de Playwright"
    evidence = Path(os.getenv("GYM_TEST_STRIPE_ARTIFACTS", ROOT / ".artifacts/testiny-checkout-stripe")).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(24)
    environment = {**os.environ, "GYM_TEST_STRIPE_SHUTDOWN_KEY": key, "GYM_TEST_STRIPE_ARTIFACTS": str(evidence)}
    headers = {"X-QA-Key": key}
    api = subprocess.Popen([sys.executable, "-B", str(SUPPORT / "api.py")], cwd=ROOT, env=environment,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 50
        while time.monotonic() < deadline:
            assert api.poll() is None, "La API aislada o el listener de Stripe no pudo iniciarse"
            try:
                response = httpx.get(QA_URL + "/__qa/tc195", headers=headers, timeout=1)
                if response.status_code == 200 and response.json().get("qa") is True:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.3)
        else:
            pytest.fail("La API aislada de Stripe no quedó lista")

        execution = subprocess.run(
            [node, str(SUPPORT / "checkout.mjs")], cwd=ROOT / "frontend", env=environment, timeout=210,
            check=False, capture_output=True, encoding="utf-8", errors="replace",
        )
        assert execution.returncode == 0, execution.stdout + execution.stderr
    finally:
        if api.poll() is None:
            try:
                httpx.post(QA_URL + "/__qa/shutdown", headers=headers, timeout=2)
                api.wait(timeout=8)
            except (httpx.RequestError, subprocess.TimeoutExpired):
                api.kill()
                api.wait(timeout=5)
