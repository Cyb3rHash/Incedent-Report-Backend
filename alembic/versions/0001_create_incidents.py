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
    # Enums
    op.execute("CREATE TYPE incident_severity AS ENUM ('Low', 'Medium', 'High', 'Critical')")
    op.execute("CREATE TYPE incident_status AS ENUM ('Open', 'In Progress', 'Resolved')")

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
    op.execute("DROP TYPE incident_status")
    op.execute("DROP TYPE incident_severity")
