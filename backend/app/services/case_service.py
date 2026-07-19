from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.user import UserRole
from app.repositories.case_repository import CaseRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.case import (
    CreateCase,
    UpdateCase,
)

from app.models.case import (
    Case,
    CasePriority,
)


class CaseService:

    @staticmethod
    def create_case(
        db: Session,
        data: CreateCase,
    ) -> Case:

        transaction = TransactionRepository.get_by_id(
            db,
            data.transaction_id,
        )

        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        existing_case = (
            CaseRepository.get_by_transaction_id(
                db,
                data.transaction_id,
            )
        )

        if existing_case is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case already exists for this transaction",
            )

        if data.assigned_to is not None:

            analyst = UserRepository.get_by_id(
                db,
                data.assigned_to,
            )

            if analyst is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned user not found",
                )

            if analyst.role not in (
                UserRole.ADMIN,
                UserRole.ANALYST,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be assigned to a case",
                )

        case = Case(
            transaction_id=data.transaction_id,
            assigned_to=data.assigned_to,
            priority=data.priority,
            notes=data.notes,
        )

        return CaseRepository.create(
            db,
            case,
        )

    @staticmethod
    def get_cases(
        db: Session,
    ):

        return CaseRepository.get_all(db)

    @staticmethod
    def get_case(
        db: Session,
        case_id: int,
    ):

        case = CaseRepository.get_by_id(
            db,
            case_id,
        )

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        return case

    @staticmethod
    def update_case(
        db: Session,
        case_id: int,
        data: UpdateCase,
    ):

        case = CaseRepository.get_by_id(
            db,
            case_id,
        )

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        if data.assigned_to is not None:

            analyst = UserRepository.get_by_id(
                db,
                data.assigned_to,
            )

            if analyst is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned user not found",
                )

            if analyst.role not in (
                UserRole.ADMIN,
                UserRole.ANALYST,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be assigned to a case",
                )

            case.assigned_to = data.assigned_to

        if data.status is not None:
            case.status = data.status

        if data.priority is not None:
            case.priority = data.priority

        if data.notes is not None:
            case.notes = data.notes

        return CaseRepository.update(
            db,
            case,
        )

    @staticmethod
    def delete_case(
        db: Session,
        case_id: int,
    ):

        case = CaseRepository.get_by_id(
            db,
            case_id,
        )

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        CaseRepository.delete(
            db,
            case,
        )

    @staticmethod
    def create_case_for_transaction(
        db: Session,
        transaction_id: int,
    ) -> Case:

        existing_case = (
            CaseRepository.get_by_transaction_id(
                db,
                transaction_id,
            )
        )

        if existing_case is not None:
            return existing_case

        case = Case(
            transaction_id=transaction_id,
            priority=CasePriority.HIGH,
        )

        return CaseRepository.create(
            db,
            case,
        )