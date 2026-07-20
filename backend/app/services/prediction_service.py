from decimal import Decimal

from fastapi import HTTPException, status
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
from app.services.case_service import CaseService
from app.services.feature_engineering_service import (
    FeatureEngineeringService,
)


class PredictionService:

    @staticmethod
    def predict_transaction(
        db: Session,
        transaction: Transaction,
    ) -> Prediction:

        features = FeatureEngineeringService.build_features(
            db,
            transaction,
        )

        result = FraudInference.predict(
            features,
        )

        prediction = Prediction(

            transaction_id=transaction.id,

            model_name=result["model_name"],

            model_version=result["model_version"],

            fraud_probability=Decimal(
                str(result["fraud_probability"])
            ),

            risk_score=Decimal(
                str(result["risk_score"])
            ),

            prediction_label=PredictionLabel(
                result["prediction"]
            ),

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

            CaseService.create_case_for_transaction(
                db,
                transaction.id,
            )

        else:

            transaction.status = (
                TransactionStatus.APPROVED
            )

        db.commit()

        db.refresh(transaction)

        return saved_prediction

    @staticmethod
    def get_predictions(
        db: Session,
        page: int = 1,
        size: int = 20,
        prediction_label: PredictionLabel | None = None,
        model_name: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):

        predictions = PredictionRepository.get_all(
            db,
            page,
            size,
            prediction_label,
            model_name,
            min_risk_score,
            max_risk_score,
            sort_by,
            sort_order,
        )

        total = PredictionRepository.count(
            db,
            prediction_label,
            model_name,
            min_risk_score,
            max_risk_score,
        )

        return {
            "page": page,
            "size": size,
            "total": total,
            "items": predictions,
        }

    @staticmethod
    def get_prediction(
        db: Session,
        prediction_id: int,
    ):

        prediction = PredictionRepository.get_by_id(
            db,
            prediction_id,
        )

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found",
            )

        return prediction

    @staticmethod
    def get_prediction_by_transaction(
        db: Session,
        transaction_id: int,
    ):

        prediction = (
            PredictionRepository.get_by_transaction_id(
                db,
                transaction_id,
            )
        )

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found",
            )

        return prediction