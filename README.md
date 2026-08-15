\# Febara - Data \& AI Integration API



API de integración de datos desarrollada con FastAPI y PostgreSQL.

El proyecto integra información de clientes, ventas y facturas y expone

endpoints para consulta y análisis de riesgo de clientes.



\## Tecnologías



\- Python 3.12

\- FastAPI

\- PostgreSQL 16

\- SQLAlchemy

\- Pandas

\- Docker / Docker Compose

\- Pytest



\## Arquitectura



El proyecto está organizado en los siguientes componentes:



\- `api/`: API REST desarrollada con FastAPI.

\- `pipeline/`: lógica de integración y procesamiento de datos.

\- `mock\_apis/`: fuentes de datos simuladas.

\- `data/`: datos utilizados por el proyecto.

\- `tests/`: pruebas automatizadas.

\- `Dockerfile`: configuración de la imagen de la API.

\- `docker-compose.yml`: configuración de los servicios API y PostgreSQL.



\## Requisitos



\- Docker Desktop

\- Git



No es necesario instalar PostgreSQL localmente para ejecutar el proyecto,

ya que PostgreSQL se ejecuta mediante Docker Compose.



\## Configuración



Crear un archivo `.env` a partir de `.env.example`:



```text

POSTGRES\_USER=febara\_user

POSTGRES\_PASSWORD=change\_me

POSTGRES\_DB=febara\_integration

