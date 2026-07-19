from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.investigation import InvestigationResponse
from app.services.investigation_service import InvestigationService

router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


@router.get(
    "/{transaction_id}",
    response_model=InvestigationResponse,
)
def investigate_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    return InvestigationService.investigate_transaction(
        db,
        transaction_id,
    )