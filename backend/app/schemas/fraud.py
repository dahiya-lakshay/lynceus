from datetime import datetime

from pydantic import BaseModel


class FraudPredictionRequest(BaseModel):

    amount: float

    timestamp: datetime

    currency: str

    payment_method: str

    merchant_category: str

    device_type: str

    origin_country: str

    destination_country: str

    hour: int

    day_of_week: int

    sender_account_age_days: int

    receiver_account_age_days: int

    sender_txn_count_24h: int

    receiver_txn_count_24h: int

    sender_avg_amount_30d: float

    receiver_avg_amount_30d: float

    velocity_score: float

    is_weekend: bool

    is_new_receiver: bool

    device_trusted: bool

    cross_border: bool

    high_risk_country: bool

class FraudPredictionResponse(BaseModel):

    prediction: str

    fraud_probability: float

    risk_score: float

    model_name: str

    model_version: str

    latency_ms: int