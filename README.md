# Incident Report Backend (FastAPI + Neon Postgres)

This container provides a working FastAPI backend with Neon PostgreSQL integration and full Incident CRUD.

## Features
- FastAPI app with OpenAPI docs (`/docs`, `/openapi.json`)
- Neon Postgres persistence via SQLAlchemy (async) + asyncpg
- Alembic migrations for schema setup
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

See `.env.example`.

## Install + Run (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run DB migrations (creates tables)
# Use module invocation so it works even if `alembic` isn't on PATH.
python -m alembic upgrade head

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

## Notes
- UUID is used as the primary key.
- `severity`: Low | Medium | High | Critical
- `status`: Open | In Progress | Resolved
- `created_at` is server-generated.
- `updated_at` auto-updates on modification.
