# Incedent-Report-Backend

Node.js (Express) backend service for incident reporting using Neon/Postgres.

## 1) Setup

1. Install dependencies:

```bash
npm install
```

2. Create your `.env` (a `.env` already exists in this environment). For local usage you can copy:

```bash
cp .env.example .env
```

Required:
- `DATABASE_URL` (Neon connection string)

## 2) Create tables in Neon

Open Neon SQL Editor and paste the contents of `schema.sql`, then run it.

## 3) Run

Development:

```bash
npm run dev
```

Production:

```bash
npm start
```

The server listens on `HOST:PORT` (defaults `0.0.0.0:3002`).

## 4) API

Base URL: `/api`

- `GET /api/health`
- `GET /api/docs`

Incidents:
- `GET /api/incidents?status=&severity=&q=&limit=&offset=&sort=`
- `POST /api/incidents`
- `GET /api/incidents/:id`
- `PATCH /api/incidents/:id`
- `GET /api/incidents/:id/events`
- `POST /api/incidents/:id/events`

Example create:

```bash
curl -X POST http://localhost:3002/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database latency spike",
    "description": "Increased p95 latency observed in API",
    "severity": "high",
    "reported_by": "oncall@company.com"
  }'
```
