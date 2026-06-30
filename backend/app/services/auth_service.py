from sqlalchemy.orm import Session

from app.auth.hashing import (
    hash_password,
    verify_password,
)
from app.auth.jwt_handler import create_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister


class AuthService:

    @staticmethod
    def register(
        db: Session,
        user_data: UserRegister,
    ) -> User:

        existing_user = UserRepository.get_by_email(
            db,
            user_data.email,
        )

        if existing_user:
            raise ValueError("Email already registered")

        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=hash_password(
                user_data.password
            ),
        )

        return UserRepository.create(
            db,
            user,
        )

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ) -> str:

        user = UserRepository.get_by_email(
            db,
            email,
        )

        if not user:
            raise ValueError("Invalid credentials")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials")

        token = create_access_token(
            {
                "sub": user.email,
            }
        )

        return token