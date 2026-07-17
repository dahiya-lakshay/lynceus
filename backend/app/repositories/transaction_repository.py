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
    ) -> list[Transaction]:

        return (
            db.query(Transaction)
            .all()
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