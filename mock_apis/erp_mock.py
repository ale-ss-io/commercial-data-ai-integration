"""
Mock ERP API - simula el sistema ERP del cliente (facturas y pagos).
Expone GET /invoices con datos ficticios: pagadas, pendientes y vencidas.
Corre en el puerto 8002.
"""
from fastapi import FastAPI

app = FastAPI(title="Mock ERP API")

INVOICES = [
    {"invoice_id": "INV-1001", "customer_id": "C001", "amount": 45000, "invoice_date": "2026-05-10", "due_date": "2026-06-10", "payment_status": "paid"},
    {"invoice_id": "INV-1002", "customer_id": "C001", "amount": 62000, "invoice_date": "2026-06-15", "due_date": "2026-07-15", "payment_status": "overdue"},
    {"invoice_id": "INV-1003", "customer_id": "C001", "amount": 78000, "invoice_date": "2026-07-20", "due_date": "2026-08-20", "payment_status": "pending"},
    {"invoice_id": "INV-1004", "customer_id": "C002", "amount": 120000, "invoice_date": "2026-04-05", "due_date": "2026-05-05", "payment_status": "paid"},
    {"invoice_id": "INV-1005", "customer_id": "C002", "amount": 95000, "invoice_date": "2026-06-01", "due_date": "2026-07-01", "payment_status": "overdue"},
    {"invoice_id": "INV-1006", "customer_id": "C003", "amount": 30000, "invoice_date": "2026-03-12", "due_date": "2026-04-12", "payment_status": "overdue"},
    {"invoice_id": "INV-1007", "customer_id": "C004", "amount": 15000, "invoice_date": "2026-07-01", "due_date": "2026-08-01", "payment_status": "paid"},
    {"invoice_id": "INV-1008", "customer_id": "C004", "amount": 22000, "invoice_date": "2026-07-25", "due_date": "2026-08-25", "payment_status": "pending"},
    {"invoice_id": "INV-1009", "customer_id": "C005", "amount": 110000, "invoice_date": "2026-05-20", "due_date": "2026-06-20", "payment_status": "overdue"},
    {"invoice_id": "INV-1010", "customer_id": "C005", "amount": 48000, "invoice_date": "2026-07-10", "due_date": "2026-08-10", "payment_status": "pending"},
    {"invoice_id": "INV-1011", "customer_id": "C006", "amount": 60000, "invoice_date": "2026-02-15", "due_date": "2026-03-15", "payment_status": "overdue"},
    {"invoice_id": "INV-1012", "customer_id": "C007", "amount": 90000, "invoice_date": "2026-07-05", "due_date": "2026-08-05", "payment_status": "paid"},
    {"invoice_id": "INV-1013", "customer_id": "C008", "amount": 33000, "invoice_date": "2026-06-28", "due_date": "2026-07-28", "payment_status": "overdue"},
    {"invoice_id": "INV-1014", "customer_id": "C008", "amount": 27000, "invoice_date": "2026-07-30", "due_date": "2026-08-30", "payment_status": "pending"},
]


@app.get("/invoices")
def get_invoices():
    return INVOICES


@app.get("/health")
def health():
    return {"status": "ok"}