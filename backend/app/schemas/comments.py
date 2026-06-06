from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReplyCreateRequest(BaseModel):
    body: str = Field(min_length=1)
    author_name: str = Field(min_length=1)


class ReplyResponse(BaseModel):
    reply_id: UUID
    comment_id: UUID
    body: str
    author_name: str
    created_at: datetime


class CommentCreateRequest(BaseModel):
    line_number: int = Field(ge=1)
    body: str = Field(min_length=1)
    author_name: str = Field(min_length=1)


class CommentResponse(BaseModel):
    comment_id: UUID
    line_number: int
    body: str
    author_name: str
    created_at: datetime


class CommentWithRepliesResponse(BaseModel):
    comment_id: UUID
    line_number: int
    body: str
    author_name: str
    created_at: datetime
    replies: list[ReplyResponse]


class CommentListResponse(BaseModel):
    comments: list[CommentWithRepliesResponse]
