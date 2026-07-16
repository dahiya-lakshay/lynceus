from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository


class AdminService:

    @staticmethod
    def get_all_users(
        db: Session,
    ):
        return UserRepository.get_all(db)