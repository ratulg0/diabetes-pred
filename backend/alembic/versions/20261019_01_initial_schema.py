"""Create GlucoCare persistence tables.

Revision ID: 20261019_01
Revises:
Create Date: 2026-10-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20261019_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("pregnancies", sa.Integer(), nullable=False),
        sa.Column("glucose", sa.Float(), nullable=False),
        sa.Column("blood_pressure", sa.Float(), nullable=False),
        sa.Column("skin_thickness", sa.Float(), nullable=False),
        sa.Column("insulin", sa.Float(), nullable=False),
        sa.Column("bmi", sa.Float(), nullable=False),
        sa.Column("diabetes_pedigree_function", sa.Float(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
    )
    op.create_index("ix_assessments_created_at", "assessments", ["created_at"])
    op.create_table(
        "prediction_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("predicted_class", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
        sa.Column("response_metadata", sa.Text(), nullable=True),
        sa.UniqueConstraint("assessment_id", name="uq_prediction_results_assessment_id"),
    )
    op.create_index("ix_prediction_results_predicted_class", "prediction_results", ["predicted_class"])
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("version", sa.String(length=128), unique=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("algorithm", sa.String(length=128), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=True),
        sa.Column("dataset_sha256", sa.String(length=64), nullable=False),
        sa.Column("feature_schema", sa.Text(), nullable=False),
        sa.Column("evaluation_metrics", sa.Text(), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("glucose_unit", sa.String(length=16), nullable=False),
        sa.Column("compact_tables", sa.Boolean(), nullable=False),
        sa.Column("assessment_notifications", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("scope", name="uq_user_preferences_scope"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("model_versions")
    op.drop_index("ix_prediction_results_predicted_class", table_name="prediction_results")
    op.drop_table("prediction_results")
    op.drop_index("ix_assessments_created_at", table_name="assessments")
    op.drop_table("assessments")
