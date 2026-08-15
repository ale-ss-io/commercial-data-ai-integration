"""
Pipeline ETL - Febara Data & AI Integration
=============================================
Extrae datos de CRM (API), ERP (API) y ventas (CSV), los limpia/normaliza,
y los carga en PostgreSQL de forma idempotente (se puede correr N veces
sin duplicar información).

Uso:
    python pipeline/etl.py
"""
import os
import sys
import csv
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("etl")

# ------------------------------------------------------------------
# Configuración (desde variables de entorno / .env)
# ------------------------------------------------------------------
CRM_URL = os.getenv("CRM_URL", "http://localhost:8001/customers")
ERP_URL = os.getenv("ERP_URL", "http://localhost:8002/invoices")
SALES_CSV_PATH = os.getenv("SALES_CSV_PATH", "data/ventas.csv")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

REQUEST_TIMEOUT_SECONDS = 5
VALID_PAYMENT_STATUSES = {"paid", "pending", "overdue"}


# ------------------------------------------------------------------
# EXTRACT
# ------------------------------------------------------------------
def extract_crm():
    try:
        resp = requests.get(CRM_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        log.info(f"CRM: {len(data)} clientes extraídos")
        return data
    except requests.exceptions.Timeout:
        log.error("CRM no respondió a tiempo (timeout). Se omite esta fuente en esta corrida.")
        return []
    except requests.exceptions.RequestException as e:
        log.error(f"CRM no disponible: {e}. Se omite esta fuente en esta corrida.")
        return []


def extract_erp():
    try:
        resp = requests.get(ERP_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        log.info(f"ERP: {len(data)} facturas extraídas")
        return data
    except requests.exceptions.Timeout:
        log.error("ERP tardó demasiado (timeout). Se omite esta fuente en esta corrida.")
        return []
    except requests.exceptions.RequestException as e:
        log.error(f"ERP no disponible: {e}. Se omite esta fuente en esta corrida.")
        return []


def extract_sales_csv(path=SALES_CSV_PATH):
    if not os.path.exists(path):
        log.error(f"No se encontró el archivo CSV en {path}. Se omite esta fuente.")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    log.info(f"CSV: {len(rows)} filas crudas leídas")
    return rows


# ------------------------------------------------------------------
# TRANSFORM
# ------------------------------------------------------------------
def parse_flexible_date(raw_value: str):
    if not raw_value or not raw_value.strip():
        return None

    raw_value = raw_value.strip()
    formats_to_try = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]

    for fmt in formats_to_try:
        try:
            return datetime.strptime(raw_value, fmt).date()
        except ValueError:
            continue

    log.warning(f"Fecha con formato no reconocido, se descarta: '{raw_value}'")
    return None


def transform_customers(raw_customers):
    clean = []
    for c in raw_customers:
        customer_id = (c.get("customer_id") or "").strip()
        if not customer_id:
            log.warning(f"Cliente sin customer_id, se descarta: {c}")
            continue
        clean.append({
            "customer_id": customer_id,
            "name": (c.get("name") or "").strip() or "Sin nombre",
            "industry": c.get("industry"),
            "sales_rep": c.get("sales_rep"),
            "email": c.get("email"),
            "status": c.get("status") or "unknown",
        })
    log.info(f"Transform CRM: {len(clean)}/{len(raw_customers)} clientes válidos")
    return clean


def transform_invoices(raw_invoices):
    clean = []
    for inv in raw_invoices:
        invoice_id = (inv.get("invoice_id") or "").strip()
        customer_id = (inv.get("customer_id") or "").strip()
        if not invoice_id or not customer_id:
            log.warning(f"Factura sin invoice_id/customer_id, se descarta: {inv}")
            continue

        try:
            amount = Decimal(str(inv.get("amount")))
        except (InvalidOperation, TypeError):
            log.warning(f"Factura {invoice_id} con amount inválido, se descarta")
            continue

        invoice_date = parse_flexible_date(str(inv.get("invoice_date", "")))
        due_date = parse_flexible_date(str(inv.get("due_date", "")))
        if not invoice_date or not due_date:
            log.warning(f"Factura {invoice_id} con fechas inválidas, se descarta")
            continue

        status = (inv.get("payment_status") or "").strip().lower()
        if status not in VALID_PAYMENT_STATUSES:
            log.warning(f"Factura {invoice_id} con payment_status desconocido '{status}', se marca 'pending'")
            status = "pending"

        clean.append({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "amount": amount,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "payment_status": status,
        })
    log.info(f"Transform ERP: {len(clean)}/{len(raw_invoices)} facturas válidas")
    return clean


def transform_sales(raw_sales):
    clean = []
    seen_keys = set()

    for row in raw_sales:
        customer_id = (row.get("customer_id") or "").strip()
        product = (row.get("product") or "").strip()
        raw_date = row.get("date", "")

        if not customer_id or not product:
            log.warning(f"Venta con campos vacíos, se descarta: {row}")
            continue

        sale_date = parse_flexible_date(raw_date)
        if not sale_date:
            log.warning(f"Venta con fecha inválida/vacía, se descarta: {row}")
            continue

        try:
            quantity = Decimal(str(row.get("quantity")))
            unit_price = Decimal(str(row.get("unit_price")))
        except (InvalidOperation, TypeError):
            log.warning(f"Venta con quantity/unit_price inválido, se descarta: {row}")
            continue

        natural_key = (customer_id, sale_date, product, quantity, unit_price)
        if natural_key in seen_keys:
            log.warning(f"Venta duplicada dentro del mismo archivo, se omite: {natural_key}")
            continue
        seen_keys.add(natural_key)

        clean.append({
            "customer_id": customer_id,
            "sale_date": sale_date,
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
        })

    log.info(f"Transform Sales: {len(clean)}/{len(raw_sales)} ventas válidas (tras deduplicar)")
    return clean


# ------------------------------------------------------------------
# LOAD (idempotente: usa ON CONFLICT para no duplicar en corridas repetidas)
# ------------------------------------------------------------------
def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            connect_timeout=5,
        )
    except psycopg2.OperationalError as e:
        log.error(f"No se pudo conectar a PostgreSQL: {e}")
        raise


def load_customers(conn, customers):
    if not customers:
        return
    query = """
        INSERT INTO customers (customer_id, name, industry, sales_rep, email, status)
        VALUES %s
        ON CONFLICT (customer_id) DO UPDATE SET
            name = EXCLUDED.name,
            industry = EXCLUDED.industry,
            sales_rep = EXCLUDED.sales_rep,
            email = EXCLUDED.email,
            status = EXCLUDED.status,
            updated_at = now()
    """
    values = [(c["customer_id"], c["name"], c["industry"], c["sales_rep"], c["email"], c["status"]) for c in customers]
    with conn.cursor() as cur:
        execute_values(cur, query, values)
    conn.commit()
    log.info(f"Load: {len(customers)} clientes insertados/actualizados")


def load_invoices(conn, invoices):
    if not invoices:
        return
    query = """
        INSERT INTO invoices (invoice_id, customer_id, amount, invoice_date, due_date, payment_status)
        VALUES %s
        ON CONFLICT (invoice_id) DO UPDATE SET
            amount = EXCLUDED.amount,
            invoice_date = EXCLUDED.invoice_date,
            due_date = EXCLUDED.due_date,
            payment_status = EXCLUDED.payment_status,
            updated_at = now()
    """
    values = [(i["invoice_id"], i["customer_id"], i["amount"], i["invoice_date"], i["due_date"], i["payment_status"]) for i in invoices]
    with conn.cursor() as cur:
        execute_values(cur, query, values)
    conn.commit()
    log.info(f"Load: {len(invoices)} facturas insertadas/actualizadas")


def load_sales(conn, sales):
    if not sales:
        return
    query = """
        INSERT INTO sales (customer_id, sale_date, product, quantity, unit_price)
        VALUES %s
        ON CONFLICT ON CONSTRAINT uq_sale_natural_key DO NOTHING
    """
    values = [(s["customer_id"], s["sale_date"], s["product"], s["quantity"], s["unit_price"]) for s in sales]
    with conn.cursor() as cur:
        execute_values(cur, query, values)
    conn.commit()
    log.info(f"Load: {len(sales)} ventas procesadas (duplicados existentes ignorados por ON CONFLICT)")


# ------------------------------------------------------------------
# ORQUESTACIÓN
# ------------------------------------------------------------------
def run_pipeline():
    log.info("=== Iniciando pipeline ETL ===")

    raw_customers = extract_crm()
    raw_invoices = extract_erp()
    raw_sales = extract_sales_csv()

    customers = transform_customers(raw_customers)
    invoices = transform_invoices(raw_invoices)
    sales = transform_sales(raw_sales)

    try:
        conn = get_connection()
    except Exception:
        log.error("Pipeline abortado: base de datos no disponible.")
        sys.exit(1)

    try:
        load_customers(conn, customers)
        load_invoices(conn, invoices)
        load_sales(conn, sales)
    except Exception as e:
        log.error(f"Error durante la carga a la base de datos: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    log.info("=== Pipeline finalizado correctamente ===")


if __name__ == "__main__":
    run_pipeline()