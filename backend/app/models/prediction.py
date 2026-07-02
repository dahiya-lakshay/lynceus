import uuid as uuid_pkg

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class PredictionLabel(str, Enum):
    LEGITIMATE = "LEGITIMATE"
    FRAUD = "FRAUD"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    prediction_uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid_pkg.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    fraud_probability: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    prediction_label: Mapped[PredictionLabel] = mapped_column(
        SQLEnum(PredictionLabel),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="predictions",
    )