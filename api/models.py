from sqlalchemy import Column, String, Numeric, Date, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from api.db import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    industry = Column(String)
    sales_rep = Column(String)
    email = Column(String)
    status = Column(String)

    invoices = relationship("Invoice", back_populates="customer")
    sales = relationship("Sale", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(String, primary_key=True)
    customer_id = Column(
        String,
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    amount = Column(Numeric(14, 2), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_status = Column(String, nullable=False)

    customer = relationship("Customer", back_populates="invoices")


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(BigInteger, primary_key=True)
    customer_id = Column(
        String,
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    sale_date = Column(Date, nullable=False)
    product = Column(String, nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)

    customer = relationship("Customer", back_populates="sales")

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "sale_date",
            "product",
            "quantity",
            "unit_price",
            name="uq_sale_natural_key",
        ),
    )

    @property
    def date(self):
        return self.sale_date