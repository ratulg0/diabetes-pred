# Declarative base for all SQLAlchemy ORM models. Inheriting from this class
# registers each model's table metadata so Alembic migrations can discover it.
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base shared by every database model."""
    pass
