from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.prediction import PredictionLabel
from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


@router.get(
    "",
    response_model=list[PredictionResponse],
)
def get_predictions(
    prediction_label: PredictionLabel | None = Query(
        default=None,
    ),
    model_name: str | None = Query(
        default=None,
    ),
    min_risk_score: float | None = Query(
        default=None,
        ge=0,
        le=100,
    ),
    max_risk_score: float | None = Query(
        default=None,
        ge=0,
        le=100,
    ),
    db: Session = Depends(get_db),
):

    return PredictionService.get_predictions(
        db,
        prediction_label,
        model_name,
        min_risk_score,
        max_risk_score,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):

    return PredictionService.get_prediction(
        db,
        prediction_id,
    )


@router.get(
    "/transaction/{transaction_id}",
    response_model=PredictionResponse,
)
def get_prediction_by_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    return PredictionService.get_prediction_by_transaction(
        db,
        transaction_id,
    )