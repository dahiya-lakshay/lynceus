from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UpdateUser


class UserService:

    @staticmethod
    def get_current_user(
        user: User,
    ) -> User:
        return user

    @staticmethod
    def update_profile(
        db: Session,
        current_user: User,
        data: UpdateUser,
    ) -> User:

        if (
            data.email is not None
            and data.email != current_user.email
        ):
            existing_user = (
                db.query(User)
                .filter(User.email == data.email)
                .first()
            )

            if existing_user is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

            current_user.email = data.email

        if data.full_name is not None:
            current_user.full_name = data.full_name

        db.commit()
        db.refresh(current_user)

        return current_user