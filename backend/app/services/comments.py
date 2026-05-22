from uuid import UUID

from app.repositories.comments import CommentRepository
from app.schemas.comments import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    CommentWithRepliesResponse,
    ReplyCreateRequest,
    ReplyResponse,
)


class CommentNotFoundError(Exception):
    pass


class CommentService:
    def __init__(self, repository: CommentRepository) -> None:
        self.repository = repository

    async def list_comments(self, session_id: UUID) -> CommentListResponse:
        comments = await self.repository.list_comments(session_id=session_id)
        return CommentListResponse(
            comments=[
                CommentWithRepliesResponse(
                    comment_id=comment.comment_id,
                    line_number=comment.line_number,
                    body=comment.body,
                    author_name=comment.author_name,
                    created_at=comment.created_at,
                    replies=[
                        ReplyResponse(
                            reply_id=reply.reply_id,
                            comment_id=reply.comment_id,
                            body=reply.body,
                            author_name=reply.author_name,
                            created_at=reply.created_at,
                        )
                        for reply in comment.replies
                    ],
                )
                for comment in comments
            ]
        )

    async def create_comment(self, session_id: UUID, payload: CommentCreateRequest) -> CommentResponse:
        comment = await self.repository.create_comment(
            session_id=session_id,
            line_number=payload.line_number,
            body=payload.body,
            author_name=payload.author_name,
        )
        return CommentResponse(
            comment_id=comment.comment_id,
            line_number=comment.line_number,
            body=comment.body,
            author_name=comment.author_name,
            created_at=comment.created_at,
        )

    async def create_reply(self, session_id: UUID, comment_id: UUID, payload: ReplyCreateRequest) -> ReplyResponse:
        comment = await self.repository.get_comment_in_session(session_id=session_id, comment_id=comment_id)
        if comment is None:
            raise CommentNotFoundError

        reply = await self.repository.create_reply(
            comment_id=comment_id,
            body=payload.body,
            author_name=payload.author_name,
        )
        return ReplyResponse(
            reply_id=reply.reply_id,
            comment_id=reply.comment_id,
            body=reply.body,
            author_name=reply.author_name,
            created_at=reply.created_at,
        )
