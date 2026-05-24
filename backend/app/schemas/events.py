from uuid import UUID

from pydantic import BaseModel


class SessionRunCompletedEvent(BaseModel):
    type: str = "session.run.completed"
    session_id: UUID
    run_id: UUID


class CommentCreatedEvent(BaseModel):
    type: str = "comment.created"
    session_id: UUID
    comment_id: UUID


class ReplyCreatedEvent(BaseModel):
    type: str = "reply.created"
    session_id: UUID
    comment_id: UUID
    reply_id: UUID

