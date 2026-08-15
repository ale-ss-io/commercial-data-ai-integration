import os

os.environ.setdefault("API_KEY", "test-key")

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from api.db import Base, get_db
from api.models import Customer, Invoice, Sale
from api.main import app


# SQLite en memoria compartida entre requests dentro del mismo test
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()

    today = date.today()

    session.add(Customer(
        customer_id="C1",
        name="Empresa ABC",
        industry="Retail",
        sales_rep="Ana",
        email="abc@example.com",
        status="active",
    ))

    session.add(Sale(
        sale_id=1,
        customer_id="C1",
        sale_date=today - timedelta(days=10),
        product="Widget",
        quantity=10,
        unit_price=100,
    ))

    session.add(Invoice(
        invoice_id="I1",
        customer_id="C1",
        amount=150000,
        invoice_date=today - timedelta(days=100),
        due_date=today - timedelta(days=70),
        payment_status="pending",
    ))

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers():
    return {"X-API-Key": "test-key"}