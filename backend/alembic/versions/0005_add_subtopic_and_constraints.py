"""add subtopic to study_tasks and constraints to study_plans

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "study_tasks",
        sa.Column("subtopic", sa.String(), nullable=True, server_default="general"),
    )
    op.add_column(
        "study_plans",
        sa.Column("constraints", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("study_plans", "constraints")
    op.drop_column("study_tasks", "subtopic")
