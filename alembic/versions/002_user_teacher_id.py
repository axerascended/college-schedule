"""add teacher_id to users

Revision ID: 002
Revises: 001
Create Date: 2026-05-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("teacher_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_users_teacher_id", "teachers", ["teacher_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_teacher_id", type_="foreignkey")
        batch_op.drop_column("teacher_id")
