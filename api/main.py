from datetime import date
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import func

from api.db import get_db
from api.models import Customer, Invoice, Sale
from api.schemas import (
    CustomerOut,
    InvoiceOut,
    SaleOut,
    CustomerSummary,
    AtRiskCustomer,
)
from api.security import verify_api_key
from api.risk import compute_overdue_days, compute_risk_level


app = FastAPI(title="Commercial Data & AI Integration API")


# ---- Resiliencia: DB no disponible -> 503 en vez de 500 genérico ----

@app.exception_handler(OperationalError)
async def db_down_handler(request, exc: OperationalError):
    return _service_unavailable()


def _service_unavailable():
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=503,
        content={
            "detail": "Base de datos no disponible temporalmente. "
            "Intenta de nuevo en unos segundos."
        },
    )


def _get_customer_or_404(db: Session, customer_id: str) -> Customer:
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente {customer_id} no encontrado",
        )

    return customer


@app.get("/health")
def health():
    """Endpoint sin auth para healthchecks de docker-compose / load balancer."""
    return {"status": "ok"}


@app.get(
    "/customers",
    response_model=List[CustomerOut],
    dependencies=[Depends(verify_api_key)],
)
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()


@app.get(
    "/customers/at-risk",
    response_model=List[AtRiskCustomer],
    dependencies=[Depends(verify_api_key)],
)
def get_customers_at_risk(db: Session = Depends(get_db)):
    today = date.today()
    results = []

    for customer in db.query(Customer).all():
        summary = _build_summary(db, customer, today)

        if summary.risk_level in ("MEDIUM", "HIGH"):
            results.append(
                AtRiskCustomer(
                    customer_id=customer.customer_id,
                    customer=customer.name,
                    outstanding_balance=summary.outstanding_balance,
                    overdue_invoices=summary.overdue_invoices,
                    risk_level=summary.risk_level,
                )
            )

    # Los más riesgosos primero
    results.sort(
        key=lambda r: (
            r.risk_level != "HIGH",
            -r.outstanding_balance,
        )
    )

    return results


@app.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    dependencies=[Depends(verify_api_key)],
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    return _get_customer_or_404(db, customer_id)


@app.get(
    "/customers/{customer_id}/sales",
    response_model=List[SaleOut],
    dependencies=[Depends(verify_api_key)],
)
def get_customer_sales(
    customer_id: str,
    db: Session = Depends(get_db),
):
    _get_customer_or_404(db, customer_id)

    return (
        db.query(Sale)
        .filter(Sale.customer_id == customer_id)
        .order_by(Sale.sale_date.desc())
        .all()
    )


@app.get(
    "/customers/{customer_id}/invoices",
    response_model=List[InvoiceOut],
    dependencies=[Depends(verify_api_key)],
)
def get_customer_invoices(
    customer_id: str,
    db: Session = Depends(get_db),
):
    _get_customer_or_404(db, customer_id)

    return (
        db.query(Invoice)
        .filter(Invoice.customer_id == customer_id)
        .order_by(Invoice.due_date.desc())
        .all()
    )


def _build_summary(
    db: Session,
    customer: Customer,
    today: date,
) -> CustomerSummary:

    total_sales = (
        db.query(
            func.coalesce(
                func.sum(Sale.quantity * Sale.unit_price),
                0,
            )
        )
        .filter(Sale.customer_id == customer.customer_id)
        .scalar()
    )

    last_purchase = (
        db.query(func.max(Sale.sale_date))
        .filter(Sale.customer_id == customer.customer_id)
        .scalar()
    )

    unpaid_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.customer_id == customer.customer_id,
            Invoice.payment_status != "paid",
        )
        .all()
    )

    outstanding_balance = sum(
        float(inv.amount)
        for inv in unpaid_invoices
    )

    overdue = [
        inv
        for inv in unpaid_invoices
        if inv.due_date < today
    ]

    overdue_days = [
        compute_overdue_days(inv.due_date, today)
        for inv in overdue
    ]

    risk_level = compute_risk_level(
        outstanding_balance,
        overdue_days,
    )

    return CustomerSummary(
        customer=customer.name,
        total_sales=float(total_sales),
        outstanding_balance=outstanding_balance,
        overdue_invoices=len(overdue),
        last_purchase=last_purchase,
        risk_level=risk_level,
    )


@app.get(
    "/customers/{customer_id}/summary",
    response_model=CustomerSummary,
    dependencies=[Depends(verify_api_key)],
)
def get_customer_summary(
    customer_id: str,
    db: Session = Depends(get_db),
):
    customer = _get_customer_or_404(db, customer_id)

    return _build_summary(
        db,
        customer,
        date.today(),
    )
