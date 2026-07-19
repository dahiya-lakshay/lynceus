from sqlalchemy.orm import Session

from app.models.prediction import (
    Prediction,
    PredictionLabel,
)


class PredictionRepository:

    @staticmethod
    def create(
        db: Session,
        prediction: Prediction,
    ) -> Prediction:

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return prediction

    @staticmethod
    def get_all(
        db: Session,
        prediction_label: PredictionLabel | None = None,
        model_name: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
    ) -> list[Prediction]:

        query = db.query(Prediction)

        if prediction_label is not None:
            query = query.filter(
                Prediction.prediction_label == prediction_label
            )

        if model_name is not None:
            query = query.filter(
                Prediction.model_name == model_name
            )

        if min_risk_score is not None:
            query = query.filter(
                Prediction.risk_score >= min_risk_score
            )

        if max_risk_score is not None:
            query = query.filter(
                Prediction.risk_score <= max_risk_score
            )

        return (
            query.order_by(
                Prediction.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        prediction_id: int,
    ) -> Prediction | None:

        return (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id)
            .first()
        )

    @staticmethod
    def get_by_transaction_id(
        db: Session,
        transaction_id: int,
    ) -> Prediction | None:

        return (
            db.query(Prediction)
            .filter(
                Prediction.transaction_id == transaction_id
            )
            .first()
        )

    @staticmethod
    def get_high_risk_transactions(
        db: Session,
    ) -> list[Prediction]:

        return (
            db.query(Prediction)
            .filter(
                Prediction.prediction_label == PredictionLabel.FRAUD
            )
            .order_by(
                Prediction.risk_score.desc()
            )
            .all()
        )