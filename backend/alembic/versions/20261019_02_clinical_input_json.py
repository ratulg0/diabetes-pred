"""Store full replacement-dataset assessment inputs as JSON.

Revision ID: 20261019_02
Revises: 20261019_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261019_02"
down_revision = "20261019_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("input_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessments", "input_json")
