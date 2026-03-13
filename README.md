# Incident Report Backend (FastAPI + Postgres)

This container provides a working FastAPI backend with PostgreSQL integration and full Incident CRUD.

## Features
- FastAPI app with OpenAPI docs (`/docs`, `/openapi.json`)
- Postgres persistence via SQLAlchemy (async) + asyncpg
- No Alembic dependency: schema is expected to be created manually (you paste/apply SQL yourself)
- Structured JSON error responses (validation + not found + server errors)
- Incident CRUD endpoints under `/api/incidents`

## Configuration (env vars)
Set `DATABASE_URL` (required). Example (Neon typically requires SSL):

```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB?sslmode=require
```

Optional:
- `ALLOWED_ORIGINS` comma-separated list for CORS
- `HOST`, `PORT`, `LOG_LEVEL`

## Schema (manual, no Alembic)
This backend intentionally does **not** use Alembic. You must create the schema yourself.

Paste/apply the provided schema file:

- `schema.sql` (in this repo)

It creates:
- Extension: `pgcrypto` (for `gen_random_uuid()`)
- Enum type: `incident_severity` with labels: `Low`, `Medium`, `High`, `Critical`
- Enum type: `incident_status` with labels: `Open`, `In Progress`, `Resolved`
- Table: `incidents`
- Trigger: maintains `updated_at` automatically on UPDATE

## Install + Run (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 3002
```

Open:
- Swagger UI: http://localhost:3002/docs

## API
Base URL: `/api`

- `POST /api/incidents` - create incident
- `GET /api/incidents` - list incidents (pagination)
- `GET /api/incidents/{incident_id}` - get by id
- `PUT /api/incidents/{incident_id}` - update incident
- `DELETE /api/incidents/{incident_id}` - delete incident
