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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    FLAGGED = "FLAGGED"


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    WALLET = "WALLET"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    transaction_uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid_pkg.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod),
        nullable=False,
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    risk_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    prediction: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_transactions",
    )

    receiver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_transactions",
    )