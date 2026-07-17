from uuid import UUID

from pydantic import BaseModel, EmailStr


class UpdateUser(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None


class UserProfile(BaseModel):
    id: int
    uuid: UUID
    full_name: str
    email: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True,
    }