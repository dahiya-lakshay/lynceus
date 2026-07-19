from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.case import (
    CasePriority,
    CaseStatus,
)


class CreateCase(BaseModel):
    transaction_id: int
    assigned_to: int | None = None
    priority: CasePriority = CasePriority.MEDIUM
    notes: str | None = None


class UpdateCase(BaseModel):
    assigned_to: int | None = None
    status: CaseStatus | None = None
    priority: CasePriority | None = None
    notes: str | None = None


class CaseResponse(BaseModel):
    id: int
    case_uuid: UUID
    transaction_id: int
    assigned_to: int | None
    status: CaseStatus
    priority: CasePriority
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }