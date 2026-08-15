"""
Mock CRM API - simula el sistema CRM del cliente.
Expone GET /customers con datos ficticios de clientes.
Corre en el puerto 8001.
"""
from fastapi import FastAPI

app = FastAPI(title="Mock CRM API")

CUSTOMERS = [
    {"customer_id": "C001", "name": "Comercial ABC", "industry": "Retail", "sales_rep": "Laura Pérez", "email": "contacto@abc.com", "status": "active"},
    {"customer_id": "C002", "name": "Industrias del Norte", "industry": "Manufactura", "sales_rep": "Jorge Ruiz", "email": "ventas@norte.com", "status": "active"},
    {"customer_id": "C003", "name": "Grupo Torres", "industry": "Construcción", "sales_rep": "Laura Pérez", "email": "info@torres.com", "status": "inactive"},
    {"customer_id": "C004", "name": "Tecnología Andina", "industry": "Tecnología", "sales_rep": "Marco Solís", "email": "hola@andina.com", "status": "active"},
    {"customer_id": "C005", "name": "Distribuidora Central", "industry": "Logística", "sales_rep": "Jorge Ruiz", "email": "compras@central.com", "status": "active"},
    {"customer_id": "C006", "name": "Alimentos del Valle", "industry": "Alimentos", "sales_rep": "Marco Solís", "email": "contacto@valle.com", "status": "churned"},
    {"customer_id": "C007", "name": "Farmacéutica Global", "industry": "Salud", "sales_rep": "Laura Pérez", "email": "ventas@farmaglobal.com", "status": "active"},
    {"customer_id": "C008", "name": "Muebles y Diseño SA", "industry": "Mobiliario", "sales_rep": "Jorge Ruiz", "email": "info@mueblesdesign.com", "status": "active"},
]


@app.get("/customers")
def get_customers():
    return CUSTOMERS


@app.get("/health")
def health():
    return {"status": "ok"}