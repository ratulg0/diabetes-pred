from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="tabular_assessment")
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pregnancies: Mapped[int] = mapped_column(Integer, nullable=False)
    glucose: Mapped[float] = mapped_column(Float, nullable=False)
    blood_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    skin_thickness: Mapped[float] = mapped_column(Float, nullable=False)
    insulin: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    diabetes_pedigree_function: Mapped[float] = mapped_column(Float, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped["PredictionResult"] = relationship(back_populates="assessment", cascade="all, delete-orphan", uselist=False)


class PredictionResult(Base):
    __tablename__ = "prediction_results"
    __table_args__ = (UniqueConstraint("assessment_id", name="uq_prediction_results_assessment_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    predicted_class: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)
    response_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[Assessment] = relationship(back_populates="result")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dataset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_schema: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_metrics: Mapped[str] = mapped_column(Text, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("scope", name="uq_user_preferences_scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    glucose_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="mg/dL")
    compact_tables: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assessment_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


Index("ix_assessments_created_at", Assessment.created_at)
Index("ix_prediction_results_predicted_class", PredictionResult.predicted_class)
