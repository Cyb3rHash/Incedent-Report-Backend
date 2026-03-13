from __future__ import annotations

"""create incidents

Revision ID: 0001_create_incidents
Revises: 
Create Date: 2026-03-13
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_create_incidents"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums (idempotent)
    #
    # Contract:
    #   - If the enum types already exist (common after partial runs or manual schema setup),
    #     this migration must not fail with DuplicateObjectError.
    #   - If they do not exist, they are created with the required labels.
    #
    # Notes:
    #   - Postgres does not support `CREATE TYPE ... IF NOT EXISTS` for enums, so we use
    #     a DO block checking pg_type/pg_namespace.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'incident_severity'
                  AND n.nspname = current_schema()
            ) THEN
                CREATE TYPE incident_severity AS ENUM ('Low', 'Medium', 'High', 'Critical');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = 'incident_status'
                  AND n.nspname = current_schema()
            ) THEN
                CREATE TYPE incident_status AS ENUM ('Open', 'In Progress', 'Resolved');
            END IF;
        END
        $$;
        """
    )

    # Table
    op.create_table(
        "incidents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.Enum(name="incident_severity"), nullable=False),
        sa.Column("status", sa.Enum(name="incident_status"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("incidents")
    # Idempotent drops help when downgrading after partial/failed runs.
    op.execute("DROP TYPE IF EXISTS incident_status")
    op.execute("DROP TYPE IF EXISTS incident_severity")
