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

        transaction = Transaction(
            sender_id=current_user.id,
            receiver_id=data.receiver_id,
            amount=data.amount,
            payment_method=PaymentMethod(
                data.payment_method
            ),
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