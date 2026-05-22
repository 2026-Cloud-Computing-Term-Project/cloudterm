from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionModel


class SessionRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create_session(self, title: str | None) -> SessionModel:
        session = SessionModel(title=title)
        self.db_session.add(session)
        await self.db_session.commit()
        await self.db_session.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> SessionModel | None:
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

