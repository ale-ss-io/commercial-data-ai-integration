from datetime import date

from api.risk import compute_risk_level, compute_overdue_days


def test_no_overdue_invoices_is_low_risk():
    assert compute_risk_level(
        outstanding_balance=0,
        overdue_invoice_days=[]
    ) == "LOW"


def test_small_overdue_balance_is_medium_risk():
    assert compute_risk_level(
        outstanding_balance=5000,
        overdue_invoice_days=[10]
    ) == "MEDIUM"


def test_high_balance_is_high_risk_even_if_recently_overdue():
    assert compute_risk_level(
        outstanding_balance=150_000,
        overdue_invoice_days=[5]
    ) == "HIGH"


def test_long_overdue_is_high_risk_even_with_small_balance():
    assert compute_risk_level(
        outstanding_balance=1000,
        overdue_invoice_days=[90]
    ) == "HIGH"


def test_takes_the_max_days_among_multiple_invoices():
    assert compute_risk_level(
        outstanding_balance=1000,
        overdue_invoice_days=[5, 70, 10]
    ) == "HIGH"


def test_compute_overdue_days_never_negative():
    future_due_date = date(2099, 1, 1)

    assert compute_overdue_days(
        future_due_date,
        date(2026, 8, 14)
    ) == 0