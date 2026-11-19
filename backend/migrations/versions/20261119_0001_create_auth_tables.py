"""Create durable authentication tables.

Revision ID: 20261119_0001
Revises:
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261119_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users and expiring email-verification records."""
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "email_verifications",
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["email"], ["users.email"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_digest"),
    )
    op.create_index(
        "ix_email_verifications_expires_at",
        "email_verifications",
        ["expires_at"],
    )


def downgrade() -> None:
    """Remove durable authentication tables."""
    op.drop_index(
        "ix_email_verifications_expires_at",
        table_name="email_verifications",
    )
    op.drop_table("email_verifications")
    op.drop_table("users")
