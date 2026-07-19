from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.investigation import (
    InvestigationResponse,
    InvestigationStatistics,
    RiskSummary,
)


class InvestigationService:

    @staticmethod
    def investigate_transaction(
        db: Session,
        transaction_id: int,
    ) -> InvestigationResponse:

        transaction = TransactionRepository.get_by_id(
            db,
            transaction_id,
        )

        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        prediction = PredictionRepository.get_by_transaction_id(
            db,
            transaction.id,
        )

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found",
            )

        sender = UserRepository.get_by_id(
            db,
            transaction.sender_id,
        )

        receiver = UserRepository.get_by_id(
            db,
            transaction.receiver_id,
        )

        if sender is None or receiver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        statistics = InvestigationStatistics(
            sender_transaction_count=TransactionRepository.count_by_sender(
                db,
                sender.id,
            ),
            receiver_transaction_count=TransactionRepository.count_by_receiver(
                db,
                receiver.id,
            ),
            sender_total_sent=TransactionRepository.total_sent_by_sender(
                db,
                sender.id,
            ),
            receiver_total_received=TransactionRepository.total_received_by_receiver(
                db,
                receiver.id,
            ),
        )

        risk = RiskSummary(
            prediction=transaction.prediction,
            prediction_label=prediction.prediction_label.value,
            risk_score=prediction.risk_score,
            fraud_probability=prediction.fraud_probability,
        )

        return InvestigationResponse(
            transaction=transaction,
            prediction=prediction,
            sender=sender,
            receiver=receiver,
            statistics=statistics,
            risk=risk,
            generated_at=datetime.utcnow(),
        )