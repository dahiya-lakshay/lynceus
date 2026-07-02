from app.models.user import User


class UserService:

    @staticmethod
    def get_current_user(
        user: User,
    ) -> User:
        return user