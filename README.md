# Integración de Datos Comerciales y AI

Una pequeña capa de integración de datos que consolida información de clientes, ventas y facturas provenientes de múltiples fuentes, y expone los datos resultantes mediante una API REST segura.

El proyecto está diseñado como una capa de datos de backend que posteriormente podría ser consumida por un agente de IA para responder preguntas comerciales como:

- ¿Qué clientes tienen mayor riesgo de atraso en sus pagos?
- ¿Cuáles fueron las últimas ventas de un cliente específico?
- ¿Qué clientes tienen facturas vencidas por encima de cierto monto?
- ¿Cuál es el estado comercial general de un cliente?

## Arquitectura

El sistema sigue una arquitectura simple de integración de datos:

```text
CRM Mock API ──────┐
                   │
ERP Mock API ──────┼──> Pipeline de Datos ──> PostgreSQL ──> FastAPI
                   │                                          │
CSV de Ventas ─────┘                                          ▼
                                                       Aplicaciones /
                                                        Agente de IA
```

La capa de IA se mantiene intencionalmente fuera de la base de datos. Un futuro agente de IA consumiría los endpoints de FastAPI en lugar de acceder directamente a PostgreSQL.

## Tecnologías

- Python 3.12
- FastAPI
- PostgreSQL 16
- SQLAlchemy
- Pandas
- Docker / Docker Compose
- Pytest

## Estructura del Proyecto

```text
commercial-data-ai-integration/
│
├── api/
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── risk.py
│   ├── schemas.py
│   └── security.py
│
├── data/
│   └── ventas.csv
│
├── mock_apis/
│   ├── crm_mock.py
│   └── erp_mock.py
│
├── pipeline/
│   ├── etl.py
│   └── schema.sql
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_risk.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

## Fuentes de Datos

### CRM

Una API REST simulada (mock) que provee información de clientes:

- `customer_id`
- `name`
- `industry`
- `sales_rep`
- `email`
- `status`

### ERP

Una API REST simulada (mock) que provee información de facturas:

- `invoice_id`
- `customer_id`
- `amount`
- `invoice_date`
- `due_date`
- `payment_status`

El conjunto de datos incluye facturas pagadas, pendientes y vencidas.

### CSV de Ventas

El historial de ventas se provee mediante un archivo CSV que contiene:

- `customer_id`
- `date`
- `product`
- `quantity`
- `unit_price`

Los datos de origen contienen intencionalmente problemas de calidad, como registros duplicados, valores vacíos, formatos de fecha inconsistentes y registros inconsistentes.

## Pipeline de Datos

El pipeline de integración realiza las siguientes operaciones:

1. Extrae datos de la API mock del CRM.
2. Extrae datos de la API mock del ERP.
3. Lee el historial de ventas desde el CSV.
4. Valida los registros entrantes.
5. Normaliza los formatos de datos.
6. Maneja registros duplicados e inválidos.
7. Carga los datos limpios en PostgreSQL.
8. Usa restricciones (constraints) de base de datos e identificadores para soportar una ejecución idempotente.

El pipeline puede ejecutarse repetidamente sin crear registros duplicados de forma intencional.

## Modelo de Datos

Las entidades principales son:

```text
customers
    │
    ├──────────────< invoices
    │
    └──────────────< sales
```

La tabla `customers` actúa como entidad central y se relaciona tanto con `invoices` como con `sales` a través de `customer_id`.

Esta estructura fue elegida porque las principales preguntas de negocio están centradas en el cliente. Permite que la API combine eficientemente la información del cliente con su actividad de ventas y el estado de sus facturas/pagos.

## API

La API está implementada con FastAPI.

### Health Check

```http
GET /health
```

Devuelve:

```json
{
  "status": "ok"
}
```

### Clientes

```http
GET /customers
```

Devuelve los clientes disponibles.

### Detalle de Cliente

```http
GET /customers/{customer_id}
```

Devuelve la información de un cliente específico.

### Ventas del Cliente

```http
GET /customers/{customer_id}/sales
```

Devuelve el historial de ventas del cliente.

### Facturas del Cliente

```http
GET /customers/{customer_id}/invoices
```

Devuelve las facturas del cliente y su estado de pago.

### Resumen del Cliente

```http
GET /customers/{customer_id}/summary
```

Devuelve información comercial consolidada, incluyendo:

- Ventas totales
- Saldo pendiente
- Número de facturas vencidas
- Fecha de la última compra
- Nivel de riesgo

Ejemplo:

```json
{
  "customer": "Comercial ABC",
  "total_sales": 3500.0,
  "outstanding_balance": 140000.0,
  "overdue_invoices": 1,
  "last_purchase": "2026-07-28",
  "risk_level": "HIGH"
}
```

### Clientes en Riesgo

```http
GET /customers/at-risk
```

Devuelve los clientes clasificados con riesgo de pago medio o alto.

## Lógica de Riesgo

La clasificación de riesgo se implementa mediante reglas de negocio determinísticas, en lugar de machine learning.

La implementación actual considera los saldos pendientes y las facturas vencidas para clasificar a los clientes en:

- `LOW` (bajo)
- `MEDIUM` (medio)
- `HIGH` (alto)

Este enfoque se eligió porque el objetivo del ejercicio es demostrar principalmente integración de datos, ingeniería de backend, diseño de APIs e implementación de reglas de negocio.

## Seguridad

La API requiere una API key mediante el header HTTP `X-API-Key` para los endpoints protegidos.

Ejemplo:

```http
X-API-Key: 1234
```

La API key se provee mediante configuración de entorno, en lugar de estar almacenada en el código fuente.

La configuración sensible se excluye del control de versiones mediante `.gitignore`.

### Consideraciones para producción

Para una implementación en producción, serían apropiadas las siguientes mejoras:

- OAuth2 u OpenID Connect
- Tokens de acceso de corta duración
- Control de acceso basado en roles (RBAC)
- Gestión de secretos mediante un secrets manager dedicado
- HTTPS/TLS
- Límite de tasa de peticiones (rate limiting) en la API
- Registro de auditoría (audit logging)
- Rotación de llaves (key rotation)

El mecanismo de API key usado en este ejercicio es intencionalmente ligero y no pretende representar una arquitectura completa de autenticación para producción.

## Resiliencia

El diseño contempla varios escenarios de falla:

### Falla de APIs externas

Las fuentes externas están aisladas de la capa de API. El pipeline de integración puede detectar fallas durante la extracción, en lugar de exponer los sistemas externos directamente a los consumidores de la API.

### Registros inválidos

Los datos entrantes se validan y normalizan antes de cargarse en la base de datos.

### Ejecución duplicada del pipeline

El pipeline está diseñado para ser idempotente, de modo que ejecutarlo nuevamente no crea registros duplicados de forma intencional.

### Disponibilidad de la base de datos

PostgreSQL se ejecuta como un servicio independiente de Docker Compose, y la API está configurada para iniciar únicamente después de que la base de datos esté saludable (healthy).

Para una implementación en producción, serían apropiadas políticas de reintento (retry) adicionales, configuración de connection pooling, monitoreo y un manejo de errores más detallado.

## Ejecutar el Proyecto

### Requisitos

- Docker Desktop
- Git

No es necesario instalar PostgreSQL localmente, ya que se ejecuta dentro de Docker.

### Configuración

Crea un archivo `.env` local basado en `.env.example`:

```text
POSTGRES_USER=app_user
POSTGRES_PASSWORD=change_me
POSTGRES_DB=commercial_integration
```

No subas el archivo `.env` al repositorio.

### Levantar la aplicación

Desde la raíz del proyecto:

```powershell
docker compose up --build
```

La API estará disponible en:

```text
http://localhost:8000
```

La documentación interactiva de la API está disponible en:

```text
http://localhost:8000/docs
```

### Detener la aplicación

```powershell
docker compose down
```

## Pruebas (Testing)

Las pruebas automatizadas están implementadas con Pytest.

Ejecutar:

```powershell
pytest -q
```

La suite de pruebas cubre el comportamiento de la API y lógica de negocio crítica, como la clasificación de riesgo de clientes.

## Ejemplos de Peticiones a la API

Health check:

```powershell
curl.exe http://localhost:8000/health
```

Petición autenticada de clientes:

```powershell
curl.exe -H "X-API-Key: 1234" http://localhost:8000/customers
```

Resumen de cliente:

```powershell
curl.exe -H "X-API-Key: 1234" http://localhost:8000/customers/C001/summary
```

Clientes en riesgo:

```powershell
curl.exe -H "X-API-Key: 1234" http://localhost:8000/customers/at-risk
```

## Decisiones Técnicas y Trade-offs

### PostgreSQL

Se eligió PostgreSQL porque los datos son relacionales y las entidades principales tienen relaciones claras entre clientes, facturas y ventas. Además, ofrece restricciones (constraints) y comportamiento transaccional útiles para mantener la integridad de los datos.

### FastAPI

Se eligió FastAPI porque ofrece una forma ligera de exponer endpoints REST tipados, documentación automática con OpenAPI, e integración sencilla con procesamiento de datos basado en Python.

### Docker Compose

Docker Compose provee un entorno local reproducible que contiene tanto la API como PostgreSQL, sin necesidad de instalar PostgreSQL directamente en la máquina anfitriona.

### Reglas de riesgo determinísticas en lugar de Machine Learning

No se introdujo machine learning de forma intencional para la clasificación de riesgo. El conjunto de datos disponible es pequeño y sintético, por lo que un modelo predictivo añadiría complejidad sin aportar evidencia significativa de desempeño predictivo.

Las reglas de negocio determinísticas son más fáciles de explicar, probar y mantener para este ejercicio.

### APIs Mock

Se usaron APIs simuladas (mock) para representar los sistemas de CRM y ERP, ya que el ejercicio no provee servicios externos reales. Esto permite ejecutar el flujo completo de integración de forma local y reproducible.

### Pipeline idempotente

Se priorizó la idempotencia porque los pipelines de integración se ejecutan comúnmente de forma repetida. Se usan identificadores y restricciones de base de datos para evitar que los mismos registros lógicos se inserten múltiples veces.

### Autenticación por API key

Se eligió una API key simple porque satisface el requisito de autenticación, manteniendo la implementación enfocada en el problema de integración de datos. Una implementación en producción requeriría una solución de identidad y control de acceso más robusta.

## Limitaciones y Mejoras Futuras

Esta implementación se enfoca intencionalmente en los requisitos principales del ejercicio.

Posibles mejoras futuras incluyen:

- Autenticación y autorización de nivel producción
- Políticas de reintento (retry) y timeout para las APIs externas
- Logging estructurado y monitoreo
- Reportes de calidad de datos más completos
- Procesamiento incremental del ETL
- Paginación y filtrado en la API
- Migraciones de base de datos con Alembic
- Pruebas de integración más extensas
- Capa de herramientas de IA (tool/function calling)
- Interfaz basada en MCP para agentes de IA
- Pipeline de CI/CD
- Monitoreo de salud de contenedores y configuración de despliegue en producción