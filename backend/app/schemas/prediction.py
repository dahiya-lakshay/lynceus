from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PredictionLabel(str, Enum):
    LEGITIMATE = "LEGITIMATE"
    FRAUD = "FRAUD"


class FeatureContribution(BaseModel):
    feature: str
    impact: float
    direction: str
    magnitude: float


class PredictionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    prediction_uuid: UUID

    transaction_id: int

    model_name: str

    model_version: str

    fraud_probability: Decimal

    risk_score: Decimal

    prediction_label: PredictionLabel

    top_features: list[FeatureContribution]

    explanation: str | None

    latency_ms: int

    created_at: datetime