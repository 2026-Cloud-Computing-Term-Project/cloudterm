from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
)
from app.services.sessions import SessionNotFoundError, session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreateRequest) -> SessionCreateResponse:
    return session_service.create_session(title=payload.title)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: UUID) -> SessionDetailResponse:
    try:
        return session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc

