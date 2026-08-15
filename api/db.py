import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError


load_dotenv()


DATABASE_URL = os.environ["DATABASE_URL"]

# pool_pre_ping evita usar conexiones muertas
# connect_timeout y statement_timeout evitan que una conexión
# o consulta se quede esperando indefinidamente
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={
        "connect_timeout": 5,
        "options": "-c statement_timeout=5000"
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """
    Dependency de FastAPI para obtener una sesión de PostgreSQL.
    La sesión se cierra siempre al terminar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()