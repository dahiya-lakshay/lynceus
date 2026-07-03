from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repositories.prediction_repository import (
    PredictionRepository,
)
from app.schemas.prediction import PredictionResponse

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


@router.get(
    "",
    response_model=list[PredictionResponse],
)
def get_predictions(
    db: Session = Depends(get_db),
):

    return PredictionRepository.get_all(
        db,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
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


@router.get(
    "/transaction/{transaction_id}",
    response_model=PredictionResponse,
)
def get_prediction_by_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
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