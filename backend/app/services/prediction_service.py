from decimal import Decimal

from sqlalchemy.orm import Session

from app.ml.inference import FraudInference
from app.models.prediction import (
    Prediction,
    PredictionLabel,
)
from app.models.transaction import (
    Transaction,
    TransactionStatus,
)
from app.repositories.prediction_repository import (
    PredictionRepository,
)


class PredictionService:

    @staticmethod
    def predict_transaction(
        db: Session,
        transaction: Transaction,
    ) -> Prediction:

        result = FraudInference.predict(
            amount=float(transaction.amount),
        )

        prediction = Prediction(
            transaction_id=transaction.id,
            model_name="Lynceus Baseline",
            model_version="1.0.0",
            fraud_probability=Decimal(
                str(result["fraud_probability"])
            ),
            risk_score=Decimal(
                str(result["risk_score"])
            ),
            prediction_label=PredictionLabel(
                result["prediction"]
            ),
            explanation=result["explanation"],
            latency_ms=result["latency_ms"],
        )

        saved_prediction = PredictionRepository.create(
            db,
            prediction,
        )

        transaction.risk_score = Decimal(
            str(result["risk_score"])
        )

        transaction.prediction = result["prediction"]

        if result["prediction"] == "FRAUD":
            transaction.status = (
                TransactionStatus.FLAGGED
            )
        else:
            transaction.status = (
                TransactionStatus.APPROVED
            )

        db.commit()
        db.refresh(transaction)

        return saved_prediction