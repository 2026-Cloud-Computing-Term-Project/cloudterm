from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import CommentModel, ReplyModel


class CommentRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def list_comments(self, session_id: UUID) -> list[CommentModel]:
        stmt = (
            select(CommentModel)
            .where(CommentModel.session_id == session_id)
            .options(selectinload(CommentModel.replies))
            .order_by(CommentModel.created_at.asc())
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def create_comment(
        self,
        session_id: UUID,
        line_number: int,
        body: str,
        author_name: str,
    ) -> CommentModel:
        comment = CommentModel(
            session_id=session_id,
            line_number=line_number,
            body=body,
            author_name=author_name,
        )
        self.db_session.add(comment)
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def get_comment(self, comment_id: UUID) -> CommentModel | None:
        stmt = select(CommentModel).where(CommentModel.comment_id == comment_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comment_in_session(self, session_id: UUID, comment_id: UUID) -> CommentModel | None:
        stmt = select(CommentModel).where(
            CommentModel.session_id == session_id,
            CommentModel.comment_id == comment_id,
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_reply(
        self,
        comment_id: UUID,
        body: str,
        author_name: str,
    ) -> ReplyModel:
        reply = ReplyModel(
            comment_id=comment_id,
            body=body,
            author_name=author_name,
        )
        self.db_session.add(reply)
        await self.db_session.commit()
        await self.db_session.refresh(reply)
        return reply
