"""Create initial transformation cache and payload metadata tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transformation_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("transformed_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("original_text", name="uq_transform_original"),
    )
    op.create_table(
        "payloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("payloads")
    op.drop_table("transformation_cache")
