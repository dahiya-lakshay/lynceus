from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from decimal import Decimal

from app.models.transaction import (
    PaymentMethod,
    Transaction,
    TransactionStatus,
)

from app.models.user import User
from app.repositories.transaction_repository import (
    TransactionRepository,
)
from app.schemas.transaction import (
    CreateTransaction,
    UpdateTransaction,
)
from app.services.prediction_service import (
    PredictionService,
)


class TransactionService:

    @staticmethod
    def create_transaction(
        db: Session,
        current_user: User,
        data: CreateTransaction,
    ) -> Transaction:

        if data.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than zero",
            )

        if current_user.id == data.receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send money to yourself",
            )

        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive",
            )

        receiver = (
            db.query(User)
            .filter(User.id == data.receiver_id)
            .first()
        )

        if receiver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found",
            )

        if not receiver.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Receiver account is inactive",
            )

        transaction = Transaction(
            sender_id=current_user.id,
            receiver_id=data.receiver_id,
            amount=data.amount,
            payment_method=PaymentMethod(data.payment_method),

            origin_country=data.origin_country,
            destination_country=data.destination_country,
            merchant_category=data.merchant_category,
            device_type=data.device_type,
            device_id_hash=data.device_id_hash,
        )

        transaction = TransactionRepository.create(
            db,
            transaction,
        )

        # Automatically generate fraud prediction
        PredictionService.predict_transaction(
            db,
            transaction,
        )

        db.refresh(transaction)

        return transaction

    @staticmethod
    def get_all_transactions(
        db: Session,
        page: int,
        size: int,
        status: TransactionStatus | None = None,
        payment_method: PaymentMethod | None = None,
        sender_id: int | None = None,
        receiver_id: int | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):

        transactions = TransactionRepository.get_all(
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

        total = TransactionRepository.count(
            db,
            status,
            payment_method,
            sender_id,
            receiver_id,
            min_amount,
            max_amount,
        )

        return {
            "page": page,
            "size": size,
            "total": total,
            "items": transactions,
        }

    @staticmethod
    def get_transaction(
        db: Session,
        transaction_id: int,
    ):

        return TransactionRepository.get_by_id(
            db,
            transaction_id,
        )

    @staticmethod
    def update_transaction(
        db: Session,
        transaction_id: int,
        data: UpdateTransaction,
    ) -> Transaction:

        transaction = TransactionRepository.get_by_id(
            db,
            transaction_id,
        )

        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        if (
            data.amount is not None
            and data.amount <= 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than zero",
            )

        if data.amount is not None:
            transaction.amount = data.amount

        if data.payment_method is not None:
            transaction.payment_method = PaymentMethod(
                data.payment_method
            )

        if data.origin_country is not None:
            transaction.origin_country = data.origin_country

        if data.destination_country is not None:
            transaction.destination_country = data.destination_country

        if data.merchant_category is not None:
            transaction.merchant_category = data.merchant_category

        if data.device_type is not None:
            transaction.device_type = data.device_type

        if data.device_id_hash is not None:
            transaction.device_id_hash = data.device_id_hash

        return TransactionRepository.update(
            db,
            transaction,
        )

    @staticmethod
    def delete_transaction(
        db: Session,
        transaction_id: int,
    ):

        transaction = TransactionRepository.get_by_id(
            db,
            transaction_id,
        )

        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        TransactionRepository.delete(
            db,
            transaction,
        )