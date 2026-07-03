from sqlalchemy.orm import Session

from app.models.prediction import Prediction


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
    ) -> list[Prediction]:

        return (
            db.query(Prediction)
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