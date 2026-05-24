from uuid import UUID

from app.core.settings import settings
from app.repositories.sessions import SessionRepository
from app.schemas.sessions import SessionCreateResponse, SessionDetailResponse


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    async def create_session(self, title: str | None) -> SessionCreateResponse:
        session = await self.repository.create_session(title=title)
        return SessionCreateResponse(
            session_id=session.session_id,
            title=session.title,
            share_url=f"{settings.frontend_base_url}/sessions/{session.session_id}",
            created_at=session.created_at,
        )

    async def get_session(self, session_id: UUID) -> SessionDetailResponse:
        session = await self.repository.get_session(session_id=session_id)
        if session is None:
            raise SessionNotFoundError
        return SessionDetailResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
        )
