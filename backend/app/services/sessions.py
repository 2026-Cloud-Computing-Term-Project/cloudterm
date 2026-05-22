from uuid import UUID, uuid4

from app.core.settings import settings
from app.schemas.sessions import SessionCreateResponse, SessionDetailResponse, SessionRecord


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}

    def create_session(self, title: str | None) -> SessionCreateResponse:
        session = SessionRecord(
            session_id=uuid4(),
            title=title,
        )
        self._sessions[session.session_id] = session
        return SessionCreateResponse(
            session_id=session.session_id,
            title=session.title,
            share_url=f"{settings.frontend_base_url}/sessions/{session.session_id}",
            created_at=session.created_at,
        )

    def get_session(self, session_id: UUID) -> SessionDetailResponse:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError
        return SessionDetailResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
        )


session_service = SessionService()

