from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import (
    UpdateUser,
    UserProfile,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserProfile,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserService.get_current_user(
        current_user,
    )


@router.patch(
    "/me",
    response_model=UserProfile,
)
def update_me(
    user: UpdateUser,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return UserService.update_profile(
        db,
        current_user,
        user,
    )