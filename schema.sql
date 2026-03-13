-- Incident Report Backend - Manual PostgreSQL Schema
--
-- Purpose:
--   Paste/apply this schema to your Postgres database *manually*.
--   This backend intentionally does NOT use Alembic migrations.
--
-- Matches SQLAlchemy model:
--   app/models/incident.py
--
-- Notes:
--   - Uses UUID primary key.
--   - Uses Postgres enum types for severity/status.
--   - Keeps updated_at in sync via a trigger.
--   - Requires pgcrypto for gen_random_uuid().

BEGIN;

-- -------------------------------
-- Extensions
-- -------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -------------------------------
-- Enum types
-- -------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_severity') THEN
        CREATE TYPE incident_severity AS ENUM ('Low', 'Medium', 'High', 'Critical');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_status') THEN
        CREATE TYPE incident_status AS ENUM ('Open', 'In Progress', 'Resolved');
    END IF;
END$$;

-- -------------------------------
-- Table: incidents
-- -------------------------------
CREATE TABLE IF NOT EXISTS incidents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title varchar(255) NOT NULL,
    description text NULL,
    severity incident_severity NOT NULL DEFAULT 'Low',
    status incident_status NOT NULL DEFAULT 'Open',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Helpful indexes for common query patterns:
-- List endpoint sorts by created_at desc; this supports that efficiently.
CREATE INDEX IF NOT EXISTS idx_incidents_created_at_desc ON incidents (created_at DESC);

-- -------------------------------
-- Trigger to maintain updated_at
-- -------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_incidents_set_updated_at ON incidents;

CREATE TRIGGER trg_incidents_set_updated_at
BEFORE UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
