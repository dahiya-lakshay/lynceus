from sqlalchemy.orm import Query, Session

from app.models.prediction import (
    Prediction,
    PredictionLabel,
)


class PredictionRepository:

    @staticmethod
    def _build_filtered_query(
        db: Session,
        prediction_label: PredictionLabel | None = None,
        model_name: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
    ) -> Query:

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

        return query

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
        page: int = 1,
        size: int = 20,
        prediction_label: PredictionLabel | None = None,
        model_name: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Prediction]:

        query = PredictionRepository._build_filtered_query(
            db,
            prediction_label,
            model_name,
            min_risk_score,
            max_risk_score,
        )

        allowed_sort_fields = {
            "id": Prediction.id,
            "risk_score": Prediction.risk_score,
            "fraud_probability": Prediction.fraud_probability,
            "created_at": Prediction.created_at,
            "prediction_label": Prediction.prediction_label,
            "model_name": Prediction.model_name,
        }

        sort_column = allowed_sort_fields.get(
            sort_by,
            Prediction.created_at,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size

        return (
            query
            .offset(offset)
            .limit(size)
            .all()
        )

    @staticmethod
    def count(
        db: Session,
        prediction_label: PredictionLabel | None = None,
        model_name: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
    ) -> int:

        query = PredictionRepository._build_filtered_query(
            db,
            prediction_label,
            model_name,
            min_risk_score,
            max_risk_score,
        )

        return query.count()

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