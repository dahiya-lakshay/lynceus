from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.case import (
    CaseResponse,
    CreateCase,
    UpdateCase,
)
from app.services.case_service import CaseService

router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


@router.post(
    "",
    response_model=CaseResponse,
    status_code=201,
)
def create_case(
    data: CreateCase,
    db: Session = Depends(get_db),
):

    return CaseService.create_case(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[CaseResponse],
)
def get_cases(
    db: Session = Depends(get_db),
):

    return CaseService.get_cases(db)


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
):

    return CaseService.get_case(
        db,
        case_id,
    )


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
)
def update_case(
    case_id: int,
    data: UpdateCase,
    db: Session = Depends(get_db),
):

    return CaseService.update_case(
        db,
        case_id,
        data,
    )


@router.delete(
    "/{case_id}",
    status_code=204,
)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
):

    CaseService.delete_case(
        db,
        case_id,
    )