-- Incident Report Backend - Postgres schema (Neon compatible)
-- Paste into Neon SQL Editor and run.
-- Notes:
-- - Uses enums for status and severity.
-- - Uses UUID primary keys.
-- - Includes updated_at trigger.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_status') THEN
    CREATE TYPE incident_status AS ENUM ('open', 'acknowledged', 'in_progress', 'resolved', 'closed');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'incident_severity') THEN
    CREATE TYPE incident_severity AS ENUM ('low', 'medium', 'high', 'critical');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS incidents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  description text NOT NULL,
  status incident_status NOT NULL DEFAULT 'open',
  severity incident_severity NOT NULL DEFAULT 'medium',
  reported_by text NULL,
  assigned_to text NULL,
  occurred_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incidents_status_idx ON incidents (status);
CREATE INDEX IF NOT EXISTS incidents_severity_idx ON incidents (severity);
CREATE INDEX IF NOT EXISTS incidents_created_at_idx ON incidents (created_at DESC);

CREATE TABLE IF NOT EXISTS incident_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  incident_id uuid NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incident_events_incident_id_idx ON incident_events (incident_id, created_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS incidents_set_updated_at ON incidents;

CREATE TRIGGER incidents_set_updated_at
BEFORE UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
