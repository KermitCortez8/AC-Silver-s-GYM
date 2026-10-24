"""Importes en céntimos; redondeo decimal a la mitad hacia arriba."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def cents(value) -> int:
    try:
        return int((Decimal(str(value or 0)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError) as error:
        raise ValueError("Importe monetario inválido") from error


def discounted_price(price, discount, kind="porcentaje") -> float:
    base = cents(price)
    if kind == "monto":
        reduction = cents(discount)
    else:
        percentage = Decimal(str(discount or 0)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        reduction = int((Decimal(base) * percentage / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(0, base - reduction) / 100


def order_totals(subtotal_cents: int) -> dict[str, float]:
    tax = int((Decimal(subtotal_cents) * Decimal("0.18")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {"subtotal": subtotal_cents / 100, "igv": tax / 100, "total": (subtotal_cents + tax) / 100}
