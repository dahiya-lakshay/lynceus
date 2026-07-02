from uuid import UUID

from pydantic import BaseModel


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