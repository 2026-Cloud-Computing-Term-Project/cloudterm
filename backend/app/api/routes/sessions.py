from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.sessions import SessionRepository
from app.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
)
from app.services.sessions import SessionNotFoundError, SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db_session: AsyncSession = Depends(get_db_session)) -> SessionService:
    repository = SessionRepository(db_session=db_session)
    return SessionService(repository=repository)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    session_service: SessionService = Depends(get_session_service),
) -> SessionCreateResponse:
    return await session_service.create_session(title=payload.title)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
) -> SessionDetailResponse:
    try:
        return await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc
