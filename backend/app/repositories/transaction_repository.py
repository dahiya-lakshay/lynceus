from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:

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
    ) -> list[Transaction]:

        offset = (page - 1) * size

        return (
            db.query(Transaction)
            .offset(offset)
            .limit(size)
            .all()
        )

    @staticmethod
    def count(
        db: Session,
    ) -> int:

        return (
            db.query(Transaction)
            .count()
        )

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