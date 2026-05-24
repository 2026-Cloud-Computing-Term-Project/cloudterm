from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: str | None = Field(default=None)


class SessionCreateResponse(BaseModel):
    session_id: UUID
    title: str | None = Field(default=None)
    share_url: str
    created_at: datetime


class SessionDetailResponse(BaseModel):
    session_id: UUID
    title: str | None = Field(default=None)
    created_at: datetime
