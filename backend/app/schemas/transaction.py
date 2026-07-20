from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.transaction import (
    DeviceType,
    MerchantCategory,
    PaymentMethod,
    TransactionStatus,
)


class CreateTransaction(BaseModel):
    receiver_id: int
    amount: Decimal
    payment_method: PaymentMethod

    origin_country: str
    destination_country: str
    merchant_category: MerchantCategory
    device_type: DeviceType
    device_id_hash: str


class UpdateTransaction(BaseModel):
    amount: Decimal | None = None
    payment_method: PaymentMethod | None = None

    origin_country: str | None = None
    destination_country: str | None = None
    merchant_category: MerchantCategory | None = None
    device_type: DeviceType | None = None
    device_id_hash: str | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_uuid: UUID

    sender_id: int
    receiver_id: int

    amount: Decimal
    currency: str
    payment_method: PaymentMethod

    origin_country: str
    destination_country: str
    merchant_category: MerchantCategory
    device_type: DeviceType
    device_id_hash: str

    status: TransactionStatus
    risk_score: Decimal | None
    prediction: str | None

    created_at: datetime