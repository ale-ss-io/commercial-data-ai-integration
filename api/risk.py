from datetime import date
from typing import Iterable, Literal

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]

# Umbrales centralizados: fáciles de ajustar o mover a config/env sin tocar la lógica
HIGH_BALANCE_THRESHOLD = 100_000
HIGH_DAYS_OVERDUE = 60
MEDIUM_DAYS_OVERDUE = 15


def compute_overdue_days(due_date: date, today: date) -> int:
    return max((today - due_date).days, 0)


def compute_risk_level(
    outstanding_balance: float,
    overdue_invoice_days: Iterable[int],
) -> RiskLevel:
    """
    overdue_invoice_days: días de atraso de cada factura NO pagada y vencida
    (lista vacía si no hay ninguna vencida).

    Regla de negocio (documentada también en el README):
    - HIGH: saldo vencido > $100,000 O alguna factura con más de 60 días de atraso.
    - MEDIUM: existe al menos una factura vencida, pero por debajo de esos umbrales.
    - LOW: no hay facturas vencidas.
    """
    overdue_invoice_days = list(overdue_invoice_days)

    if not overdue_invoice_days:
        return "LOW"

    max_days = max(overdue_invoice_days)

    if outstanding_balance > HIGH_BALANCE_THRESHOLD or max_days > HIGH_DAYS_OVERDUE:
        return "HIGH"

    return "MEDIUM"
