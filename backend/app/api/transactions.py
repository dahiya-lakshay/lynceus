from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.transaction import (
    CreateTransaction,
    TransactionResponse,
    UpdateTransaction,
)
from app.services.transaction_service import (
    TransactionService,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction: CreateTransaction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return TransactionService.create_transaction(
        db,
        current_user,
        transaction,
    )


@router.get(
    "",
    response_model=list[TransactionResponse],
)
def get_transactions(
    db: Session = Depends(get_db),
):

    return TransactionService.get_all_transactions(
        db,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    transaction = TransactionService.get_transaction(
        db,
        transaction_id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def update_transaction(
    transaction_id: int,
    transaction: UpdateTransaction,
    db: Session = Depends(get_db),
):

    return TransactionService.update_transaction(
        db,
        transaction_id,
        transaction,
    )


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):

    TransactionService.delete_transaction(
        db,
        transaction_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )