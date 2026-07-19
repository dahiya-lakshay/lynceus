from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.transaction import (
    PaymentMethod,
    TransactionStatus,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
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
    response_model=PaginatedResponse[TransactionResponse],
)
def get_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: TransactionStatus | None = Query(
        default=None,
    ),
    payment_method: PaymentMethod | None = Query(
        default=None,
    ),
    sender_id: int | None = Query(
        default=None,
        ge=1,
    ),
    receiver_id: int | None = Query(
        default=None,
        ge=1,
    ),
    min_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    db: Session = Depends(get_db),
):

    result = TransactionService.get_all_transactions(
        db,
        page,
        size,
        status,
        payment_method,
        sender_id,
        receiver_id,
        min_amount,
        max_amount,
    )

    return PaginatedResponse[TransactionResponse].create(
        page=result["page"],
        size=result["size"],
        total=result["total"],
        items=result["items"],
    )


@router.get(
    "",
    response_model=PaginatedResponse[TransactionResponse],
)
def get_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: TransactionStatus | None = Query(
        default=None,
    ),
    payment_method: PaymentMethod | None = Query(
        default=None,
    ),
    sender_id: int | None = Query(
        default=None,
        ge=1,
    ),
    receiver_id: int | None = Query(
        default=None,
        ge=1,
    ),
    min_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    sort_by: str = Query(
        default="created_at",
        pattern="^(id|amount|created_at|status|payment_method)$",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):

    result = TransactionService.get_all_transactions(
        db,
        page,
        size,
        status,
        payment_method,
        sender_id,
        receiver_id,
        min_amount,
        max_amount,
        sort_by,
        sort_order,
    )

    return PaginatedResponse[TransactionResponse].create(
        page=result["page"],
        size=result["size"],
        total=result["total"],
        items=result["items"],
    )


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