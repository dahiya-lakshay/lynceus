from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.models.transaction import (
    PaymentMethod,
    Transaction,
    TransactionStatus,
)


class TransactionRepository:

    @staticmethod
    def _build_filtered_query(
        db: Session,
        status: TransactionStatus | None = None,
        payment_method: PaymentMethod | None = None,
        sender_id: int | None = None,
        receiver_id: int | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
    ) -> Query:

        query = db.query(Transaction)

        if status is not None:
            query = query.filter(
                Transaction.status == status
            )

        if payment_method is not None:
            query = query.filter(
                Transaction.payment_method == payment_method
            )

        if sender_id is not None:
            query = query.filter(
                Transaction.sender_id == sender_id
            )

        if receiver_id is not None:
            query = query.filter(
                Transaction.receiver_id == receiver_id
            )

        if min_amount is not None:
            query = query.filter(
                Transaction.amount >= min_amount
            )

        if max_amount is not None:
            query = query.filter(
                Transaction.amount <= max_amount
            )

        return query

    @staticmethod
    def create(
        db: Session,
        transaction: Transaction,
    ) -> Transaction:

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        size: int = 20,
        status: TransactionStatus | None = None,
        payment_method: PaymentMethod | None = None,
        sender_id: int | None = None,
        receiver_id: int | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Transaction]:

        query = TransactionRepository._build_filtered_query(
            db,
            status,
            payment_method,
            sender_id,
            receiver_id,
            min_amount,
            max_amount,
        )

        allowed_sort_fields = {
            "id": Transaction.id,
            "amount": Transaction.amount,
            "created_at": Transaction.created_at,
            "status": Transaction.status,
            "payment_method": Transaction.payment_method,
        }

        sort_column = allowed_sort_fields.get(
            sort_by,
            Transaction.created_at,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size

        return (
            query
            .offset(offset)
            .limit(size)
            .all()
        )

    @staticmethod
    def count(
        db: Session,
        status: TransactionStatus | None = None,
        payment_method: PaymentMethod | None = None,
        sender_id: int | None = None,
        receiver_id: int | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
    ) -> int:

        query = TransactionRepository._build_filtered_query(
            db,
            status,
            payment_method,
            sender_id,
            receiver_id,
            min_amount,
            max_amount,
        )

        return query.count()

    @staticmethod
    def get_by_id(
        db: Session,
        transaction_id: int,
    ) -> Transaction | None:

        return (
            db.query(Transaction)
            .filter(Transaction.id == transaction_id)
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        transaction: Transaction,
    ) -> Transaction:

        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def delete(
        db: Session,
        transaction: Transaction,
    ) -> None:

        db.delete(transaction)
        db.commit()

    # ==========================================================
    # Existing Aggregate Methods
    # ==========================================================

    @staticmethod
    def count_by_sender(
        db: Session,
        sender_id: int,
    ) -> int:

        return (
            db.query(func.count(Transaction.id))
            .filter(Transaction.sender_id == sender_id)
            .scalar()
            or 0
        )

    @staticmethod
    def count_by_receiver(
        db: Session,
        receiver_id: int,
    ) -> int:

        return (
            db.query(func.count(Transaction.id))
            .filter(Transaction.receiver_id == receiver_id)
            .scalar()
            or 0
        )

    @staticmethod
    def total_sent_by_sender(
        db: Session,
        sender_id: int,
    ) -> Decimal:

        return (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.sender_id == sender_id)
            .scalar()
            or Decimal("0")
        )

    @staticmethod
    def total_received_by_receiver(
        db: Session,
        receiver_id: int,
    ) -> Decimal:

        return (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.receiver_id == receiver_id)
            .scalar()
            or Decimal("0")
        )

    # ==========================================================
    # Feature Engineering Queries
    # ==========================================================

    @staticmethod
    def count_sender_transactions_last_24h(
        db: Session,
        sender_id: int,
    ) -> int:

        since = datetime.utcnow() - timedelta(hours=24)

        return (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.sender_id == sender_id,
                Transaction.created_at >= since,
            )
            .scalar()
            or 0
        )

    @staticmethod
    def count_receiver_transactions_last_24h(
        db: Session,
        receiver_id: int,
    ) -> int:

        since = datetime.utcnow() - timedelta(hours=24)

        return (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.receiver_id == receiver_id,
                Transaction.created_at >= since,
            )
            .scalar()
            or 0
        )

    @staticmethod
    def average_sender_amount_last_30d(
        db: Session,
        sender_id: int,
    ) -> Decimal:

        since = datetime.utcnow() - timedelta(days=30)

        return (
            db.query(func.avg(Transaction.amount))
            .filter(
                Transaction.sender_id == sender_id,
                Transaction.created_at >= since,
            )
            .scalar()
            or Decimal("0")
        )

    @staticmethod
    def average_receiver_amount_last_30d(
        db: Session,
        receiver_id: int,
    ) -> Decimal:

        since = datetime.utcnow() - timedelta(days=30)

        return (
            db.query(func.avg(Transaction.amount))
            .filter(
                Transaction.receiver_id == receiver_id,
                Transaction.created_at >= since,
            )
            .scalar()
            or Decimal("0")
        )

    @staticmethod
    def has_previous_transaction(
        db: Session,
        sender_id: int,
        receiver_id: int,
    ) -> bool:

        return (
            db.query(Transaction)
            .filter(
                Transaction.sender_id == sender_id,
                Transaction.receiver_id == receiver_id,
            )
            .first()
            is not None
        )

    @staticmethod
    def has_seen_device(
        db: Session,
        sender_id: int,
        device_id_hash: str,
    ) -> bool:

        return (
            db.query(Transaction)
            .filter(
                Transaction.sender_id == sender_id,
                Transaction.device_id_hash == device_id_hash,
            )
            .first()
            is not None
        )