from decimal import Decimal

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