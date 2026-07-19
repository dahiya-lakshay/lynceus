from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
    PredictionLabel,
)
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_repository import UserRepository


class AdminService:

    @staticmethod
    def get_all_users(
        db: Session,
    ):
        return UserRepository.get_all(db)

    @staticmethod
    def get_dashboard_stats(
        db: Session,
    ):

        total_users = (
            db.query(User)
            .count()
        )

        total_transactions = (
            db.query(Transaction)
            .count()
        )

        total_predictions = (
            db.query(Prediction)
            .count()
        )

        high_risk_transactions = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_label == PredictionLabel.FRAUD
            )
            .count()
        )

        return {
            "total_users": total_users,
            "total_transactions": total_transactions,
            "total_predictions": total_predictions,
            "high_risk_transactions": high_risk_transactions,
        }

    @staticmethod
    def get_high_risk_transactions(
        db: Session,
    ):
        return PredictionRepository.get_high_risk_transactions(db)

    @staticmethod
    def get_analytics(
        db: Session,
    ):

        total_predictions = (
            db.query(Prediction)
            .count()
        )

        fraud_predictions = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_label == PredictionLabel.FRAUD
            )
            .count()
        )

        legitimate_predictions = (
            total_predictions - fraud_predictions
        )

        fraud_rate = (
            Decimal("0.00")
            if total_predictions == 0
            else round(
                Decimal(fraud_predictions * 100)
                / Decimal(total_predictions),
                2,
            )
        )

        average_risk_score = (
            db.query(
                func.avg(Prediction.risk_score)
            ).scalar()
            or Decimal("0.00")
        )

        average_fraud_probability = (
            db.query(
                func.avg(Prediction.fraud_probability)
            ).scalar()
            or Decimal("0.00")
        )

        return {
            "total_predictions": total_predictions,
            "fraud_predictions": fraud_predictions,
            "legitimate_predictions": legitimate_predictions,
            "fraud_rate": fraud_rate,
            "average_risk_score": round(
                Decimal(average_risk_score),
                2,
            ),
            "average_fraud_probability": round(
                Decimal(average_fraud_probability),
                2,
            ),
        }