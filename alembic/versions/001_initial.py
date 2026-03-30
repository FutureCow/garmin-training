"""initial

Revision ID: 001
Revises:
Create Date: 2026-03-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("garmin_credentials_encrypted", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("active_days", sa.JSON(), nullable=True),
        sa.Column("long_run_day", sa.String(), nullable=True),
        sa.Column("goal_distance", sa.String(), nullable=True),
        sa.Column("goal_distance_km", sa.Float(), nullable=True),
        sa.Column("goal_pace", sa.String(), nullable=True),
        sa.Column("goal_time", sa.String(), nullable=True),
        sa.Column("schema_type", sa.String(), nullable=True),
        sa.Column("schema_weeks", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_preferences_id"), "user_preferences", ["id"], unique=False)

    op.create_table(
        "training_schemas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schema_type", sa.String(), nullable=False),
        sa.Column("schema_data", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_training_schemas_id"), "training_schemas", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_training_schemas_id"), table_name="training_schemas")
    op.drop_table("training_schemas")
    op.drop_index(op.f("ix_user_preferences_id"), table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
