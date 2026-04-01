"""Initial migration: users and user_accounts

Revision ID: 6b8d8a744a8b
Revises:
Create Date: 2026-03-31 15:51:14.792256

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6b8d8a744a8b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgcrypto extension for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "user_id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")
        ),
        sa.Column("fio", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("sex", sa.Boolean(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, default="user"),
        sa.Column("dobro_id", sa.String(), nullable=True),
        sa.Column("consent", sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    # Create user_accounts table
    op.create_table(
        "user_accounts",
        sa.Column(
            "account_id",
            sa.UUID(),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform_name", sa.String(), nullable=False),
        sa.Column("platform_user_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("account_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_accounts")
    op.drop_table("users")
