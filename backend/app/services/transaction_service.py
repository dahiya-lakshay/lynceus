from sqlalchemy.orm import Session

from app.models.transaction import (
    PaymentMethod,
    Transaction,
)
from app.models.user import User
from app.repositories.transaction_repository import (
    TransactionRepository,
)
from app.schemas.transaction import CreateTransaction


class TransactionService:

    @staticmethod
    def create_transaction(
        db: Session,
        current_user: User,
        data: CreateTransaction,
    ) -> Transaction:

        transaction = Transaction(
            sender_id=current_user.id,
            receiver_id=data.receiver_id,
            amount=data.amount,
            payment_method=PaymentMethod(
                data.payment_method
            ),
        )

        return TransactionRepository.create(
            db,
            transaction,
        )

    @staticmethod
    def get_all_transactions(
        db: Session,
    ):

        return TransactionRepository.get_all(
            db,
        )

    @staticmethod
    def get_transaction(
        db: Session,
        transaction_id: int,
    ):

        return TransactionRepository.get_by_id(
            db,
            transaction_id,
        )