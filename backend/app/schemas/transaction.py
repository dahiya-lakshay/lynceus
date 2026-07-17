from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    WALLET = "WALLET"


class CreateTransaction(BaseModel):
    receiver_id: int
    amount: Decimal
    payment_method: PaymentMethod


class UpdateTransaction(BaseModel):
    amount: Decimal | None = None
    payment_method: PaymentMethod | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_uuid: UUID
    sender_id: int
    receiver_id: int
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    status: str
    risk_score: Decimal | None
    prediction: str | None
    created_at: datetime