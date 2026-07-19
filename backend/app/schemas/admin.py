from decimal import Decimal

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_transactions: int
    total_predictions: int
    high_risk_transactions: int


class AnalyticsResponse(BaseModel):
    total_predictions: int
    fraud_predictions: int
    legitimate_predictions: int

    fraud_rate: Decimal

    average_risk_score: Decimal
    average_fraud_probability: Decimal