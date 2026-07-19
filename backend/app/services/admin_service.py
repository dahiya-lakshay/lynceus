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