from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel


class CustomerOut(BaseModel):
    customer_id: str
    name: str
    industry: Optional[str] = None
    sales_rep: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    invoice_id: str
    amount: float
    invoice_date: date
    due_date: date
    payment_status: str

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    date: date
    product: str
    quantity: float
    unit_price: float

    class Config:
        from_attributes = True


class CustomerSummary(BaseModel):
    customer: str
    total_sales: float
    outstanding_balance: float
    overdue_invoices: int
    last_purchase: Optional[date] = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]


class AtRiskCustomer(BaseModel):
    customer_id: str
    customer: str
    outstanding_balance: float
    overdue_invoices: int
    risk_level: Literal["MEDIUM", "HIGH"]
