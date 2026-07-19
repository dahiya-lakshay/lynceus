from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.prediction import PredictionLabel
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


@router.get(
    "",
    response_model=PaginatedResponse[PredictionResponse],
)
def get_predictions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
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
    sort_by: str = Query(
        default="created_at",
        pattern="^(id|risk_score|fraud_probability|created_at|prediction_label|model_name)$",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):

    result = PredictionService.get_predictions(
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

    return PaginatedResponse[PredictionResponse].create(
        page=result["page"],
        size=result["size"],
        total=result["total"],
        items=result["items"],
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