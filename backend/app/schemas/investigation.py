from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel

from app.schemas.prediction import PredictionResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.user import UserProfile


class InvestigationStatistics(BaseModel):
    sender_transaction_count: int
    receiver_transaction_count: int
    sender_total_sent: Decimal
    receiver_total_received: Decimal


class RiskSummary(BaseModel):
    prediction: str
    prediction_label: str
    risk_score: Decimal
    fraud_probability: Decimal


class InvestigationResponse(BaseModel):
    transaction: TransactionResponse
    prediction: PredictionResponse
    sender: UserProfile
    receiver: UserProfile
    statistics: InvestigationStatistics
    risk: RiskSummary
    generated_at: datetime