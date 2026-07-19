from sqlalchemy.orm import Session

from app.models.case import Case


class CaseRepository:

    @staticmethod
    def create(
        db: Session,
        case: Case,
    ) -> Case:

        db.add(case)
        db.commit()
        db.refresh(case)

        return case

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Case]:

        return (
            db.query(Case)
            .order_by(Case.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        case_id: int,
    ) -> Case | None:

        return (
            db.query(Case)
            .filter(Case.id == case_id)
            .first()
        )

    @staticmethod
    def get_by_transaction_id(
        db: Session,
        transaction_id: int,
    ) -> Case | None:

        return (
            db.query(Case)
            .filter(
                Case.transaction_id == transaction_id
            )
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        case: Case,
    ) -> Case:

        db.commit()
        db.refresh(case)

        return case

    @staticmethod
    def delete(
        db: Session,
        case: Case,
    ) -> None:

        db.delete(case)
        db.commit()